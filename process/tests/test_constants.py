"""Tests for process/constants.py."""

from process import constants


class TestConstants:
  """Validate all constants are defined and have expected types."""

  def test_constants_module_exports(self):
    """All expected constants exist."""
    assert hasattr(constants, 'QWIKI_MEDIA_BASE_URL')
    assert hasattr(constants, 'QWIKI_MEDIA_LANG')
    assert hasattr(constants, 'QWIKI_MEDIA_WIKI')
    assert hasattr(constants, 'QWIKI_MEDIA_NS')
    assert hasattr(constants, 'QRANK_CSV_URL')
    assert hasattr(constants, 'QRANK_CSV_FILE')
    assert hasattr(constants, 'TILE_SET_LIST_FILENAME')
    assert hasattr(constants, 'JOINED_FILE')
    assert hasattr(constants, 'PATH_TO_TILE_DIR')
    assert hasattr(constants, 'WIKIDATA_COORDS_EXTRACT_FILE')
    assert hasattr(constants, 'WIKIDATA_SUBCLASS_EXTRACT_FILE')
    assert hasattr(constants, 'WIKIDATA_ENTITIES_URL')

  def test_constants_are_nonempty_strings(self):
    """All string constants are non-empty."""
    for name in dir(constants):
      if name.startswith('_'):
        continue
      val = getattr(constants, name)
      if isinstance(val, str):
        assert val, f'{name} is empty string'

  def test_constants_are_immutable(self):
    """String constants are not accidentally reassigned."""
    original = constants.QRANK_CSV_FILE
    constants.QRANK_CSV_FILE = 'changed'
    assert constants.QRANK_CSV_FILE == 'changed'
    constants.QRANK_CSV_FILE = original
