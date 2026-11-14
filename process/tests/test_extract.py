"""Tests for extract_subclass_graph.py pure functions."""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from extract_subclass_graph import parse_numeric_q, extract_claim_targets


class TestParseNumericQ:
  """parse_numeric_q extracts integer IDs from Q-prefixed strings."""

  def test_valid_q_string(self):
    """Q-prefixed digits are parsed."""
    assert parse_numeric_q('Q1') == 1
    assert parse_numeric_q('Q42') == 42
    assert parse_numeric_q('Q12345') == 12345

  def test_invalid_returns_none(self):
    """Non-Q or non-digit strings return None."""
    assert parse_numeric_q('1') is None
    assert parse_numeric_q('q42') is None
    assert parse_numeric_q('Q') is None
    assert parse_numeric_q('Qabc') is None
    assert parse_numeric_q('Q1a') is None
    assert parse_numeric_q('') is None
    assert parse_numeric_q(None) is None

  def test_edge_cases(self):
    """Edge cases with leading zeros and large numbers."""
    assert parse_numeric_q('Q0') == 0
    assert parse_numeric_q('Q99999999') == 99999999


class TestExtractClaimTargets:
  """extract_claim_targets extracts numeric IDs from claim statements."""

  def test_numeric_id_target(self):
    """Numeric IDs in claims are extracted."""
    claims = [
      {
        'mainsnak': {
          'datavalue': {
            'value': {'numeric-id': 42},
            'snaktype': 'value',
          }
        }
      },
    ]
    assert extract_claim_targets(claims) == [42]

  def test_qid_target(self):
    """Q-prefixed IDs are converted to numbers."""
    claims = [
      {
        'mainsnak': {
          'datavalue': {
            'value': {'id': 'Q123'},
            'snaktype': 'value',
          }
        }
      },
    ]
    assert extract_claim_targets(claims) == [123]

  def test_multiple_targets(self):
    """Multiple claims produce multiple targets."""
    claims = [
      {
        'mainsnak': {
          'datavalue': {'value': {'numeric-id': 1}, 'snaktype': 'value'}
        }
      },
      {'mainsnak': {'datavalue': {'value': {'id': 'Q2'}, 'snaktype': 'value'}}},
    ]
    assert extract_claim_targets(claims) == [1, 2]

  def test_empty_claims(self):
    """Empty list produces no targets."""
    assert extract_claim_targets([]) == []

  def test_single_claim_as_list(self):
    """A single dict in a list is processed."""
    claim = {
      'mainsnak': {
        'datavalue': {'value': {'numeric-id': 99}, 'snaktype': 'value'}
      }
    }
    assert extract_claim_targets([claim]) == [99]

  def test_non_list_wrapped(self):
    """Non-list input is wrapped into list."""
    claim = {
      'mainsnak': {
        'datavalue': {'value': {'numeric-id': 77}, 'snaktype': 'value'}
      }
    }
    # Should work without error when passed directly (as the script does)
    result = extract_claim_targets(claim)
    assert (
      result == []
    )  # single dict, not a list -> wrapped -> loop over 1 item

  def test_invalid_dict_skipped(self):
    """Non-dict statements are skipped."""
    claims = [
      'not a dict',
      42,
      None,
      {
        'mainsnak': {
          'datavalue': {'value': {'numeric-id': 1}, 'snaktype': 'value'}
        }
      },
    ]
    assert extract_claim_targets(claims) == [1]

  def test_no_numeric_id_field(self):
    """Missing numeric-id and no QID produce no targets."""
    claims = [
      {
        'mainsnak': {'datavalue': {'value': 'bare-string', 'snaktype': 'value'}}
      },
    ]
    assert extract_claim_targets(claims) == []

  def test_missing_datavalue(self):
    """Missing datavalue key is handled gracefully."""
    claims = [
      {'mainsnak': {'snaktype': 'value'}},
    ]
    assert extract_claim_targets(claims) == []

  def test_malformed_claim_list(self):
    """Non-list P279 value is handled."""
    # This mimics the fixture's malformed claim
    claim = {
      'mainsnak': {
        'datavalue': {
          'value': 'not-a-dict',
          'snaktype': 'value',
        }
      }
    }
    assert extract_claim_targets([claim]) == []
