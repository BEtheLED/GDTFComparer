"""Loads/saves a single fixture type's requirements as a shareable sidecar file
(SUB-03, D-07..D-09, Task 2 decision).

A requirements file is a standalone sidecar for exactly one fixture type,
never written into the MVR -- Save Requirements... and Open Requirements...
go only through save_requirements()/load_requirements() here (SUB-03).
Writes are atomic exactly like core.profile_repository: a same-folder temp
file is written, flushed, fsynced and then moved over the old file with
os.replace. This module imports neither tempfile nor shutil (the Phase 1
architecture guard).
"""

import json
import os
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

_INVALID_NAME_CHARACTERS = '/\\:*?"<>|'


def suggested_file_name(requirement_set: RequirementSet) -> str:
    """Return a suggested save-dialog file name for requirement_set.

    Parameters:
        requirement_set: The RequirementSet being saved.

    Returns:
        The fixture name with every filesystem-unsafe or control character
        replaced by "_", falling back to "Fixture" when the name is empty
        after trimming, plus REQUIREMENTS_FILE_SUFFIX.
    """
    name = requirement_set.fixture_name.strip() or "Fixture"
    cleaned = "".join(
        "_" if character in _INVALID_NAME_CHARACTERS or not character.isprintable() else character
        for character in name
    )
    return cleaned + REQUIREMENTS_FILE_SUFFIX


def save_requirements(path: str, requirement_set: RequirementSet) -> None:
    """Atomically save requirement_set as the shareable sidecar file at path (D-08, D-09).

    Parameters:
        path: Path to write the requirements file to.
        requirement_set: The RequirementSet to save.

    The on-disk payload holds only: format, version, tolerance_kind, the
    fixture's name/manufacturer/gdtf_file, and each marked requirement's
    category/element/attribute/target/direction/tolerance -- nothing else
    (D-09: no positions, no other fixtures, no show name).

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
            f"Could not save the requirements to '{path}' ({type(exc).__name__})."
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
                f"Could not save the requirements to '{path}' ({type(exc).__name__})."
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
            f"The requirements file '{basename}' could not be read: "
            f"it is damaged ({type(exc).__name__}). Nothing was loaded."
        ) from exc

    if len(raw) > MAX_REQUIREMENTS_FILE_BYTES:
        raise RequirementsFileError(
            f"'{basename}' is too large to be a fixture requirements file. Nothing was loaded."
        )

    def _damaged(detail: str) -> RequirementsFileError:
        return RequirementsFileError(
            f"The requirements file '{basename}' could not be read: "
            f"it is damaged ({detail}). Nothing was loaded."
        )

    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise _damaged(type(exc).__name__) from exc

    if not isinstance(payload, dict) or payload.get("format") != REQUIREMENTS_FORMAT_ID:
        raise RequirementsFileError(f"'{basename}' is not a fixture requirements file. Nothing was loaded.")

    version = payload.get("version")
    if type(version) is not int:
        raise _damaged("unexpected layout")
    if version > REQUIREMENTS_SCHEMA_VERSION:
        raise RequirementsFileError(
            f"'{basename}' was saved by a newer version of GDTF Comparer. Nothing was loaded."
        )
    if version != REQUIREMENTS_SCHEMA_VERSION:
        raise _damaged("unexpected layout")

    if payload.get("tolerance_kind") != TOLERANCE_KIND:
        raise _damaged("unexpected layout")

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
                tolerance=float(entry["tolerance"]),
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
