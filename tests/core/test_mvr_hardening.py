"""Unit tests for MVR hardening: every damaged/hostile/wrong file ends in one
typed, friendly error -- never a raw AttributeError/KeyError/ValueError or a
traceback, and pymvr is never even constructed when pre-validation fails
(PARSE-02, RESEARCH Pitfalls 1-3).
"""

import os
import sys
import threading
import time

import pytest

from gdtf_comparer.core import hardening
from gdtf_comparer.core.errors import GDTFError, MVRParseError, MVRUnsafeFileError, MVRValidationError
from gdtf_comparer.core.mvr_repository import import_mvr

XXE_SCENE_XML = b"""<?xml version="1.0"?>
<!DOCTYPE GeneralSceneDescription [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<GeneralSceneDescription verMajor="1" verMinor="6"><Scene>&xxe;</Scene></GeneralSceneDescription>
"""

BILLION_LAUGHS_SCENE_XML = b"""<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<GeneralSceneDescription verMajor="1" verMinor="6"><Scene>&lol2;</Scene></GeneralSceneDescription>
"""


def _assert_friendly(exc: Exception, path) -> str:
    """Assert exc is the friendly, traceback-free shape every MVR error must have."""
    message = str(exc)
    assert message.startswith(f"Could not open '{os.path.basename(str(path))}':")
    assert "Traceback" not in message
    return message


def test_not_a_zip(tmp_path):
    path = tmp_path / "bad.mvr"
    path.write_bytes(b"not a zip")

    with pytest.raises(MVRValidationError) as exc_info:
        import_mvr(str(path))

    message = _assert_friendly(exc_info.value, path)
    assert "not a valid MVR file (the file is not a zip archive)" in message


def test_missing_scene_description(make_gdtf):
    path = make_gdtf("mistaken.mvr")

    with pytest.raises(MVRValidationError) as exc_info:
        import_mvr(str(path))

    message = _assert_friendly(exc_info.value, path)
    assert "GeneralSceneDescription.xml is missing" in message


def test_xxe_rejected(make_mvr):
    path = make_mvr("xxe.mvr", scene_xml=XXE_SCENE_XML)

    with pytest.raises(MVRUnsafeFileError) as exc_info:
        import_mvr(str(path))

    message = _assert_friendly(exc_info.value, path)
    assert "/etc/passwd" not in message
    assert "root:" not in message


def test_billion_laughs_rejected(make_mvr):
    path = make_mvr("lolz.mvr", scene_xml=BILLION_LAUGHS_SCENE_XML)

    with pytest.raises(MVRUnsafeFileError) as exc_info:
        import_mvr(str(path))

    _assert_friendly(exc_info.value, path)


def test_malformed_scene_xml(make_mvr):
    path = make_mvr(
        "malformed.mvr", scene_xml=b"<GeneralSceneDescription><Scene></GeneralSceneDescription>"
    )

    with pytest.raises(MVRValidationError) as exc_info:
        import_mvr(str(path))

    message = _assert_friendly(exc_info.value, path)
    assert "not well-formed" in message


def test_wrong_root_or_no_scene(make_mvr):
    wrong_root_path = make_mvr("wrong-root.mvr", scene_xml=b'<?xml version="1.0"?>\n<GDTF/>')
    with pytest.raises(MVRValidationError) as exc_info:
        import_mvr(str(wrong_root_path))
    message = _assert_friendly(exc_info.value, wrong_root_path)
    assert "does not contain an MVR scene description" in message

    no_scene_path = make_mvr(
        "no-scene.mvr",
        scene_xml=b'<?xml version="1.0"?>\n<GeneralSceneDescription verMajor="1" verMinor="6"/>',
    )
    with pytest.raises(MVRValidationError) as exc_info2:
        import_mvr(str(no_scene_path))
    message2 = _assert_friendly(exc_info2.value, no_scene_path)
    assert "does not contain an MVR scene description" in message2


def test_oversized_file_rejected(make_mvr, monkeypatch):
    monkeypatch.setattr(hardening, "MAX_MVR_FILE_BYTES", 1024)
    path = make_mvr("big.mvr", extra_members={"padding.bin": os.urandom(2048)})

    with pytest.raises(MVRUnsafeFileError) as exc_info:
        import_mvr(str(path))

    _assert_friendly(exc_info.value, path)


def test_total_uncompressed_limit_rejected(make_mvr, monkeypatch):
    monkeypatch.setattr(hardening, "MAX_MVR_TOTAL_UNCOMPRESSED_BYTES", 1000)
    padded_scene = (
        '<?xml version="1.0"?>\n'
        '<GeneralSceneDescription verMajor="1" verMinor="6" providerVersion="'
        + ("a" * 1200)
        + '"><Scene><Layers/></Scene></GeneralSceneDescription>\n'
    ).encode("utf-8")
    path = make_mvr("total.mvr", scene_xml=padded_scene)

    with pytest.raises(MVRUnsafeFileError) as exc_info:
        import_mvr(str(path))

    _assert_friendly(exc_info.value, path)


