"""Loads/saves a single fixture type's requirements as a shareable sidecar file
(SUB-03, D-07..D-09, Task 2 decision).

A requirements file is a standalone sidecar for exactly one fixture type,
never written into the MVR -- Save Requirements... and Open Requirements...
go only through save_requirements()/load_requirements() here (SUB-03). This
file crosses the phase's main trust boundary: it travels from one person's
machine to another's (D-07), so load_requirements refuses anything it does
not exactly understand rather than guessing at it (prohibition) -- a
damaged, foreign or newer-version file is never partially read or silently
coerced. Writes are atomic exactly like core.profile_repository: a
same-folder temp file is written, flushed, fsynced and then moved over the
old file with os.replace, so a reader never sees a partial file and an
interrupted write leaves the previous file (or no file) untouched. This
module imports neither tempfile nor shutil (the Phase 1 architecture guard).

load_requirements reads with the same regular-file discipline as
core.hardening.read_gdtf_bytes (WR-01): the path is opened once with
O_NONBLOCK so a folder, named pipe or device returns immediately instead of
blocking the GUI thread, and the S_ISREG check runs on that same opened
descriptor. _parse_payload then validates the decoded JSON's shape exactly
-- every top-level, fixture and requirement key set, every value's type and
range -- refusing anything it does not exactly understand rather than
coercing or partially loading it (prohibition).
"""

import json
import math
import os
import stat
import unicodedata
from typing import Any, Dict

from gdtf_comparer.core.errors import RequirementsFileError
from gdtf_comparer.core.models import AttributeKey
from gdtf_comparer.core.substitution import (
    NUMERIC_DIRECTIONS,
    TOLERANCE_KIND,
    Direction,
    Requirement,
    RequirementSet,
)

REQUIREMENTS_FORMAT_ID = "gdtf-comparer-fixture-requirements"
REQUIREMENTS_SCHEMA_VERSION = 1
REQUIREMENTS_FILE_SUFFIX = " requirements.json"

# Discretion value (05-01-PLAN.md): a requirements file larger than this is
# treated as damaged rather than read into memory.
MAX_REQUIREMENTS_FILE_BYTES = 1024 * 1024

# Discretion values (05-04-PLAN.md): bound the parsed size of a requirements
# file so a well-formed but absurd document is refused rather than accepted.
MAX_REQUIREMENTS_COUNT = 1000
MAX_TEXT_FIELD_LENGTH = 300
MAX_SUGGESTED_NAME_LENGTH = 100
DEFAULT_SUGGESTED_NAME = "Fixture"

_INVALID_NAME_CHARACTERS = '/\\:*?"<>|'

_TOP_LEVEL_KEYS = frozenset({"format", "version", "tolerance_kind", "fixture", "requirements"})
_FIXTURE_KEYS = frozenset({"name", "manufacturer", "gdtf_file"})
_REQUIREMENT_KEYS = frozenset({"category", "element", "attribute", "direction", "target", "tolerance"})
_DIRECTION_VALUES = frozenset(direction.value for direction in Direction)

DAMAGED_TEMPLATE = (
    "The requirements file '{file}' could not be read: it is damaged ({detail}). Nothing was loaded."
)
NOT_REQUIREMENTS_TEMPLATE = "'{file}' is not a fixture requirements file. Nothing was loaded."
NEWER_VERSION_TEMPLATE = "'{file}' was saved by a newer version of GDTF Comparer. Nothing was loaded."
TOLERANCE_KIND_TEMPLATE = (
    "'{file}' uses a different kind of tolerance than this version of GDTF Comparer reads. "
    "Nothing was loaded."
)
TOO_LARGE_TEMPLATE = "'{file}' is too large to be a fixture requirements file. Nothing was loaded."
NOT_A_FILE_TEMPLATE = "'{file}' is not a regular file (it may be a folder, pipe or device). Nothing was loaded."
UNREADABLE_TEMPLATE = "The requirements file '{file}' could not be opened ({reason}). Nothing was loaded."
SAVE_FAILED_TEMPLATE = "Could not save the requirements to '{path}' ({reason})."


