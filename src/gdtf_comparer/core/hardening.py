"""Size limits, zip-bomb checks and defusedxml pre-parse before pygdtf/pymvr
(RELI-02, PARSE-02).

pygdtf's own internal parser (`xml.etree.ElementTree`) has no XXE/entity or
size hardening and silently substitutes a stub fixture for malformed XML
(RESEARCH Pitfall 1); pymvr has none of its own hardening either (Phase 5
RESEARCH Pitfall 3). prevalidate_gdtf_document() / prevalidate_mvr_document()
run entirely before pygdtf/pymvr ever see a byte: each reads its archive once
into memory, checks size and compression-ratio limits, extracts only the
exact named member (no `extractall`, no temp directory -- T-01-14), and
parses it with defusedxml's forbid_dtd/forbid_entities/forbid_external all
True. Every limit below is a module constant read at call time (never
captured as a default argument), so tests can monkeypatch them directly.

The validated <GDTF> tree it returns (ValidatedGDTF.description_root) is not
just discarded after validation -- core.extract also walks it, in lockstep
with pygdtf's own parsed model, to decide whether each displayed attribute
was actually declared in the manufacturer's file or only backfilled by
pygdtf's spec-default substitution (Plan 01-06).

The GDTF and MVR pipelines share one set of helpers (_read_file_bytes,
_extract_member_bytes, _parse_xml_safely), parameterized by a _FileKind so
every message names the right file kind and member -- never a second,
independently-maintained hardening module (Phase 5 Don't Hand-Roll).
"""

import io
import os
import stat
import zipfile
import zlib
import xml.etree.ElementTree as ET
from typing import NamedTuple

import defusedxml.ElementTree as DET
from defusedxml.common import DefusedXmlException

from gdtf_comparer.core.errors import (
    GDTFUnsafeFileError,
    GDTFValidationError,
    MVRUnsafeFileError,
    MVRValidationError,
)

# [ASSUMED] per RESEARCH A1 -- unbenchmarked reasonable defaults; tune here
# only if real-world fixtures trip them.
MAX_GDTF_FILE_BYTES = 100 * 1024 * 1024
MAX_DESCRIPTION_XML_BYTES = 64 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
RATIO_CHECK_FLOOR_BYTES = 10 * 1024 * 1024

DESCRIPTION_MEMBER = "description.xml"

# [ASSUMED] per Phase 5 RESEARCH A7 -- unbenchmarked reasonable defaults, the
# same posture as the GDTF constants above; module constants read at call
# time so tests can monkeypatch them.
GSD_XML_MEMBER = "GeneralSceneDescription.xml"
MAX_MVR_FILE_BYTES = 500 * 1024 * 1024
MAX_GSD_XML_BYTES = 64 * 1024 * 1024
MAX_MVR_TOTAL_UNCOMPRESSED_BYTES = 2 * 1024 * 1024 * 1024


def _mb(num_bytes: int) -> int:
    """Format a byte count as whole megabytes for a friendly message."""
    return num_bytes // (1024 * 1024)


class _FileKind(NamedTuple):
    """The file-kind-specific pieces _read_file_bytes/_extract_member_bytes/
    _parse_xml_safely need to raise the right typed error with the right
    wording, without duplicating their logic per file kind.

    Parameters:
        label: Short, capitalized name of the file kind used in messages
            ("GDTF" or "MVR").
        validation_error: The typed error class to raise for a not-valid or
            damaged file of this kind.
        unsafe_error: The typed error class to raise for a file of this kind
            rejected by a safety limit.
    """

    label: str
    validation_error: type
    unsafe_error: type


_GDTF_KIND = _FileKind("GDTF", GDTFValidationError, GDTFUnsafeFileError)
_MVR_KIND = _FileKind("MVR", MVRValidationError, MVRUnsafeFileError)


def _damaged_archive_reason(kind: _FileKind) -> str:
    """Return the friendly reason fragment for an archive damaged/encrypted/unsupported."""
    return (
        f"it is not a valid {kind.label} file "
        "(the archive is damaged, encrypted or uses unsupported compression)."
    )


