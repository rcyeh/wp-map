"""Tests for extract_wikidata in download_extract_wikidata.py."""
import sys
import os
import gzip
import json
import io

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from download_extract_wikidata import (
    extract_wikidata,
    _counters,
    COORD_PROP_BYTES,
    SUBCLASS_PROP_BYTES,
)


@pytest.fixture(autouse=True)
def reset_counters():
     _counters.reset()
    yield
    _counters.reset()


class TestExtractWikidata:
     """extract_wikidata processes Wikidata JSON lines."""

     def test_no_coords_no_subclass(self):
         """Line without P625 or P279 is a no-op."""
         line = b'{"id":"Q1","claims":{}}'
         extract_wikidata(line)
         assert _counters.coords_written == 0
         assert _counters.rejects_written == 0
         assert _counters.subclasses_written == 0

     def test_subclass_only(self):
         """P279-only line increments subclass counter."""
         line = b'{"id":"Q1","claims":{"P279":[{}]}}'
         extract_wikidata(line)
         assert _counters.subclasses_written == 1

     def test_coords_only(self):
         """Line with P625 coords extracts and writes."""
         line = b'{"id":"Q1","claims":{"P625":[{}],"P31":[{"mainsnak":{"datavalue":{"value":{"numeric-id":1}}}]}},sitelinks":{"enwiki":{"title":"Test"}}}'
         extract_wikidata(line)
         assert _counters.coords_written == 1

     def test_coords_and_subclass(self):
         """Line with both P625 and P279 writes both."""
         line = (
             b'{"id":"Q1","claims":{"P625":[{}],"P279":[{}]}}'
             b',sitelinks":{"enwiki":{"title":"Test"}}'
         )
         extract_wikidata(line)
         assert _counters.coords_written == 1
         assert _counters.subclasses_written == 1

     def test_coords_rejected(self):
         """Valid coords but no sitelink -> rejected."""
         line = b'{"id":"Q1","claims":{"P625":[{}]}}'
         extract_wikidata(line)
         assert _counters.coords_written == 0
         assert _counters.rejects_written == 1

     def test_invalid_json(self):
         """Invalid JSON is rejected."""
         line = b'{"id":"Q1",invalid}'
         extract_wikidata(line)
         assert _counters.rejects_written == 1

     def test_classify_classes_integration(self):
         """Class IDs from P31 are classified."""
         line = (
             b'{"id":"Q1","claims":{"P625":[{}],"\