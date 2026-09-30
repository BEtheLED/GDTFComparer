"""Shared pytest fixtures: GDTF test-file builder and offscreen Qt platform default."""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import zipfile
from pathlib import Path
from typing import Mapping, Optional
from xml.sax.saxutils import quoteattr

import pytest


def build_description_xml(
    *,
    name: str,
    manufacturer: str,
    weight: Optional[float],
    models_xml: str,
    geometries_xml: str,
    attributes_xml: str = "",
) -> str:
    """Build a minimal but well-formed GDTF 1.2 description.xml document.

    Parameters:
        name: Value used for the FixtureType's Name, ShortName and LongName.
        manufacturer: Value used for the FixtureType's Manufacturer.
        weight: Fixture weight in kg. When None, the Weight element is
            omitted entirely from PhysicalDescriptions/Properties.
        models_xml: Raw XML inserted verbatim inside <Models>.
        geometries_xml: Raw XML inserted verbatim inside <Geometries>.
        attributes_xml: Raw XML inserted verbatim inside
            AttributeDefinitions/Attributes.

    Returns:
        A UTF-8 XML document string representing a full GDTF FixtureType.
    """
    name_attr = quoteattr(name)
    manufacturer_attr = quoteattr(manufacturer)

    if weight is None:
        weight_xml = ""
    else:
        weight_xml = f'<Weight Value="{weight}"/>'

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<GDTF DataVersion="1.2">\n'
        "  <FixtureType"
        f" Name={name_attr}"
        f" ShortName={name_attr}"
        f" LongName={name_attr}"
        f" Manufacturer={manufacturer_attr}"
        ' Description=""'
        ' FixtureTypeID="00000000-0000-4000-8000-000000000001"'
        ' RefFT=""'
        ' Thumbnail="">\n'
        "    <AttributeDefinitions>\n"
        "      <ActivationGroups/>\n"
        "      <FeatureGroups/>\n"
        f"      <Attributes>{attributes_xml}</Attributes>\n"
        "    </AttributeDefinitions>\n"
        "    <Wheels/>\n"
        "    <PhysicalDescriptions>\n"
        "      <Properties>\n"
        f"        {weight_xml}\n"
        "      </Properties>\n"
        "    </PhysicalDescriptions>\n"
        f"    <Models>{models_xml}</Models>\n"
        f"    <Geometries>{geometries_xml}</Geometries>\n"
        "    <DMXModes/>\n"
        "    <Revisions/>\n"
        "    <FTPresets/>\n"
        "    <Protocols/>\n"
        "  </FixtureType>\n"
        "</GDTF>\n"
    )


@pytest.fixture
def make_gdtf(tmp_path):
    """Factory fixture that writes .gdtf (zip) archives for tests.

    Returns:
        A callable ``_make(filename, **kwargs) -> Path`` that writes
        ``tmp_path/filename`` as a ZIP_DEFLATED archive containing a
        description.xml member (or the caller's override) plus any extra
        members, and returns the written path.
    """

    def _make(
        filename: str,
        *,
        name: str = "Test Fixture",
        manufacturer: str = "Test Co",
        weight: Optional[float] = 10.0,
        models_xml: str = "",
        geometries_xml: str = "",
        attributes_xml: str = "",
        description: Optional[object] = None,
        include_description: bool = True,
        extra_members: Optional[Mapping[str, bytes]] = None,
    ) -> Path:
        """Write a .gdtf archive and return its path.

        Parameters:
            filename: Name of the archive to create under tmp_path.
            name: Fixture name/short name/long name used when building a
                default description.xml (ignored if description is given).
            manufacturer: Manufacturer used when building a default
                description.xml (ignored if description is given).
            weight: Fixture weight used when building a default
                description.xml (ignored if description is given).
            models_xml: Raw <Models> inner XML for the default description.
            geometries_xml: Raw <Geometries> inner XML for the default
                description.
            attributes_xml: Raw XML inserted verbatim inside
                AttributeDefinitions/Attributes for the default description.
            description: Explicit description.xml content (str or bytes).
                When provided, overrides the generated document entirely.
            include_description: When False, no description.xml member is
                written at all (used to test missing-file error paths).
            extra_members: Additional zip members (name -> bytes) to write.

        Returns:
            Path to the written .gdtf archive.
        """
        archive_path = tmp_path / filename

        if description is None:
            description_content: bytes = build_description_xml(
                name=name,
                manufacturer=manufacturer,
                weight=weight,
                models_xml=models_xml,
                geometries_xml=geometries_xml,
                attributes_xml=attributes_xml,
            ).encode("utf-8")
        elif isinstance(description, bytes):
            description_content = description
        else:
            description_content = description.encode("utf-8")

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if include_description:
                zf.writestr("description.xml", description_content)
            for member_name, member_bytes in (extra_members or {}).items():
                zf.writestr(member_name, member_bytes)

        return archive_path

    return _make