def _read_file_bytes(path: str, limit: int, kind: _FileKind) -> bytes:
    """Read a file into memory, once, after checking it is safe.

    The path is opened exactly once, with O_NONBLOCK when the platform
    supports it, so a folder, named pipe (FIFO) or device file returns
    immediately instead of blocking forever waiting for a writer or for a
    read that will never complete (WR-01, T-01-28). The regular-file check
    (os.fstat + stat.S_ISREG) runs on that same opened descriptor, so a path
    swapped for a pipe or device after it was picked is still refused before
    any read happens (T-01-30) -- there is no separate stat-then-open. Once
    confirmed regular, the descriptor is switched back to blocking mode and
    the file is still read once, in full, into memory (T-01-15).

    Parameters:
        path: Path to the archive to read.
        limit: Maximum number of bytes this file kind may be.
        kind: Which typed errors to raise (_GDTF_KIND or _MVR_KIND).

    Returns:
        The raw bytes of the archive.

    Raises:
        kind.validation_error: The file could not be opened or read
            (missing, permission denied, another OS-level failure), or it is
            not a regular file (a folder, pipe or device).
        kind.unsafe_error: The file is larger than limit.
    """
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise kind.validation_error(
            path, f"the file could not be read ({exc.strerror})."
        ) from exc

    owns_fd = True
    try:
        try:
            st = os.fstat(fd)
        except OSError as exc:
            raise kind.validation_error(
                path, f"the file could not be read ({exc.strerror})."
            ) from exc

        if not stat.S_ISREG(st.st_mode):
            raise kind.validation_error(
                path,
                "it is not a regular file (it may be a folder, pipe or device).",
            )

        if st.st_size > limit:
            raise kind.unsafe_error(
                path,
                "it was rejected for safety reasons "
                f"(the file is {_mb(st.st_size)} MB; the limit is {_mb(limit)} MB).",
            )

        if getattr(os, "O_NONBLOCK", 0):
            os.set_blocking(fd, True)

        try:
            handle = os.fdopen(fd, "rb")
        except OSError as exc:
            raise kind.validation_error(
                path, f"the file could not be read ({exc.strerror})."
            ) from exc
        owns_fd = False

        try:
            with handle:
                data = handle.read(limit + 1)
        except OSError as exc:
            raise kind.validation_error(
                path, f"the file could not be read ({exc.strerror})."
            ) from exc
    finally:
        if owns_fd:
            os.close(fd)

    # A file that grew past the limit between the size check and the read
    # is also unsafe -- never trust the stat() result alone.
    if len(data) > limit:
        raise kind.unsafe_error(
            path,
            f"it was rejected for safety reasons (the file exceeds the {_mb(limit)} MB limit).",
        )
    return data


def read_gdtf_bytes(path: str) -> bytes:
    """Read a .gdtf file into memory, once, after checking it is safe.

    Parameters:
        path: Path to the .gdtf archive to read.

    Returns:
        The raw bytes of the archive.

    Raises:
        GDTFValidationError: The file could not be opened or read, or is not
            a regular file.
        GDTFUnsafeFileError: The file is larger than MAX_GDTF_FILE_BYTES.
    """
    return _read_file_bytes(path, MAX_GDTF_FILE_BYTES, _GDTF_KIND)


def _extract_member_bytes(
    data: bytes,
    path: str,
    member: str,
    max_member_bytes: int,
    max_total_uncompressed_bytes: int,
    kind: _FileKind,
) -> bytes:
    """Open an in-memory zip and return one named member's bytes.

    Only the exact member name is ever read; nothing is unpacked to disk
    (T-01-14). Declared zip-header sizes are never trusted alone -- the
    member is read with a capped read one byte past the limit.

    Parameters:
        data: The raw archive bytes (from _read_file_bytes).
        path: The original file path, used only for error messages.
        member: The exact zip member name to extract.
        max_member_bytes: Maximum number of bytes this member may be.
        max_total_uncompressed_bytes: Maximum total uncompressed size the
            whole archive may expand to.
        kind: Which typed errors to raise (_GDTF_KIND or _MVR_KIND).

    Returns:
        The raw bytes of the named member.

    Raises:
        kind.validation_error: The data is not a valid zip archive, or the
            member is missing, or the archive is damaged/encrypted/uses
            unsupported compression.
        kind.unsafe_error: The archive's declared or actual uncompressed
            size, compression ratio, or member size exceeds a safety limit.
    """
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise kind.validation_error(
            path, f"it is not a valid {kind.label} file (the file is not a zip archive)."
        ) from exc

    try:
        infolist = zf.infolist()
        total_uncompressed = sum(info.file_size for info in infolist)
        total_compressed = sum(info.compress_size for info in infolist)

        oversized_total = total_uncompressed > max_total_uncompressed_bytes
        bad_ratio = (
            total_uncompressed >= RATIO_CHECK_FLOOR_BYTES
            and total_uncompressed / max(total_compressed, 1) > MAX_COMPRESSION_RATIO
        )
        if oversized_total or bad_ratio:
            raise kind.unsafe_error(
                path,
                "it was rejected for safety reasons (its contents expand to an unsafe size).",
            )

        try:
            member_info = zf.getinfo(member)
        except KeyError as exc:
            raise kind.validation_error(
                path, f"it is not a valid {kind.label} file ({member} is missing)."
            ) from exc

        if member_info.file_size > max_member_bytes:
            raise kind.unsafe_error(
                path,
                "it was rejected for safety reasons "
                f"({member} is larger than the {_mb(max_member_bytes)} MB limit).",
            )

        try:
            with zf.open(member_info) as handle:
                member_bytes = handle.read(max_member_bytes + 1)
        except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError) as exc:
            raise kind.validation_error(path, _damaged_archive_reason(kind)) from exc

        # The declared header size can lie -- never trust it alone.
        if len(member_bytes) > max_member_bytes:
            raise kind.unsafe_error(
                path,
                "it was rejected for safety reasons "
                f"({member} is larger than the {_mb(max_member_bytes)} MB limit).",
            )

        return member_bytes
    finally:
        zf.close()


