"""Loads a .gdtf file into a FixtureModel using pygdtf (PARSE-01, D-09).

load() = prevalidate_gdtf_document() -> pygdtf on the already-validated bytes
-> typed errors (RELI-01, RELI-02, D-12). The archive is read once into
memory by prevalidate_gdtf_document(); pygdtf then parses io.BytesIO of those
same bytes, and the same call's validated description_root is handed to
extract_attributes() for its attribute-presence check, so there is no second
disk read and no check-then-parse (TOCTOU) gap -- T-01-15.
"""

import io
import os

import pygdtf

from gdtf_comparer.core.errors import GDTFError, GDTFParseError, GDTFValidationError
from gdtf_comparer.core.extract import extract_attributes
from gdtf_comparer.core.hardening import (
    ValidatedGDTF,
    prevalidate_gdtf_bytes,
    prevalidate_gdtf_document,
)
from gdtf_comparer.core.models import FixtureModel

# Defence in depth: pygdtf substitutes this stub fixture for malformed XML
# instead of raising (RESEARCH Pitfall 1). prevalidate_gdtf() already rejects
# malformed XML before pygdtf ever runs, so this should be unreachable -- but
# it must never be displayed as if it were the user's file if it is.
PYGDTF_BROKEN_XML_STUB_NAME = "Original File Had Broken XML"


class FixtureRepository:
    """Loads GDTF files from disk into FixtureModel instances."""

    def load(self, path: str) -> FixtureModel:
        """Parse a .gdtf file and wrap it in a FixtureModel.

        Parameters:
            path: Path to the .gdtf archive to load.

        Returns:
            A FixtureModel with the namespaced attribute projection
            (core.extract.extract_attributes) and the full pygdtf
            FixtureType retained on .fixture_type (D-09).

        Raises:
            GDTFValidationError: The file is not a valid, safe GDTF archive.
            GDTFUnsafeFileError: The file was rejected by a RELI-02 safety
                limit (subclass of GDTFValidationError).
            GDTFParseError: pygdtf itself failed on the validated bytes, or
                the validated tree could not be paired with pygdtf's parsed
                model (DescriptionMismatchError, reported by exception type
                name only -- never file content).
        """
        return self._model_from_validated(prevalidate_gdtf_document(path), path)

    def load_bytes(self, data: bytes, label: str) -> FixtureModel:
        """Parse already-in-memory GDTF bytes and wrap them in a FixtureModel.

        Parameters:
            data: The raw GDTF archive bytes (e.g. extracted from an MVR zip
                member -- nothing here touches disk).
            label: Stands in for the path in error messages and
                FixtureModel.source_path (e.g. an MVR member name).

        Returns:
            A FixtureModel, exactly like load() but sourced from bytes
            already in memory instead of a file on disk.

        Raises:
            GDTFValidationError: The data is not a valid, safe GDTF archive.
            GDTFUnsafeFileError: The data was rejected by a RELI-02 safety
                limit (subclass of GDTFValidationError).
            GDTFParseError: pygdtf itself failed on the validated bytes.
        """
        return self._model_from_validated(prevalidate_gdtf_bytes(data, label), label)

    def _model_from_validated(self, validated: ValidatedGDTF, label: str) -> FixtureModel:
        """Run pygdtf + typed-error wrapping on already-validated GDTF bytes.

        Parameters:
            validated: The ValidatedGDTF to parse.
            label: Path or label used for error messages, source_path and
                the name fallback.

        Raises:
            GDTFValidationError: The validated bytes do not contain a GDTF
                fixture definition (the stub-name check).
            GDTFParseError: pygdtf itself failed on the validated bytes, or
                the validated tree could not be paired with pygdtf's parsed
                model.
        """
        try:
            with pygdtf.FixtureType(io.BytesIO(validated.archive_bytes)) as fixture_type:
                if fixture_type.name == PYGDTF_BROKEN_XML_STUB_NAME:
                    raise GDTFValidationError(
                        label, "it does not contain a GDTF fixture definition."
                    )
                attributes = extract_attributes(fixture_type, validated.description_root)
                return FixtureModel(
                    source_path=label,
                    name=fixture_type.name or os.path.basename(label),
                    manufacturer=fixture_type.manufacturer or "",
                    attributes=attributes,
                    fixture_type=fixture_type,
                )
        except GDTFError:
            # Already a typed error (e.g. the stub-name check above) --
            # propagate unchanged so callers see the specific failure.
            raise
        except Exception as exc:
            # Anything else from pygdtf/extraction on already-validated bytes
            # is propagated as a typed error so callers can show a friendly
            # message (D-12) instead of an uncaught exception.
            raise GDTFParseError(
                label, f"its GDTF data could not be parsed ({type(exc).__name__})."
            ) from exc
