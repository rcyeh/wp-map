"""Tests for parse_poi_line in analyze_poi_taxonomy.py and generate_subclass_graphviz.py."""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from analyze_poi_taxonomy import parse_poi_line as parse_poi_line_analyze
from generate_subclass_graphviz import parse_poi_line as parse_poi_line_graphviz


class TestParsePoiLineAnalyze:
  """parse_poi_line in analyze_poi_taxonomy.py."""

  def test_raw_json_bytes(self):
    """Raw JSON bytes are parsed directly."""
    line = b'{"q":"Q1","t":"Test"}'
    result = parse_poi_line_analyze(line)
    assert result == {'q': 'Q1', 't': 'Test'}

  def test_raw_json_bytes_stripped(self):
    """Leading/trailing whitespace is stripped."""
    line = b'  {"q":"Q1"}  '
    result = parse_poi_line_analyze(line)
    assert result == {'q': 'Q1'}

  def test_raw_json_bytes_with_newline(self):
    """Trailing newline is stripped."""
    line = b'{"q":"Q1"}\n'
    result = parse_poi_line_analyze(line)
    assert result == {'q': 'Q1'}

  def test_json_encoded_string(self):
    """A JSON-encoded Python string literal is evaluated."""
    line = b'b\'{"q":"Q1"}\''
    result = parse_poi_line_analyze(line)
    assert result == {'q': 'Q1'}

  def test_json_encoded_string_double_quotes(self):
    """Double-quoted encoded string is handled."""
    line = b'b"{\\"q\\":\\"Q1\\"}"'
    result = parse_poi_line_analyze(line)
    assert result == {'q': 'Q1'}

  def test_empty_line(self):
    """Empty bytes return empty dict after strip."""
    result = parse_poi_line_analyze(b'')
    assert result == {}


class TestParsePoiLineGraphviz:
  """parse_poi_line in generate_subclass_graphviz.py."""

  def test_raw_json_bytes(self):
    """Raw JSON bytes are parsed directly."""
    line = b'{"q":"Q1","t":"Test"}'
    result = parse_poi_line_graphviz(line)
    assert result == {'q': 'Q1', 't': 'Test'}

  def test_json_encoded_string(self):
    """Encoded string literals are handled."""
    line = b'b\'{"q":"Q1"}\''
    result = parse_poi_line_graphviz(line)
    assert result == {'q': 'Q1'}

  def test_both_parse_poi_line_equivalent(self):
    """Both parse_poi_line implementations produce same results."""
    line = b'{"q":"Q1"}'
    assert parse_poi_line_analyze(line) == parse_poi_line_graphviz(line)