def extract_description_bytes(data: bytes, path: str) -> bytes:
    """Open an in-memory GDTF zip and return its description.xml bytes.

    Parameters:
        data: The raw archive bytes (from read_gdtf_bytes).
        path: The original file path, used only for error messages.

    Returns:
        The raw bytes of the description.xml member.

    Raises:
        GDTFValidationError: The data is not a valid zip archive, or
            description.xml is missing, or the archive is damaged/encrypted/
            uses unsupported compression.
        GDTFUnsafeFileError: The archive's declared or actual uncompressed
            size, compression ratio, or description.xml size exceeds a
            safety limit.
    """
    return _extract_member_bytes(
        data,
        path,
        DESCRIPTION_MEMBER,
        MAX_DESCRIPTION_XML_BYTES,
        MAX_TOTAL_UNCOMPRESSED_BYTES,
        _GDTF_KIND,
    )


def _parse_xml_safely(xml_bytes: bytes, path: str, member: str, kind: _FileKind) -> ET.Element:
    """Parse one member's bytes with defusedxml, rejecting unsafe XML.

    Parameters:
        xml_bytes: The raw bytes of the member.
        path: The original file path, used only for error messages.
        member: The member's name, used only for error messages.
        kind: Which typed errors to raise (_GDTF_KIND or _MVR_KIND).

    Returns:
        The parsed root element.

    Raises:
        kind.unsafe_error: The member declares a DTD or entities (XXE,
            billion-laughs).
        kind.validation_error: The member is not well-formed XML.
    """
    # Mirrors pygdtf's own _find_root(): a single trailing NUL byte is
    # tolerated, exactly like the file this pre-validation stands in front of.
    if xml_bytes.endswith(b"\x00"):
        xml_bytes = xml_bytes[:-1]

    try:
        root = DET.fromstring(
            xml_bytes, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
    except DefusedXmlException as exc:
        raise kind.unsafe_error(
            path,
            "it was rejected for safety reasons "
            f"({member} declares a DTD or entities, which {kind.label} files never use).",
        ) from exc
    except ET.ParseError as exc:
        line, column = exc.position
        raise kind.validation_error(
            path,
            f"it is not a valid {kind.label} file "
            f"({member} is not well-formed XML at line {line}, column {column}).",
        ) from exc

    return root


def parse_description_safely(xml_bytes: bytes, path: str) -> ET.Element:
    """Parse description.xml bytes with defusedxml, rejecting unsafe XML.

    Parameters:
        xml_bytes: The raw bytes of description.xml.
        path: The original file path, used only for error messages.

    Returns:
        The parsed root <GDTF> element.

    Raises:
        GDTFUnsafeFileError: description.xml declares a DTD or entities
            (XXE, billion-laughs).
        GDTFValidationError: description.xml is not well-formed XML, or does
            not contain a GDTF fixture definition.
    """
    root = _parse_xml_safely(xml_bytes, path, DESCRIPTION_MEMBER, _GDTF_KIND)

    if root.tag != "GDTF" or root.find("FixtureType") is None:
        raise GDTFValidationError(
            path, "it does not contain a GDTF fixture definition."
        )

    return root


class ValidatedGDTF(NamedTuple):
    """The result of validating a .gdtf file end to end before pygdtf parses it.

    Parameters:
        archive_bytes: The validated archive bytes, ready to hand to pygdtf.
        description_root: The validated <GDTF> root element, parsed by
            defusedxml with DTD/entities/external references all forbidden.
    """

    archive_bytes: bytes
    description_root: ET.Element


class ValidatedMVR(NamedTuple):
    """The result of validating a .mvr file end to end before pymvr parses it.

    Parameters:
        archive_bytes: The validated archive bytes, ready to hand to pymvr.
        scene_root: The validated <GeneralSceneDescription> root element,
            parsed by defusedxml with DTD/entities/external references all
            forbidden.
    """

    archive_bytes: bytes
    scene_root: ET.Element


def prevalidate_gdtf_bytes(data: bytes, label: str) -> ValidatedGDTF:
    """Validate already-in-memory GDTF bytes before pygdtf ever parses them.

    Parameters:
        data: The raw GDTF archive bytes (e.g. extracted from an MVR zip
            member -- nothing here touches disk).
        label: Used only for error messages and as ValidatedGDTF's implicit
            source identity (e.g. an MVR member name instead of a path).

    Returns:
        A ValidatedGDTF carrying both the validated archive bytes and the
        parsed <GDTF> root element.

    Raises:
        GDTFValidationError: The data is not a valid GDTF archive.
        GDTFUnsafeFileError: The data was rejected by a safety limit.
    """
    if len(data) > MAX_GDTF_FILE_BYTES:
        raise GDTFUnsafeFileError(
            label,
            "it was rejected for safety reasons "
            f"(the file exceeds the {_mb(MAX_GDTF_FILE_BYTES)} MB limit).",
        )
    return ValidatedGDTF(
        archive_bytes=data,
        description_root=parse_description_safely(
            extract_description_bytes(data, label), label
        ),
    )


def prevalidate_gdtf_document(path: str) -> ValidatedGDTF:
    """Validate a .gdtf file end to end before pygdtf ever parses it.

    Parameters:
        path: Path to the .gdtf archive to validate.

    Returns:
        A ValidatedGDTF carrying both the validated archive bytes and the
        parsed <GDTF> root element, produced from a single read of the file
        (T-01-15) -- pygdtf and any attribute-presence check both work from
        the same bytes.

    Raises:
        GDTFValidationError: The file is not a valid GDTF archive.
        GDTFUnsafeFileError: The file was rejected by a safety limit.
    """
    return prevalidate_gdtf_bytes(read_gdtf_bytes(path), path)


def prevalidate_gdtf(path: str) -> bytes:
    """Validate a .gdtf file end to end before pygdtf ever parses it.

    Parameters:
        path: Path to the .gdtf archive to validate.

    Returns:
        The validated archive bytes, ready to hand to pygdtf. Delegates to
        prevalidate_gdtf_document() and discards its parsed tree.

    Raises:
        GDTFValidationError: The file is not a valid GDTF archive.
        GDTFUnsafeFileError: The file was rejected by a safety limit.
    """
    return prevalidate_gdtf_document(path).archive_bytes


def prevalidate_mvr_document(path: str) -> ValidatedMVR:
    """Validate a .mvr file end to end before pymvr ever parses it.

    The same checks that already stand in front of pygdtf now stand in front
    of pymvr too, which has no DTD, entity, size or zip-bomb protection of
    its own (RESEARCH Pitfall 3).

    Parameters:
        path: Path to the .mvr archive to validate.

    Returns:
        A ValidatedMVR carrying both the validated archive bytes (used for
        pymvr AND for later embedded-.gdtf extraction) and the parsed
        <GeneralSceneDescription> root element.

    Raises:
        MVRValidationError: The file is not a valid MVR archive, or does not
            contain an MVR scene description.
        MVRUnsafeFileError: The file was rejected by a safety limit.
    """
    data = _read_file_bytes(path, MAX_MVR_FILE_BYTES, _MVR_KIND)
    xml_bytes = _extract_member_bytes(
        data, path, GSD_XML_MEMBER, MAX_GSD_XML_BYTES, MAX_MVR_TOTAL_UNCOMPRESSED_BYTES, _MVR_KIND
    )
    root = _parse_xml_safely(xml_bytes, path, GSD_XML_MEMBER, _MVR_KIND)

    if root.tag != "GeneralSceneDescription" or root.find("Scene") is None:
        raise MVRValidationError(path, "it does not contain an MVR scene description.")

    return ValidatedMVR(archive_bytes=data, scene_root=root)


def read_mvr_member_bytes(archive_bytes: bytes, path: str, member: str) -> bytes:
    """Read one embedded-GDTF member's bytes from an already-validated MVR archive.

    Parameters:
        archive_bytes: The validated MVR archive bytes (ValidatedMVR.archive_bytes).
        path: The original .mvr file path, used only for error messages.
        member: The exact embedded .gdtf zip member name to read.

    Returns:
        The raw bytes of the named member.

    Raises:
        MVRValidationError: The member is missing, or the archive is
            damaged/encrypted/uses unsupported compression.
        MVRUnsafeFileError: The member's declared or actual size, or the
            archive's total uncompressed size/ratio, exceeds a safety limit.
    """
    return _extract_member_bytes(
        archive_bytes, path, member, MAX_GDTF_FILE_BYTES, MAX_MVR_TOTAL_UNCOMPRESSED_BYTES, _MVR_KIND
    )
