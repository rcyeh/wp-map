"""Tests for ProcessingCounters in download_extract_wikidata.py."""

import sys
from process.download_extract_wikidata import ProcessingCounters, _counters


class TestProcessingCounters:
  """Thread-safe counter operations."""

  def setup_method(self):
    """Create fresh counter instance for each test."""
    self.counters = ProcessingCounters()

  # -- Init --

  def test_init_defaults_all_to_zero(self):
    """All counters start at zero."""
    assert self.counters.current_bytes == 0
    assert self.counters.coords_written == 0
    assert self.counters.rejects_written == 0
    assert self.counters.subclasses_written == 0

  def test_snapshot_initial(self):
    """Snapshot of fresh counters returns all zeros."""
    result = self.counters.snapshot()
    assert result == (0, 0, 0, 0)

  # -- Increments --

  def test_inc_bytes(self):
    """inc_bytes adds to current_bytes."""
    self.counters.inc_bytes(100)
    assert self.counters.current_bytes == 100
    self.counters.inc_bytes(50)
    assert self.counters.current_bytes == 150

  def test_inc_coords(self):
    """inc_coords increments coords_written."""
    self.counters.inc_coords()
    assert self.counters.coords_written == 1
    self.counters.inc_coords(5)
    assert self.counters.coords_written == 6

  def test_inc_rejects(self):
    """inc_rejects increments rejects_written."""
    self.counters.inc_rejects()
    assert self.counters.rejects_written == 1
    self.counters.inc_rejects(3)
    assert self.counters.rejects_written == 4

  def test_inc_subclasses(self):
    """inc_subclasses increments subclasses_written."""
    self.counters.inc_subclasses()
    assert self.counters.subclasses_written == 1
    self.counters.inc_subclasses(2)
    assert self.counters.subclasses_written == 3

  # -- Snapshot --

  def test_snapshot_after_operations(self):
    """Snapshot reflects all increments."""
    self.counters.inc_bytes(1000)
    self.counters.inc_coords(3)
    self.counters.inc_rejects(1)
    self.counters.inc_subclasses(5)
    result = self.counters.snapshot()
    assert result == (1000, 3, 1, 5)

  # -- Reset --

  def test_reset_clears_all(self):
    """reset() zeroes all counters."""
    self.counters.inc_bytes(1000)
    self.counters.inc_coords(3)
    self.counters.inc_rejects(1)
    self.counters.inc_subclasses(5)
    self.counters.reset()
    assert self.counters.current_bytes == 0
    assert self.counters.coords_written == 0
    assert self.counters.rejects_written == 0
    assert self.counters.subclasses_written == 0

  def test_snapshot_after_reset(self):
    """Snapshot after reset returns all zeros."""
    self.counters.inc_bytes(100)
    self.counters.reset()
    assert self.counters.snapshot() == (0, 0, 0, 0)

  # -- Context manager --

  def test_enter_returns_self(self):
    """__enter__ returns the instance."""
    assert self.counters.__enter__() is self.counters

  def test_exit_noop(self):
    """__exit__ does not raise."""
    assert self.counters.__exit__(None, None, None) is None

  # -- Global instance --

  def test_global_counters_initial_state(self):
    """The module-level _counters starts at zero."""
    assert _counters.current_bytes == 0
    assert _counters.coords_written == 0
    assert _counters.rejects_written == 0
    assert _counters.subclasses_written == 0


class TestProcessingCountersEdgeCases:
  """Boundary and edge-case behavior."""

  def setup_method(self):
    self.counters = ProcessingCounters()

  def test_inc_by_large_number(self):
    """Large increments work correctly."""
    self.counters.inc_bytes(1024 * 1024 * 1024 * 10)  # 10 GB
    assert self.counters.current_bytes == 1024 * 1024 * 1024 * 10

  def test_inc_by_zero(self):
    """inc with n=0 is a no-op."""
    self.counters.inc_bytes(100)
    self.counters.inc_bytes(0)
    assert self.counters.current_bytes == 100

  def test_snapshot_is_independent(self):
    """Snapshot does not alias internal state."""
    self.counters.inc_bytes(50)
    snap1 = self.counters.snapshot()
    self.counters.inc_bytes(50)
    snap2 = self.counters.snapshot()
    assert snap1 != snap2
    assert snap1[0] == 50  # snap1 unchanged after second increment
    assert snap2[0] == 100
