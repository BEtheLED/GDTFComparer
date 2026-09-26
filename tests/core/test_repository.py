"""Unit tests for core.repository: loader error paths, encoding, no-disk-write.

FixtureRepository.load() = prevalidate_gdtf() -> pygdtf on validated bytes ->
typed errors (RELI-01, D-12). These tests exercise the loader end to end,
including compare_files()'s all-or-nothing batch behavior (D-15).
"""

import os
import tempfile

import pytest

from gdtf_comparer.core import repository as repository_module
from gdtf_comparer.core.comparator import compare_files
from gdtf_comparer.core.errors import GDTFError, GDTFParseError, GDTFValidationError
from gdtf_comparer.core.models import CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, AttributeKey
from gdtf_comparer.core.repository import PYGDTF_BROKEN_XML_STUB_NAME, FixtureRepository


def test_load_valid_gdtf(make_gdtf):
    path = make_gdtf("valid.gdtf", name="Test Fixture", manufacturer="Test Co", weight=42.5)
    repo = FixtureRepository()

    model = repo.load(str(path))

    assert model.name == "Test Fixture"
    assert model.manufacturer == "Test Co"
    weight_key = AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")
    assert model.attributes[weight_key] == 42.5
    assert model.fixture_type is not None


def test_invalid_zip_raises(tmp_path):
    path = tmp_path / "invalid.gdtf"
    path.write_text("not a zip")
    repo = FixtureRepository()

    with pytest.raises(GDTFValidationError) as exc_info:
        repo.load(str(path))

    message = str(exc_info.value)
    assert message.startswith("Could not open 'invalid.gdtf':")
    assert "Traceback" not in message


def test_empty_file_raises(tmp_path):
    path = tmp_path / "empty.gdtf"
    path.write_bytes(b"")
    repo = FixtureRepository()

    with pytest.raises(GDTFValidationError):
        repo.load(str(path))


def test_missing_file_raises(tmp_path):
    path = tmp_path / "does-not-exist.gdtf"
    repo = FixtureRepository()

    with pytest.raises(GDTFValidationError) as exc_info:
        repo.load(str(path))

    assert "could not be read" in str(exc_info.value)


def test_broken_xml_never_returns_placeholder_fixture(make_gdtf):
    path = make_gdtf("broken.gdtf", description="<GDTF><FixtureType></GDTF>")
    repo = FixtureRepository()

    with pytest.raises(GDTFError) as exc_info:
        repo.load(str(path))

    assert PYGDTF_BROKEN_XML_STUB_NAME not in str(exc_info.value)


def test_pygdtf_failure_wrapped(make_gdtf, monkeypatch):
    path = make_gdtf("valid.gdtf")

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(repository_module.pygdtf, "FixtureType", _boom)
    repo = FixtureRepository()

    with pytest.raises(GDTFParseError) as exc_info:
        repo.load(str(path))

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_non_ascii_text_and_path_roundtrip(make_gdtf):
    path = make_gdtf(
        "Lumière Ü.gdtf",
        name="Lumière Ü",
        manufacturer="Städium & Co",
    )
    repo = FixtureRepository()

    model = repo.load(str(path))

    assert model.name == "Lumière Ü"
    assert model.manufacturer == "Städium & Co"
    assert model.file_name == "Lumière Ü.gdtf"


def test_load_writes_nothing_to_disk(make_gdtf, monkeypatch, tmp_path):
    path = make_gdtf("valid.gdtf")

    def _forbidden(*args, **kwargs):
        raise AssertionError("core.repository.load must not touch temp files or directories")

    monkeypatch.setattr(tempfile, "mkdtemp", _forbidden)
    monkeypatch.setattr(tempfile, "TemporaryDirectory", _forbidden)
    monkeypatch.setattr(tempfile, "NamedTemporaryFile", _forbidden)

    before = sorted(os.listdir(tmp_path))
    repo = FixtureRepository()
    repo.load(str(path))
    after = sorted(os.listdir(tmp_path))

    assert before == after


def test_compare_files_with_no_comparisons(make_gdtf):
    target = make_gdtf("target.gdtf", weight=10.0)

    result = compare_files(str(target), [])

    assert result.comparisons == ()
    for row in result.rows:
        assert row.comparison_values == ()


def test_compare_files_fails_whole_batch_naming_bad_file(make_gdtf, tmp_path):
    good = make_gdtf("good.gdtf", weight=10.0)
    bad = tmp_path / "bad.gdtf"
    bad.write_text("not a zip")

    with pytest.raises(GDTFValidationError) as exc_info:
        compare_files(str(good), [str(bad)])

    assert exc_info.value.file_name == "bad.gdtf"