def suggested_file_name(requirement_set: RequirementSet) -> str:
    """Return a suggested save-dialog file name for requirement_set.

    Parameters:
        requirement_set: The RequirementSet being saved.

    Returns:
        A file name built only from the fixture name: Unicode-NFC
        normalized, every filesystem-reserved character
        (``/\\:*?"<>|``) and every Unicode "Cc"/"Cs"-category control
        character replaced with "_", runs of whitespace collapsed to one
        space, leading/trailing spaces and dots trimmed, and truncated to
        MAX_SUGGESTED_NAME_LENGTH characters -- falling back to
        DEFAULT_SUGGESTED_NAME when nothing is left -- plus
        REQUIREMENTS_FILE_SUFFIX. This result is only ever offered as a
        save-dialog default: the app never joins it to a path itself.
    """
    normalized = unicodedata.normalize("NFC", requirement_set.fixture_name)
    replaced = "".join(
        "_"
        if character in _INVALID_NAME_CHARACTERS or unicodedata.category(character) in ("Cc", "Cs")
        else character
        for character in normalized
    )
    collapsed = " ".join(replaced.split())
    stripped = collapsed.strip(" .")
    truncated = stripped[:MAX_SUGGESTED_NAME_LENGTH].strip(" .")
    stem = truncated or DEFAULT_SUGGESTED_NAME
    return stem + REQUIREMENTS_FILE_SUFFIX


def save_requirements(path: str, requirement_set: RequirementSet) -> None:
    """Atomically save requirement_set as the shareable sidecar file at path (D-08, D-09).

    Parameters:
        path: Path to write the requirements file to.
        requirement_set: The RequirementSet to save.

    The on-disk payload holds only: format, version, tolerance_kind, the
    fixture's name/manufacturer/gdtf_file, and each marked requirement's
    category/element/attribute/target/direction/tolerance -- nothing else
    (D-09: no positions, no other fixtures, no show name). A reader never
    sees a partial file: the write lands in a same-folder temp file, is
    flushed and fsynced, then moved into place with os.replace. An
    interrupted write (the temp write or the final replace failing) leaves
    the previous file -- or no file -- exactly as it was, and never leaves
    a stray temp file behind.

    Raises:
        RequirementsFileError: The file could not be written.
    """
    payload: Dict[str, Any] = {
        "format": REQUIREMENTS_FORMAT_ID,
        "version": REQUIREMENTS_SCHEMA_VERSION,
        "tolerance_kind": TOLERANCE_KIND,
        "fixture": {
            "name": requirement_set.fixture_name,
            "manufacturer": requirement_set.manufacturer,
            "gdtf_file": requirement_set.gdtf_file,
        },
        "requirements": [
            {
                "category": requirement.key.category,
                "element": requirement.key.element_path,
                "attribute": requirement.key.attribute,
                "target": requirement.target,
                "direction": requirement.direction.value,
                "tolerance": requirement.tolerance,
            }
            for requirement in requirement_set.requirements
        ],
    }

    try:
        text = json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    except ValueError as exc:
        raise RequirementsFileError(
            SAVE_FAILED_TEMPLATE.format(path=path, reason=type(exc).__name__)
        ) from exc

    directory = os.path.dirname(os.path.abspath(path))
    tmp_path = os.path.join(
        directory, "." + os.path.basename(path) + "." + os.urandom(8).hex() + ".tmp"
    )
    try:
        try:
            fd = os.open(
                tmp_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                0o644,
            )
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, path)
        except OSError as exc:
            raise RequirementsFileError(
                SAVE_FAILED_TEMPLATE.format(path=path, reason=type(exc).__name__)
            ) from exc
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def _read_requirements_bytes(path: str) -> bytes:
    """Read a requirements file into memory, once, after checking it is safe.

    Mirrors core.hardening.read_gdtf_bytes's WR-01 regular-file discipline:
    the path is opened exactly once, with O_NONBLOCK when the platform
    supports it, so a folder, named pipe or device file returns immediately
    instead of blocking the GUI thread forever. The S_ISREG check runs on
    that same opened descriptor, so a path swapped for a pipe or device
    after it was picked is still refused before any read happens. This is a
    JSON read, not a second archive guard, so it does not duplicate
    core.hardening's zip/XML handling.

    Parameters:
        path: Path to the requirements file to read.

    Returns:
        The raw bytes of the file.

    Raises:
        RequirementsFileError: The file could not be opened or read, is not
            a regular file, or is larger than MAX_REQUIREMENTS_FILE_BYTES
            (checked at call time, so a shrunk limit in tests takes effect
            immediately).
    """
    basename = os.path.basename(path)

    def _unreadable(exc: OSError) -> RequirementsFileError:
        return RequirementsFileError(
            UNREADABLE_TEMPLATE.format(file=basename, reason=exc.strerror or type(exc).__name__)
        )

    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise _unreadable(exc) from exc

    owns_fd = True
    try:
        try:
            st = os.fstat(fd)
        except OSError as exc:
            raise _unreadable(exc) from exc

        if not stat.S_ISREG(st.st_mode):
            raise RequirementsFileError(NOT_A_FILE_TEMPLATE.format(file=basename))

        if st.st_size > MAX_REQUIREMENTS_FILE_BYTES:
            raise RequirementsFileError(TOO_LARGE_TEMPLATE.format(file=basename))

        if getattr(os, "O_NONBLOCK", 0):
            os.set_blocking(fd, True)

        try:
            handle = os.fdopen(fd, "rb")
        except OSError as exc:
            raise _unreadable(exc) from exc
        owns_fd = False

        try:
            with handle:
                data = handle.read(MAX_REQUIREMENTS_FILE_BYTES + 1)
        except OSError as exc:
            raise _unreadable(exc) from exc
    finally:
        if owns_fd:
            os.close(fd)

    # A file that grew past the limit between the fstat check and the read
    # is also too large -- never trust the stat() result alone.
    if len(data) > MAX_REQUIREMENTS_FILE_BYTES:
        raise RequirementsFileError(TOO_LARGE_TEMPLATE.format(file=basename))

    return data


