"""Size limits, zip-bomb checks and defusedxml pre-parse before pygdtf (RELI-02).

pygdtf's own internal parser (`xml.etree.ElementTree`) has no XXE/entity or
size hardening and silently substitutes a stub fixture for malformed XML
(RESEARCH Pitfall 1). prevalidate_gdtf() runs entirely before pygdtf ever
sees a byte: it reads the archive once into memory, checks size and
compression-ratio limits, extracts only the exact "description.xml" member
(no `extractall`, no temp directory -- T-01-14), and parses it with
defusedxml's forbid_dtd/forbid_entities/forbid_external all True. Every
limit below is a module constant read at call time (never captured as a
default argument), so tests can monkeypatch them directly.
"""

import io
import os
import zipfile
import zlib
import xml.etree.ElementTree as ET

import defusedxml.ElementTree as DET
from defusedxml.common import DefusedXmlException

from gdtf_comparer.core.errors import GDTFUnsafeFileError, GDTFValidationError

# [ASSUMED] per RESEARCH A1 -- unbenchmarked reasonable defaults; tune here
# only if real-world fixtures trip them.
MAX_GDTF_FILE_BYTES = 100 * 1024 * 1024
MAX_DESCRIPTION_XML_BYTES = 64 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
RATIO_CHECK_FLOOR_BYTES = 10 * 1024 * 1024

DESCRIPTION_MEMBER = "description.xml"

_DAMAGED_ARCHIVE_REASON = (
    "it is not a valid GDTF file "
    "(the archive is damaged, encrypted or uses unsupported compression)."
)


def _mb(num_bytes: int) -> int:
    """Format a byte count as whole megabytes for a friendly message."""
    return num_bytes // (1024 * 1024)


def read_gdtf_bytes(path: str) -> bytes:
    """Read a .gdtf file into memory, once, after checking its size.

    Parameters:
        path: Path to the .gdtf archive to read.

    Returns:
        The raw bytes of the archive.

    Raises:
        GDTFValidationError: The file could not be read (missing, permission
            denied, or another OS-level failure).
        GDTFUnsafeFileError: The file is larger than MAX_GDTF_FILE_BYTES.
    """
    try:
        size = os.path.getsize(path)
    except OSError as exc:
        raise GDTFValidationError(
            path, f"the file could not be read ({exc.strerror})."
        ) from exc

    limit = MAX_GDTF_FILE_BYTES
    if size > limit:
        raise GDTFUnsafeFileError(
            path,
            "it was rejected for safety reasons "
            f"(the file is {_mb(size)} MB; the limit is {_mb(limit)} MB).",
        )

    try:
        with open(path, "rb") as handle:
            data = handle.read(limit + 1)
    except OSError as exc:
        raise GDTFValidationError(
            path, f"the file could not be read ({exc.strerror})."
        ) from exc

    # A file that grew past the limit between the size check and the read
    # is also unsafe -- never trust the stat() result alone.
    if len(data) > limit:
        raise GDTFUnsafeFileError(
            path,
            f"it was rejected for safety reasons (the file exceeds the {_mb(limit)} MB limit).",
        )
    return data


def extract_description_bytes(data: bytes, path: str) -> bytes:
    """Open an in-memory GDTF zip and return its description.xml bytes.

    Only the exact "description.xml" member is ever read; nothing is
    unpacked to disk (T-01-14). Declared zip-header sizes are never trusted
    alone -- the member is read with a capped read one byte past the limit.

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
    try:
        zf = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        raise GDTFValidationError(
            path, "it is not a valid GDTF file (the file is not a zip archive)."
        ) from exc

    try:
        infolist = zf.infolist()
        total_uncompressed = sum(info.file_size for info in infolist)
        total_compressed = sum(info.compress_size for info in infolist)

        oversized_total = total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES
        bad_ratio = (
            total_uncompressed >= RATIO_CHECK_FLOOR_BYTES
            and total_uncompressed / max(total_compressed, 1) > MAX_COMPRESSION_RATIO
        )
        if oversized_total or bad_ratio:
            raise GDTFUnsafeFileError(
                path,
                "it was rejected for safety reasons (its contents expand to an unsafe size).",
            )

        try:
            member_info = zf.getinfo(DESCRIPTION_MEMBER)
        except KeyError as exc:
            raise GDTFValidationError(
                path, "it is not a valid GDTF file (description.xml is missing)."
            ) from exc

        if member_info.file_size > MAX_DESCRIPTION_XML_BYTES:
            raise GDTFUnsafeFileError(
                path,
                "it was rejected for safety reasons "
                f"(description.xml is larger than the {_mb(MAX_DESCRIPTION_XML_BYTES)} MB limit).",
            )

        try:
            with zf.open(member_info) as member:
                xml_bytes = member.read(MAX_DESCRIPTION_XML_BYTES + 1)
        except (zipfile.BadZipFile, zlib.error, EOFError, NotImplementedError, RuntimeError) as exc:
            raise GDTFValidationError(path, _DAMAGED_ARCHIVE_REASON) from exc

        # The declared header size can lie -- never trust it alone.
        if len(xml_bytes) > MAX_DESCRIPTION_XML_BYTES:
            raise GDTFUnsafeFileError(
                path,
                "it was rejected for safety reasons "
                f"(description.xml is larger than the {_mb(MAX_DESCRIPTION_XML_BYTES)} MB limit).",
            )

        return xml_bytes
    finally:
        zf.close()


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
    # Mirrors pygdtf's own _find_root(): a single trailing NUL byte is
    # tolerated, exactly like the file this pre-validation stands in front of.
    if xml_bytes.endswith(b"\x00"):
        xml_bytes = xml_bytes[:-1]

    try:
        root = DET.fromstring(
            xml_bytes, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
    except DefusedXmlException as exc:
        raise GDTFUnsafeFileError(
            path,
            "it was rejected for safety reasons "
            "(description.xml declares a DTD or entities, which GDTF files never use).",
        ) from exc
    except ET.ParseError as exc:
        line, column = exc.position
        raise GDTFValidationError(
            path,
            "it is not a valid GDTF file "
            f"(description.xml is not well-formed XML at line {line}, column {column}).",
        ) from exc

    if root.tag != "GDTF" or root.find("FixtureType") is None:
        raise GDTFValidationError(
            path, "it does not contain a GDTF fixture definition."
        )

    return root


def prevalidate_gdtf(path: str) -> bytes:
    """Validate a .gdtf file end to end before pygdtf ever parses it.

    Parameters:
        path: Path to the .gdtf archive to validate.

    Returns:
        The validated archive bytes, ready to hand to pygdtf.

    Raises:
        GDTFValidationError: The file is not a valid GDTF archive.
        GDTFUnsafeFileError: The file was rejected by a safety limit.
    """
    data = read_gdtf_bytes(path)
    xml_bytes = extract_description_bytes(data, path)
    parse_description_safely(xml_bytes, path)
    return data
