"""Tests for get_all_ancestors in analyze_poi_taxonomy.py."""

import sys
import os
import gzip
import json

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from analyze_poi_taxonomy import get_all_ancestors


class TestGetAllAncestors:
  """get_all_ancestors traverses the subclass graph upward."""

  def test_simple_chain(self):
    """Linear chain: A -> B -> C -> D."""
    graph = {
      100: {'p279': [50]},
      50: {'p279': [25]},
      25: {'p279': [10]},
      10: {'p279': []},
    }
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100, 50, 25, 10}

  def test_diamond_graph(self):
    """Diamond: A -> B, A -> C, B -> D, C -> D."""
    graph = {
      100: {'p279': [50, 60]},
      50: {'p279': [25]},
      60: {'p279': [25]},
      25: {'p279': []},
    }
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100, 50, 60, 25}

  def test_no_ancestors(self):
    """Node with no parents."""
    graph = {100: {'p279': [], 'p31': []}}
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100}

  def test_missing_node_in_graph(self):
    """Missing nodes are silently skipped."""
    graph = {
      100: {'p279': [50]},  # 50 not in graph
    }
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100}

  def test_max_depth_limit(self):
    """Traversal stops at max_depth."""
    graph = {
      100: {'p279': [50]},
      50: {'p279': [25]},
      25: {'p279': [10]},
      10: {'p279': [5]},
      5: {'p279': []},
    }
    # With max_depth=2: 100 -> 50 -> 25 (stop, depth exceeded)
    ancestors = get_all_ancestors(100, graph, max_depth=2)
    assert ancestors == {100, 50, 25}

  def test_max_depth_zero(self):
    """Zero depth returns only the starting node."""
    graph = {100: {'p279': [50]}}
    ancestors = get_all_ancestors(100, graph, max_depth=0)
    assert ancestors == {100}

  def test_orphan_not_in_graph(self):
    """Starting node not in graph returns empty set."""
    graph = {100: {'p279': []}}
    ancestors = get_all_ancestors(999, graph)
    assert ancestors == set()

  def test_self_reference(self):
    """Self-referencing nodes are handled."""
    graph = {100: {'p279': [100]}}
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100}

  def test_deep_chain(self):
    """Deep linear chain works."""
    graph = {}
    for i in range(100, 0, -1):
      graph[i] = {'p279': [i - 1]} if i > 1 else {'p279': []}
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == set(range(1, 101))

  def test_both_p279_and_p31(self):
    """Both subclass (P279) and instance (P31) edges are followed."""
    graph = {
      100: {'p279': [50], 'p31': [60]},
      50: {'p279': [], 'p31': []},
      60: {'p279': [], 'p31': []},
    }
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100, 50, 60}

  def test_p31_only(self):
    """Only P31 edges are followed when no P279."""
    graph = {
      100: {'p279': [], 'p31': [50]},
      50: {'p279': [], 'p31': []},
    }
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100, 50}

  def test_p279_only(self):
    """Only P279 edges are followed when no P31."""
    graph = {
      100: {'p279': [50], 'p31': []},
      50: {'p279': [], 'p31': []},
    }
    ancestors = get_all_ancestors(100, graph)
    assert ancestors == {100, 50}

  def test_empty_graph(self):
    """Empty graph returns only the starting node."""
    ancestors = get_all_ancestors(100, {})
    assert ancestors == {100}