def _no_duplicate_keys(pairs):
    """object_pairs_hook: refuse a JSON object with a repeated key.

    Parameters:
        pairs: The (key, value) pairs of one JSON object, in document order.

    Returns:
        A plain dict built from pairs.

    Raises:
        ValueError: The same key appears more than once in pairs.
    """
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _refuse_constant(name: str) -> None:
    """parse_constant: refuse a raw NaN/Infinity/-Infinity token.

    Parameters:
        name: The token json.loads encountered ("NaN", "Infinity" or
            "-Infinity").

    Raises:
        ValueError: Always -- these tokens are never valid here.
    """
    raise ValueError(f"{name} is not allowed")


def load_requirements(path: str) -> RequirementSet:
    """Load a shareable requirements sidecar file (SUB-03).

    Parameters:
        path: Path to the requirements file to load.

    Returns:
        The RequirementSet the file describes.

    Raises:
        RequirementsFileError: The file is too large, damaged, not a
            requirements file, or was saved by a newer version of this app.
            Nothing is loaded in any of these cases.
    """
    basename = os.path.basename(path)
    raw = _read_requirements_bytes(path)

    try:
        payload = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_no_duplicate_keys,
            parse_constant=_refuse_constant,
        )
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise RequirementsFileError(
            DAMAGED_TEMPLATE.format(file=basename, detail=type(exc).__name__)
        ) from exc

    return _parse_payload(payload, basename)


