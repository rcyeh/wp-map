"""Tests for wpmaps_pb2 module."""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import wpmaps_pb2


class TestTileSet:
  """TileSet message fields."""

  def test_create_tile(self):
    """Tile message is created."""
    tile = wpmaps_pb2.TileSet()
    assert tile is not None

  def test_tile_default_deletas(self):
    """Default tile has empty deletas."""
    tile = wpmaps_pb2.TileSet()
    assert tile.deletas == []

  def test_tile_set_deletas(self):
    """Can set deletas."""
    tile = wpmaps_pb2.TileSet()
    tile.deletas = [1, 2, 3]
    assert tile.deletas == [1, 2, 3]


class TestTileSetList:
  """TileSetList message."""

  def test_create_list(self):
    """TileSetList is created."""
    tsl = wpmaps_pb2.TileSetList()
    assert tsl is not None

  def test_list_tilesets_empty(self):
    """Empty list has no tilesets."""
    tsl = wpmaps_pb2.TileSetList()
    assert len(tsl.tilesets) == 0

  def test_list_add_tile(self):
    """Can add tiles to list."""
    tsl = wpmaps_pb2.TileSetList()
    tile = wpmaps_pb2.TileSet()
    tile.deletas = [1, 2]
    tsl.tilesets.add(deletas=[1, 2])
    assert len(tsl.tilesets) == 1

  def test_list_extend(self):
    """Can extend tileset list."""
    tsl = wpmaps_pb2.TileSetList()
    tsl.tilesets.add()
    tsl.tilesets.add()
    assert len(tsl.tilesets) == 2


class TestWikiGeoData:
  """WikiGeoData message."""

  def test_create(self):
    """WikiGeoData is created."""
    wg = wpmaps_pb2.WikiGeoData()
    assert wg is not None

  def test_fields(self):
    """All fields exist and have defaults."""
    wg = wpmaps_pb2.WikiGeoData()
    assert wg.q_id == 0
    assert wg.name == ''
    assert wg.longitude == 0
    assert wg.latitude == 0
    assert wg.logrank == 0

  def test_set_fields(self):
    """Fields can be set and retrieved."""
    wg = wpmaps_pb2.WikiGeoData()
    wg.q_id = 123
    wg.name = 'Test'
    wg.longitude = -73990000
    wg.latitude = 40700000
    wg.logrank = 100
    assert wg.q_id == 123
    assert wg.name == 'Test'
    assert wg.longitude == -73990000
    assert wg.latitude == 40700000
    assert wg.logrank == 100

  def test_serialize(self):
    """Proto can be serialized."""
    wg = wpmaps_pb2.WikiGeoData()
    wg.q_id = 1
    data = wg.SerializeToString()
    assert isinstance(data, bytes)
    assert len(data) > 0

  def test_roundtrip(self):
    """Serialize -> deserialize round-trips."""
    wg = wpmaps_pb2.WikiGeoData()
    wg.q_id = 42
    wg.name = 'RoundTrip'
    wg.longitude = 1000
    wg.latitude = 2000
    wg.logrank = 50
    data = wg.SerializeToString()
    wg2 = wpmaps_pb2.WikiGeoData()
    wg2.ParseFromString(data)
    assert wg2.q_id == 42
    assert wg2.name == 'RoundTrip'
    assert wg2.longitude == 1000
    assert wg2.latitude == 2000
    assert wg2.logrank == 50


class TestWikiGeoDataList:
  """WikiGeoDataList message."""

  def test_create(self):
    """WikiGeoDataList is created."""
    wgdl = wpmaps_pb2.WikiGeoDataList()
    assert wgdl is not None

  def test_empty_items(self):
    """Empty list has no items."""
    wgdl = wpmaps_pb2.WikiGeoDataList()
    assert len(wgdl.items) == 0

  def test_add_item(self):
    """Can add WikiGeoData items."""
    wgdl = wpmaps_pb2.WikiGeoDataList()
    wg = wpmaps_pb2.WikiGeoData()
    wg.q_id = 1
    wgdl.items.add(q_id=1)
    assert len(wgdl.items) == 1

  def test_extend_items(self):
    """Can extend items."""
    wgdl = wpmaps_pb2.WikiGeoDataList()
    wgdl.items.add(q_id=1)
    wgdl.items.add(q_id=2)
    assert len(wgdl.items) == 2

  def test_list_serialize(self):
    """List can be serialized."""
    wgdl = wpmaps_pb2.WikiGeoDataList()
    wgdl.items.add(q_id=1)
    wgdl.items.add(q_id=2)
    data = wgdl.SerializeToString()
    assert isinstance(data, bytes)
    assert len(data) > 0

  def test_list_roundtrip(self):
    """List round-trips correctly."""
    wgdl = wpmaps_pb2.WikiGeoDataList()
    wgdl.items.add(q_id=100, name='A')
    wgdl.items.add(q_id=200, name='B')
    data = wgdl.SerializeToString()
    wgdl2 = wpmaps_pb2.WikiGeoDataList()
    wgdl2.ParseFromString(data)
    assert len(wgdl2.items) == 2
    assert wgdl2.items[0].q_id == 100
    assert wgdl2.items[0].name == 'A'
    assert wgdl2.items[1].q_id == 200
    assert wgdl2.items[1].name == 'B'


class TestModuleLevel:
  """Module-level attributes."""

  def test_descriptor_exists(self):
    """DESCRIPTOR is defined."""
    assert hasattr(wpmaps_pb2, 'DESCRIPTOR')
    assert wpmaps_pb2.DESSCRIPTOR is not None
