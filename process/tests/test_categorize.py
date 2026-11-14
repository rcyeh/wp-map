"""Tests for categorize function in create_class_mapping.py."""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from create_class_mapping import categorize


class TestCategorizeLabelRules:
  """Category classification based on English labels."""

  def test_natural_river(self):
    """River label -> natural."""
    assert categorize(100, 'River', []) == 'natural'
    assert categorize(100, 'River Valley', []) == 'natural'

  def test_natural_mountain(self):
    """Mountain label -> natural."""
    assert categorize(100, 'Mountain', []) == 'natural'
    assert categorize(100, 'Peak', []) == 'natural'
    assert categorize(100, 'Volcano', []) == 'natural'

  def test_natural_island(self):
    """Island label -> natural."""
    assert categorize(100, 'Island', []) == 'natural'

  def test_natural_desert(self):
    """Desert label -> natural."""
    assert categorize(100, 'Desert', []) == 'natural'

  def test_natural_forest(self):
    """Forest label -> natural."""
    assert categorize(100, 'Forest', []) == 'natural'

  def test_natural_lake(self):
    """Lake label -> natural."""
    assert categorize(100, 'Lake', []) == 'natural'

  def test_natural_cave(self):
    """Cave label -> natural."""
    assert categorize(100, 'Cave', []) == 'natural'

  def test_transport_station(self):
    """Station label -> transportation."""
    assert categorize(100, 'Station', []) == 'transportation'

  def test_transport_airport(self):
    """Airport label -> transportation."""
    assert categorize(100, 'Airport', []) == 'transportation'

  def test_transport_highway(self):
    """Highway label -> transportation."""
    assert categorize(100, 'Highway', []) == 'transportation'

  def test_transport_bridge(self):
    """Bridge label -> transportation."""
    assert categorize(100, 'Bridge', []) == 'transportation'

  def test_transport_tunnel(self):
    """Tunnel label -> transportation."""
    assert categorize(100, 'Tunnel', []) == 'transportation'

  def test_transport_dam(self):
    """Dam label -> transportation."""
    assert categorize(100, 'Dam', []) == 'transportation'

  def test_admin_country(self):
    """Country label -> administrative."""
    assert categorize(100, 'Country', []) == 'administrative'

  def test_admin_city(self):
    """City label -> administrative."""
    assert categorize(100, 'City', []) == 'administrative'

  def test_admin_county(self):
    """County label -> administrative."""
    assert categorize(100, 'County', []) == 'administrative'

  def test_admin_state(self):
    """State label -> administrative."""
    assert categorize(100, 'State', []) == 'administrative'

  def test_admin_province(self):
    """Province label -> administrative."""
    assert categorize(100, 'Province', []) == 'administrative'

  def test_admin_village(self):
    """Village label -> administrative."""
    assert categorize(100, 'Village', []) == 'administrative'

  def test_admin_parish(self):
    """Parish label -> administrative."""
    assert categorize(100, 'Parish', []) == 'administrative'

  def test_building_church(self):
    """Church label -> building."""
    assert categorize(100, 'Church', []) == 'building'

  def test_building_cathedral(self):
    """Cathedral label -> building."""
    assert categorize(100, 'Cathedral', []) == 'building'

  def test_building_castle(self):
    """Castle label -> building."""
    assert categorize(100, 'Castle', []) == 'building'

  def test_building_museum(self):
    """Museum label -> building."""
    assert categorize(100, 'Museum', []) == 'building'

  def test_building_hospital(self):
    """Hospital label -> building."""
    assert categorize(100, 'Hospital', []) == 'building'

  def test_building_school(self):
    """School label -> building."""
    assert categorize(100, 'School', []) == 'building'

  def test_building_library(self):
    """Library label -> building."""
    assert categorize(100, 'Library', []) == 'building'

  def test_cultural_historic_site(self):
    """Historic site -> cultural."""
    assert categorize(100, 'Historic District', []) == 'cultural'

  def test_cultural_monument(self):
    """Monument -> cultural."""
    assert categorize(100, 'Monument', []) == 'cultural'

  def test_cultural_gallery(self):
    """Gallery -> cultural."""
    assert categorize(100, 'Gallery', []) == 'cultural'

  def test_event_battle(self):
    """Battle -> event."""
    assert categorize(100, 'Battle', []) == 'event'

  def test_event_war(self):
    """War -> event."""
    assert categorize(100, 'War', []) == 'event'

  def test_event_disaster(self):
    """Disaster -> event."""
    assert categorize(100, 'Disaster', []) == 'event'

  def test_event_flood(self):
    """Flood -> event."""
    assert categorize(100, 'Flood', []) == 'event'

  def test_event_festival(self):
    """Festival -> event."""
    assert categorize(100, 'Festival', []) == 'event'

  def test_unknown_default(self):
    """Unknown label falls back to 'unknown'."""
    assert categorize(100, 'Random Category', []) == 'unknown'


