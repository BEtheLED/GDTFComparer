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
"""

import json
import os
import unicodedata
from typing import Any, Dict

from gdtf_comparer.core.errors import RequirementsFileError
from gdtf_comparer.core.models import AttributeKey
from gdtf_comparer.core.substitution import TOLERANCE_KIND, Direction, Requirement, RequirementSet

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

    try:
        with open(path, "rb") as fh:
            raw = fh.read(MAX_REQUIREMENTS_FILE_BYTES + 1)
    except OSError as exc:
        raise RequirementsFileError(
            UNREADABLE_TEMPLATE.format(file=basename, reason=exc.strerror or type(exc).__name__)
        ) from exc

    if len(raw) > MAX_REQUIREMENTS_FILE_BYTES:
        raise RequirementsFileError(TOO_LARGE_TEMPLATE.format(file=basename))

    def _damaged(detail: str) -> RequirementsFileError:
        return RequirementsFileError(DAMAGED_TEMPLATE.format(file=basename, detail=detail))

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise _damaged(type(exc).__name__) from exc

    return _parse_payload(payload, basename)


def _parse_payload(payload: object, file_name: str) -> RequirementSet:
    """Validate a decoded requirements payload's shape and build a RequirementSet.

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

    if not isinstance(payload, dict) or payload.get("format") != REQUIREMENTS_FORMAT_ID:
        raise RequirementsFileError(NOT_REQUIREMENTS_TEMPLATE.format(file=file_name))

    version = payload.get("version")
    if type(version) is not int:
        raise _damaged("unexpected layout")
    if version > REQUIREMENTS_SCHEMA_VERSION:
        raise RequirementsFileError(NEWER_VERSION_TEMPLATE.format(file=file_name))
    if version != REQUIREMENTS_SCHEMA_VERSION:
        raise _damaged("unexpected layout")

    if payload.get("tolerance_kind") != TOLERANCE_KIND:
        raise RequirementsFileError(TOLERANCE_KIND_TEMPLATE.format(file=file_name))

    try:
        fixture = payload["fixture"]
        requirements = tuple(
            Requirement(
                key=AttributeKey(
                    category=str(entry["category"]),
                    element_path=str(entry["element"]),
                    attribute=str(entry["attribute"]),
                ),
                target=entry["target"],
                direction=Direction(entry["direction"]),
                tolerance=entry["tolerance"],
            )
            for entry in payload["requirements"]
        )
        return RequirementSet(
            fixture_name=str(fixture["name"]),
            manufacturer=str(fixture["manufacturer"]),
            gdtf_file=str(fixture["gdtf_file"]),
            requirements=requirements,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise _damaged(type(exc).__name__) from exc
