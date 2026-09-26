"""Loads a .gdtf file into a FixtureModel using pygdtf (PARSE-01, D-09).

Reads the archive in place -- no copying, no temporary directories (avoids
the double-I/O anti-pattern in the old BEtheLD.parse_gdtf()). Errors from
pygdtf/zipfile propagate unchanged for now; Plan 01-04 adds pre-validation
and typed errors inside this same load() call site.
"""

import os

import pygdtf

from gdtf_comparer.core.extract import extract_attributes
from gdtf_comparer.core.models import FixtureModel


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
        """
        # Propagate any pygdtf/zipfile error unchanged so callers can handle
        # it (e.g. tests); Plan 01-04 adds pre-validation + typed errors here.
        with pygdtf.FixtureType(path) as fixture_type:
            attributes = extract_attributes(fixture_type)
            return FixtureModel(
                source_path=path,
                name=fixture_type.name or os.path.basename(path),
                manufacturer=fixture_type.manufacturer or "",
                attributes=attributes,
                fixture_type=fixture_type,
            )