class TestCategorizeTitleFallback:
  """Title-based heuristic fallback when labels are empty."""

  def test_title_natural(self):
    """Titles suggesting natural features."""
    result = categorize(100, '', ['Mount Everest'])
    assert result == 'natural'

    result = categorize(100, '', ['River Thames'])
    assert result == 'natural'

    result = categorize(100, '', ['Lake Victoria'])
    assert result == 'natural'

  def test_title_transport(self):
    """Titles suggesting transportation."""
    result = categorize(100, '', ['Central Station'])
    assert result == 'transportation'

    result = categorize(100, '', ['Golden Gate Bridge'])
    assert result == 'transportation'

  def test_title_admin(self):
    """Titles suggesting administrative divisions."""
    result = categorize(100, '', ['New York City'])
    assert result == 'administrative'

    result = categorize(100, '', ['Los Angeles County'])
    assert result == 'administrative'

  def test_title_event(self):
    """Titles suggesting events."""
    result = categorize(100, '', ['Battle of Waterloo'])
    assert result == 'event'

    result = categorize(100, '', ['Earthquake 2010'])
    assert result == 'event'

  def test_label_takes_precedence_over_title(self):
    """Non-matching label wins over title keywords."""
    # "Building" label with "Mountain" title -> building wins
    result = categorize(100, 'Building', ['Mountain'])
    assert result == 'building'

  def test_no_match_anything(self):
    """Empty label and titles -> unknown."""
    result = categorize(100, '', [])
    assert result == 'unknown'

  def test_unknown_label_with_natural_title(self):
    """Unknown label with natural title -> natural."""
    result = categorize(100, 'Unknown Thing', ['River Valley'])
    assert result == 'natural'


class TestCategorizeEdgeCases:
  """Edge cases and boundary conditions."""

  def test_empty_label(self):
    """Empty string label."""
    assert categorize(100, '', []) == 'unknown'

  def test_none_label(self):
    """None label treated as empty."""
    assert categorize(100, None, []) == 'unknown'

  def test_empty_titles(self):
    """Empty titles list."""
    assert categorize(100, 'Mountain', []) == 'natural'

  def test_empty_list_titles(self):
    """Empty list titles."""
    assert categorize(100, 'Mountain', []) == 'natural'

  def test_case_insensitive(self):
    """Labels are case-insensitive."""
    assert categorize(100, 'MOUNTAIN', []) == 'natural'
    assert categorize(100, 'mountain', []) == 'natural'
    assert categorize(100, 'MountaIn', []) == 'natural'

  def test_multiline_label(self):
    """Multi-word labels work."""
    assert categorize(100, 'National Park', []) == 'natural'
    assert categorize(100, 'City Hall', []) == 'building'

  def test_special_characters(self):
    """Special characters in label."""
    assert categorize(100, "St. Mary's Church", []) == 'building'
    assert categorize(100, 'Île-de-France', []) == 'administrative'
