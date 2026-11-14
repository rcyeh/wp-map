"""Tests for wpmap proto creation in write.py."""

import sys
import os
import gzip
import json

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import write
import wpmaps_pb2

LATLON = write.LATLON
MAXLAT = write.MAXLAT
LOGRANKFACTOR = write.LOGRANKFACTOR


class TestWpmap:
  """wpmap constructs WikiGeoData protos from POI dicts."""

  def test_basic_fields(self):
    """q_id, name, longitude, latitude are set correctly."""
    poi = {'q': 'Q123', 't': 'Test City', 'x': -73.99, 'y': 40.7, 'k': 100}
    proto = write.wpmap(poi)
    assert proto.q_id == 123
    assert proto.name == 'Test City'
    assert proto.longitude == round(-73.99 * LATLON)
    assert proto.latitude == round(40.7 * LATLON)

  def test_lat_clamping(self):
    """Latitude is clamped to MAXLAT."""
    poi = {'q': 'Q1', 't': 'North', 'x': 0, 'y': 90.5, 'k': 1}
    proto = write.wpmap(poi)
    assert proto.latitude == round(MAXLAT * LATLON)

    poi = {'q': 'Q2', 't': 'South', 'x': 0, 'y': -90.5, 'k': 1}
    proto = write.wpmap(poi)
    assert proto.latitude == round(-MAXLAT * LATLON)

  def test_logrank_from_k(self):
    """logrank is log-based on k value."""
    poi = {'q': 'Q1', 't': 'X', 'x': 0, 'y': 0, 'k': 10}
    proto = write.wpmap(poi)
    import math

    expected = round(LOGRANKFACTOR * math.log(max(10, 1)))
    assert proto.logrank == expected

  def test_logrank_missing_k(self):
    """Missing k defaults to 1."""
    poi = {'q': 'Q1', 't': 'X', 'x': 0, 'y': 0}
    proto = write.wpmap(poi)
    import math

    expected = round(LOGRANKFACTOR * math.log(max(1, 1)))
    assert proto.logrank == expected

  def test_q_id_strips_q_prefix(self):
    """Q prefix is stripped from q_id."""
    poi = {'q': 'Q99999', 't': 'X', 'x': 0, 'y': 0, 'k': 1}
    proto = write.wpmap(poi)
    assert proto.q_id == 99999

  def test_q_id_is_int(self):
    """q_id is always an int."""
    poi = {'q': 'Q0', 't': 'X', 'x': 0, 'y': 0, 'k': 1}
    proto = write.wpmap(poi)
    assert isinstance(proto.q_id, int)
    assert proto.q_id == 0

  def test_proto_type(self):
    """Returns a WikiGeoData proto instance."""
    poi = {'q': 'Q1', 't': 'X', 'x': 0, 'y': 0, 'k': 1}
    proto = write.wpmap(poi)
    assert isinstance(proto, wpmaps_pb2.WikiGeoData)


class TestLoopOverZoom:
  """loop_over_zoom computes tiles per zoom level."""

  def test_single_point_one_tile(self):
    """A single POI produces exactly one tile."""
    allpoints = [{'q': 'Q1', 't': 'X', 'x': -73.99, 'y': 40.7, 'k': 1}]
    result = write.loop_over_zoom(allpoints)
    # Should produce entries for all zoom levels 0-15
    assert len(result) == 16  # 0..15 inclusive
    # Each zoom level should have exactly 1 tile entry
    for z in range(16):
      assert z in result
      # Each tile should have at least 1 point
      for tile_list in result[z]:
        assert isinstance(tile_list, list)

  def test_multiple_points_different_tiles(self):
    """Different POIs may produce different tiles."""
    allpoints = [
      {'q': 'Q1', 't': 'NYC', 'x': -73.99, 'y': 40.7, 'k': 1},
      {'q': 'Q2', 't': 'London', 'x': -0.1, 'y': 51.5, 'k': 1},
    ]
    result = write.loop_over_zoom(allpoints)
    assert len(result) == 16

  def test_zoom_range(self):
    """Zoom levels go from MAXZOOM down to 0."""
    import math

    allpoints = [{'q': 'Q1', 't': 'X', 'x': 0, 'y': 0, 'k': 1}]
    result = write.loop_over_zoom(allpoints)
    assert 15 in result  # MAXZOOM
    assert 0 in result


class TestWriteTiles:
  """write_some_tiles groups POIs into tiles."""

  def test_single_poi(self):
    """Single POI writes to exactly one tile."""
    poi = {'q': 'Q1', 't': 'X', 'x': -73.99, 'y': 40.7, 'k': 1, 'pbf': None}
    # Pre-build pbf for write_some_tiles
    poi['pbf'] = write.wpmap(poi)
    result = write.write_some_tiles([poi], 15)
    assert len(result) == 1

  def test_tile_min_poi_threshold(self):
    """Tiles with fewer than MINPOI are not written."""
    write.MINPOI = 5  # Set threshold above 1
    try:
      poi = {'q': 'Q1', 't': 'X', 'x': -73.99, 'y': 40.7, 'k': 1}
      poi['pbf'] = write.wpmap(poi)
      result = write.write_some_tiles([poi], 15)
      assert len(result) == 0  # Only 1 POI, threshold is 5
    finally:
      write.MINPOI = 20  # Restore
    poi['pbf'] = write.wpmap(poi)
    result = write.write_some_tiles([poi], 15)
    assert len(result) == 0  # Still below restored threshold