def _parse_payload(payload: object, file_name: str) -> RequirementSet:
    """Validate a decoded requirements payload's shape and build a RequirementSet.

    Every check refuses rather than coerces (prohibition): an unexpected
    key set, type or value stops the whole load with a short, fixed-phrase
    detail -- never file content -- so a damaged, foreign or newer-shape
    file is never partially read.

    Parameters:
        payload: The json.loads() result of a requirements file's contents.
        file_name: The file's basename, used only for error messages.

    Returns:
        The RequirementSet the payload describes.

    Raises:
        RequirementsFileError: The payload is not a requirements file, is
            damaged, was saved by a newer version, or uses a different
            tolerance kind.
    """

    def _damaged(detail: str) -> RequirementsFileError:
        return RequirementsFileError(DAMAGED_TEMPLATE.format(file=file_name, detail=detail))

    # The format check comes first, so another app's JSON is reported as
    # "not a requirements file", never "damaged".
    if not isinstance(payload, dict) or payload.get("format") != REQUIREMENTS_FORMAT_ID:
        raise RequirementsFileError(NOT_REQUIREMENTS_TEMPLATE.format(file=file_name))

    version = payload.get("version")
    if type(version) is not int:
        raise _damaged("unexpected layout")
    if version > REQUIREMENTS_SCHEMA_VERSION:
        raise RequirementsFileError(NEWER_VERSION_TEMPLATE.format(file=file_name))
    if version != REQUIREMENTS_SCHEMA_VERSION:
        raise _damaged("unexpected version")

    if set(payload.keys()) != _TOP_LEVEL_KEYS:
        raise _damaged("unexpected layout")

    if payload["tolerance_kind"] != TOLERANCE_KIND:
        raise RequirementsFileError(TOLERANCE_KIND_TEMPLATE.format(file=file_name))

    fixture = payload["fixture"]
    if not isinstance(fixture, dict) or set(fixture.keys()) != _FIXTURE_KEYS:
        raise _damaged("unexpected layout")
    for field_name in _FIXTURE_KEYS:
        value = fixture[field_name]
        if not isinstance(value, str) or len(value) > MAX_TEXT_FIELD_LENGTH:
            raise _damaged("invalid value")
    if not fixture["name"].strip():
        raise _damaged("invalid value")

    requirements_raw = payload["requirements"]
    if not isinstance(requirements_raw, list) or len(requirements_raw) > MAX_REQUIREMENTS_COUNT:
        raise _damaged("unexpected layout")

    requirements = []
    seen_triples = set()
    for entry in requirements_raw:
        if not isinstance(entry, dict) or set(entry.keys()) != _REQUIREMENT_KEYS:
            raise _damaged("unexpected layout")

        category = entry["category"]
        element = entry["element"]
        attribute = entry["attribute"]
        direction_value = entry["direction"]
        target = entry["target"]
        tolerance = entry["tolerance"]

        if not isinstance(category, str) or not category or len(category) > MAX_TEXT_FIELD_LENGTH:
            raise _damaged("invalid value")
        if not isinstance(element, str) or len(element) > MAX_TEXT_FIELD_LENGTH:
            raise _damaged("invalid value")
        if not isinstance(attribute, str) or not attribute or len(attribute) > MAX_TEXT_FIELD_LENGTH:
            raise _damaged("invalid value")

        if not isinstance(direction_value, str) or direction_value not in _DIRECTION_VALUES:
            raise _damaged("invalid value")
        direction = Direction(direction_value)

        if type(tolerance) not in (int, float) or not math.isfinite(tolerance) or tolerance < 0:
            raise _damaged("invalid value")

        if direction in NUMERIC_DIRECTIONS:
            if type(target) not in (int, float) or not math.isfinite(target):
                raise _damaged("invalid value")
        else:
            if type(target) not in (int, float, str):
                raise _damaged("invalid value")
            if isinstance(target, float) and not math.isfinite(target):
                raise _damaged("invalid value")

        triple = (category, element, attribute)
        if triple in seen_triples:
            raise _damaged("duplicate attribute")
        seen_triples.add(triple)

        requirements.append(
            Requirement(
                key=AttributeKey(category=category, element_path=element, attribute=attribute),
                target=target,
                direction=direction,
                tolerance=tolerance,
            )
        )

    return RequirementSet(
        fixture_name=fixture["name"],
        manufacturer=fixture["manufacturer"],
        gdtf_file=fixture["gdtf_file"],
        requirements=tuple(requirements),
    )
