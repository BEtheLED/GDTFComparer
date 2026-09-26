"""Unit tests for core.hardening: pre-validation before pygdtf (RELI-02).

Every hardening limit is a module constant read at call time (never
captured as a default argument), so these tests shrink the limits via
monkeypatch instead of writing real 100 MB / 1 GB files.
"""

import os
import zipfile

import pytest

from gdtf_comparer.core import hardening
from gdtf_comparer.core.errors import GDTFUnsafeFileError, GDTFValidationError
from gdtf_comparer.core.hardening import prevalidate_gdtf

XXE_PAYLOAD = b"""<?xml version="1.0"?>
<!DOCTYPE GDTF [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<GDTF DataVersion="1.2"><FixtureType Name="&xxe;"/></GDTF>
"""

BILLION_LAUGHS_PAYLOAD = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<GDTF DataVersion="1.2"><FixtureType Name="&lol2;"/></GDTF>
"""


def test_malformed_xml_raises(make_gdtf):
    path = make_gdtf("malformed.gdtf", description="<GDTF><FixtureType></GDTF>")

    with pytest.raises(GDTFValidationError) as exc_info:
        prevalidate_gdtf(str(path))

    message = str(exc_info.value)
    assert "malformed.gdtf" in message
    assert "not well-formed" in message


def test_xxe_rejected(make_gdtf):
    path = make_gdtf("xxe.gdtf", description=XXE_PAYLOAD)

    with pytest.raises(GDTFUnsafeFileError) as exc_info:
        prevalidate_gdtf(str(path))

    message = str(exc_info.value)
    assert "/etc/passwd" not in message
    assert "root:" not in message


def test_billion_laughs_rejected(make_gdtf):
    path = make_gdtf("lolz.gdtf", description=BILLION_LAUGHS_PAYLOAD)

    with pytest.raises(GDTFUnsafeFileError):
        prevalidate_gdtf(str(path))


def test_oversized_file_rejected(make_gdtf, monkeypatch):
    monkeypatch.setattr(hardening, "MAX_GDTF_FILE_BYTES", 1024)
    path = make_gdtf("big.gdtf", extra_members={"padding.bin": os.urandom(2048)})

    with pytest.raises(GDTFUnsafeFileError):
        prevalidate_gdtf(str(path))


def test_compression_ratio_rejected(make_gdtf, monkeypatch):
    monkeypatch.setattr(hardening, "RATIO_CHECK_FLOOR_BYTES", 0)
    path = make_gdtf(
        "ratio.gdtf",
        extra_members={"padding.bin": b"\x00" * (1024 * 1024)},
    )

    with pytest.raises(GDTFUnsafeFileError):
        prevalidate_gdtf(str(path))


def test_total_uncompressed_limit_rejected(make_gdtf, monkeypatch):
    monkeypatch.setattr(hardening, "MAX_TOTAL_UNCOMPRESSED_BYTES", 1000)
    padded_description = (
        '<GDTF DataVersion="1.2"><FixtureType Name="X" Padding="'
        + ("a" * 1200)
        + '"/></GDTF>'
    )
    path = make_gdtf("total.gdtf", description=padded_description)

    with pytest.raises(GDTFUnsafeFileError):
        prevalidate_gdtf(str(path))


def test_description_size_cap_uses_actual_bytes(make_gdtf, monkeypatch):
    monkeypatch.setattr(hardening, "MAX_DESCRIPTION_XML_BYTES", 512)
    path = make_gdtf("desc-size.gdtf", description="<GDTF>" + "a" * 2048 + "</GDTF>")

    with pytest.raises(GDTFUnsafeFileError):
        prevalidate_gdtf(str(path))


def test_missing_description_rejected(make_gdtf):
    path = make_gdtf("missing-desc.gdtf", include_description=False)

    with pytest.raises(GDTFValidationError) as exc_info:
        prevalidate_gdtf(str(path))

    assert "description.xml is missing" in str(exc_info.value)


def test_miscased_description_rejected(tmp_path):
    path = tmp_path / "miscased.gdtf"
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("Description.xml", b"<GDTF><FixtureType/></GDTF>")

    with pytest.raises(GDTFValidationError) as exc_info:
        prevalidate_gdtf(str(path))

    assert "description.xml is missing" in str(exc_info.value)


def test_non_gdtf_root_rejected(make_gdtf):
    path = make_gdtf("non-gdtf.gdtf", description="<Foo/>")

    with pytest.raises(GDTFValidationError) as exc_info:
        prevalidate_gdtf(str(path))

    assert "does not contain a GDTF fixture definition" in str(exc_info.value)


def test_trailing_nul_accepted(make_gdtf):
    xml = (
        '<?xml version="1.0"?>\n'
        '<GDTF DataVersion="1.2"><FixtureType Name="Valid"/></GDTF>\n'
    )
    path = make_gdtf("trailing-nul.gdtf", description=(xml.encode("utf-8") + b"\x00"))

    prevalidate_gdtf(str(path))  # must not raise


def test_valid_file_passes_prevalidation(make_gdtf):
    path = make_gdtf("valid.gdtf")

    data = prevalidate_gdtf(str(path))

    assert isinstance(data, bytes)
    assert len(data) > 0
