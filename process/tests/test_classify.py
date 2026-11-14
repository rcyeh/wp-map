"""Tests for classify_classes in download_extract_wikidata.py."""
import sys
import os

import pytest

# We need to inject the fixture into the module path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from download_extract_wikidata import (
    classify_classes,
    _counters,
    load_class_mapping,
)


@pytest.fixture(autouse=True)
def reset_counters():
     """Reset global counters before/after each test."""
     _counters.reset()
    yield
    _counters.reset()


class TestClassifyClasses:
     """classify_classes maps class IDs to category codes."""

     def test_empty_class_ids(self):
         """Empty input produces empty output."""
         assert classify_classes([]) == []

     def test_unknown_class_returns_zero(self):
         """Unseen class IDs get code 0 (ARTICLE_TYPE_UNKNOWN)."""
         # Ensure class_category_map is empty for this test
         original_map = dict(class_category_map)
        class_category_map.clear()
        try:
             result = classify_classes([999999])
             assert result == [0]
        finally:
             class_category_map.clear()
             class_category_map.update(original_map)

     def test_known_category_maps_to_code(self):
         """Known categories map to their integer codes."""
         # Load fixtures
         load_class_mapping()
         original_map = dict(class_category_map)
         try:
             result = classify_classes([4])   # administrative -> 1
             assert result == [1]
             result = classify_classes([8])   # cultural -> 3
             assert result == [3]
             result = classify_classes([19])  # natural -> 5
             assert result == [5]
         finally:
             class_category_map.clear()
             class_category_map.update(original_map)

     def test_mixed_known_and_unknown(self):
         """Mix of known and unknown classes."""
         load_class_mapping()
         original_map = dict(class_category_map)
         try:
             result = classify_classes([4, 999999, 8])
             assert result[0] == 1   # administrative
             assert result[1] == 0   # unknown
             assert result[2] == 3   # cultural
         finally:
             class_category_map.clear()
             class_category_map.update(original_map)

     def test_non_int_class_ids_are_skipped(self):
         """Non-integer class IDs are silently skipped."""
         original_map = dict(class_category_map)
        class_category_map.clear()
        try:
             result = classify_classes(["not_an_int", 999])
             assert result == [0]  # only 999 produces output
         finally:
             class_category_map.clear()
             class_category_map.update(original_map)

     def test_incremental_discovery(self):
         """New classes are added to the map and get code 0."""
         load_class_mapping()
         original_map = dict(class_category_map)
         try:
             result1 = classify_classes([12345])
             assert result1 == [0]
             assert "12345" in class_category_map
             assert class_category_map["12345"] == "unknown"
             # Now it's known
             result2 = classify_classes([12345])
             assert result2 == [0]   # still 0 since unknown -> 0
         finally:
             class_category_map.clear()
             class_category_map.update(original_map)

     def test_all_category_codes(self):
         """Each known category maps to its correct code."""
         mapping = {
             "unknown": 0,
             "administrative": 1,
             "building": 2,
             "cultural": 3,
             "event": 4,
             "natural": 5,
             "transportation": 6,
         }
         for cat_code in mapping.values():
             assert 0 <= cat_code <= 6
         # Verify category_code_map matches
         for cat, expected_code in mapping.items():
             assert category_code_map[cat] == expected_code
