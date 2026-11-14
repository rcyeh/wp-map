"""Shared pytest fixtures for wp-map process scripts."""

import gzip
import json
from pathlib import Path

import pytest

PROCESS_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture
def tmp_project(tmp_path):
  """Create a temporary directory that mirrors the project layout."""
  return tmp_path


@pytest.fixture
def class_mapping_file(tmp_project):
  """Write a small class_mapping.jsonl.gz with known entries."""
  data = [
    [4, 'death', 'administrative'],
    [5, 'human', 'unknown'],
    [19, 'cheating', 'natural'],
    [8, 'happiness', 'cultural'],
    [100, 'unknown_class', 'building'],
    [200, 'river_spot', 'transportation'],
  ]
  path = tmp_project / 'class_mapping.jsonl.gz'
  with gzip.open(path, 'wt', encoding='utf-8') as f:
    for item in data:
      f.write(json.dumps(item) + '\n')
  return path


@pytest.fixture
def q_subclass_file(tmp_project):
  """Write a small q_subclass.jsonl.gz with known subclass claims."""
  data = [
    {
      'type': 'item',
      'id': 'Q100',
      'labels': {'en': {'value': 'some building'}},
      'claims': {
        'P279': [
          {
            'mainsnak': {
              'datavalue': {'value': {'numeric-id': 47548}},
              'snaktype': 'value',
            }
          }
        ]
      },
    },
    {
      'type': 'item',
      'id': 'Q200',
      'labels': {'en': {'value': 'a river'}},
      'claims': {
        'P279': [
          {
            'mainsnak': {
              'datavalue': {'value': {'id': 'Q300'}},
              'snaktype': 'value',
            }
          }
        ],
        'P31': [
          {
            'mainsnak': {
              'datavalue': {'value': {'numeric-id': 2000}},
              'snaktype': 'value',
            }
          }
        ],
      },
    },
    {
      'type': 'item',
      'id': 'Q300',
      'labels': {'en': {'value': 'watercourse'}},
      'claims': {},
    },
    {
      'type': 'item',
      'id': 'Q999',
      'labels': {'en': {'value': 'no claims'}},
      'claims': {
        'P279': 'not-a-list'  # malformed claim
      },
    },
  ]
  path = tmp_project / 'q_subclass.jsonl.gz'
  with gzip.open(path, 'wt', encoding='utf-8') as f:
    for item in data:
      f.write(json.dumps(item) + '\n')
  return path


@pytest.fixture
def subclass_graph_file(tmp_project):
  """Write a small subclass_graph.jsonl.gz for ancestor traversal."""
  data = [
    {'id': 100, 'p279': [50], 'p31': []},
    {'id': 50, 'p279': [25], 'p31': []},
    {'id': 25, 'p279': [], 'p31': [10]},
    {'id': 10, 'p279': [], 'p31': []},
    {'id': 200, 'p279': [100, 250], 'p31': [300]},
    {'id': 250, 'p279': [50], 'p31': []},
    {'id': 300, 'p279': [], 'p31': []},
    {'id': 400, 'p279': [], 'p31': []},  # orphan, not referenced
  ]
  path = tmp_project / 'subclass_graph.jsonl.gz'
  with gzip.open(path, 'wb') as f:
    for item in data:
      f.write(json.dumps(item).encode('utf-8') + b'\n')
  return path


@pytest.fixture
def q_title_latlon_file(tmp_project):
  """Write a small q_title_latlon.jsonl.gz with POI data."""
  records = [
    {
      'q': 'Q1',
      't': 'Test City',
      'xy': [{'latitude': 40.7, 'longitude': -73.99}],
      'c': [100, 200],
    },
    {
      'q': 'Q2',
      't': 'Test Village',
      'xy': [{'latitude': 48.8, 'longitude': 2.35}],
      'c': [50],
    },
    {
      'q': 'Q3',
      't': 'Mount Test',
      'xy': [{'latitude': 46.5, 'longitude': 7.6}],
      'c': [75, 100],
    },
    {
      'q': 'Q4',
      't': 'River Test',
      'xy': [{'latitude': 51.5, 'longitude': -0.1}],
      'c': [200],
    },
    {
      'q': 'Q5',
      't': 'Airport Test',
      'xy': [{'latitude': 35.6, 'longitude': 139.7}],
      'c': [300],
    },
  ]
  path = tmp_project / 'q_title_latlon.jsonl.gz'
  with gzip.open(path, 'wt', encoding='utf-8') as f:
    for item in records:
      f.write(json.dumps(item) + '\n')
  return path


@pytest.fixture
def joined_file(tmp_project, q_title_latlon_file):
  """Write a joined.jsonl.gz combining POI data."""
  path = tmp_project / 'joined.jsonl.gz'
  with gzip.open(path, 'wt', encoding='utf-8') as f:
    for item in [
      {'q': 'Q1', 't': 'Test City', 'x': -73.99, 'y': 40.7, 'k': 100},
      {'q': 'Q2', 't': 'Test Village', 'x': 2.35, 'y': 48.8, 'k': 50},
      {'q': 'Q3', 't': 'Mount Test', 'x': 7.6, 'y': 46.5, 'k': 200},
    ]:
      f.write(json.dumps(item) + '\n')
  return path