def test_compression_ratio_rejected(make_mvr, monkeypatch):
    monkeypatch.setattr(hardening, "RATIO_CHECK_FLOOR_BYTES", 0)
    path = make_mvr("ratio.mvr", extra_members={"padding.bin": b"\x00" * (1024 * 1024)})

    with pytest.raises(MVRUnsafeFileError) as exc_info:
        import_mvr(str(path))

    _assert_friendly(exc_info.value, path)


def test_scene_xml_size_cap(make_mvr, monkeypatch):
    monkeypatch.setattr(hardening, "MAX_GSD_XML_BYTES", 256)
    path = make_mvr(
        "scene-size.mvr",
        scene_xml=("<GeneralSceneDescription>" + "a" * 2048 + "</GeneralSceneDescription>").encode(
            "utf-8"
        ),
    )

    with pytest.raises(MVRUnsafeFileError) as exc_info:
        import_mvr(str(path))

    _assert_friendly(exc_info.value, path)


def test_folder_rejected(tmp_path):
    if sys.platform == "win32":
        pytest.skip("opening a directory on Windows raises a permission error")

    dir_path = tmp_path / "folder.mvr"
    dir_path.mkdir()

    with pytest.raises(MVRValidationError) as exc_info:
        import_mvr(str(dir_path))

    message = _assert_friendly(exc_info.value, dir_path)
    assert "not a regular file" in message


def test_fifo_rejected_without_blocking(tmp_path):
    if not hasattr(os, "mkfifo"):
        pytest.skip("os.mkfifo is not available on this platform")

    fifo_path = tmp_path / "pipe.mvr"
    os.mkfifo(fifo_path)

    def _keep_fifo_openable() -> None:
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                fd = os.open(str(fifo_path), os.O_WRONLY | os.O_NONBLOCK)
            except OSError:
                pass
            else:
                os.close(fd)
            time.sleep(0.1)

    helper = threading.Thread(target=_keep_fifo_openable, daemon=True)
    helper.start()

    try:
        start = time.monotonic()
        with pytest.raises(MVRValidationError) as exc_info:
            import_mvr(str(fifo_path))
        elapsed = time.monotonic() - start

        message = _assert_friendly(exc_info.value, fifo_path)
        assert "not a regular file" in message
        assert elapsed < 2
    finally:
        helper.join(timeout=5)


def test_unreadable_scene_field_becomes_parse_error(make_mvr):
    layers_xml = (
        '<Layer name="Layer 1" uuid="00000000-0000-4000-8000-200000000001">'
        '<ChildList><Fixture name="F1" uuid="00000000-0000-4000-8000-200000000002">'
        "<FixtureIDNumeric>abc</FixtureIDNumeric></Fixture></ChildList></Layer>"
    )
    path = make_mvr("badfield.mvr", layers_xml=layers_xml)

    with pytest.raises(MVRParseError) as exc_info:
        import_mvr(str(path))

    message = _assert_friendly(exc_info.value, path)
    assert message.endswith("(ValueError).")
    assert "abc" not in message


def test_latin1_scene_becomes_parse_error(make_mvr):
    scene_xml = (
        '<?xml version="1.0" encoding="ISO-8859-1"?>\n'
        '<GeneralSceneDescription verMajor="1" verMinor="6" provider="é">'
        "<Scene><Layers/></Scene></GeneralSceneDescription>\n"
    ).encode("iso-8859-1")
    path = make_mvr("latin1.mvr", scene_xml=scene_xml)

    with pytest.raises(MVRParseError) as exc_info:
        import_mvr(str(path))

    message = _assert_friendly(exc_info.value, path)
    assert "could not be parsed" in message


def test_pymvr_never_sees_unvalidated_bytes(monkeypatch, make_mvr, tmp_path):
    import gdtf_comparer.core.mvr_repository as mvr_repository_module

    def _recorder(*args, **kwargs):
        pytest.fail("pymvr.GeneralSceneDescription must never be called on unvalidated bytes")

    monkeypatch.setattr(mvr_repository_module.pymvr, "GeneralSceneDescription", _recorder)

    not_a_zip = tmp_path / "bad.mvr"
    not_a_zip.write_bytes(b"not a zip")
    with pytest.raises(MVRValidationError):
        import_mvr(str(not_a_zip))

    xxe_path = make_mvr("xxe.mvr", scene_xml=XXE_SCENE_XML)
    with pytest.raises(MVRUnsafeFileError):
        import_mvr(str(xxe_path))

    monkeypatch.setattr(hardening, "MAX_MVR_FILE_BYTES", 10)
    oversized_path = make_mvr("big.mvr")
    with pytest.raises(MVRUnsafeFileError):
        import_mvr(str(oversized_path))


def test_every_mvr_error_is_a_gdtf_error():
    assert issubclass(MVRParseError, GDTFError)
    assert issubclass(MVRUnsafeFileError, MVRValidationError)
