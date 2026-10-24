"""Shared pytest fixtures: GDTF/MVR test-file builders and offscreen Qt platform default."""

import itertools
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import io
import zipfile
from pathlib import Path
from typing import Mapping, Optional, Sequence, Tuple, Union
from xml.sax.saxutils import escape, quoteattr

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


def build_gdtf_bytes(
    *,
    name: str = "Test Fixture",
    manufacturer: str = "Test Co",
    weight: Optional[float] = 10.0,
    models_xml: str = "",
    geometries_xml: str = "",
    attributes_xml: str = "",
) -> bytes:
    """Build a minimal .gdtf archive entirely in memory, as bytes.

    Parameters mirror make_gdtf's defaults -- this is its byte-producing
    sibling, for embedding a GDTF as an MVR zip member (never written to
    disk as its own file).

    Returns:
        A ZIP_DEFLATED archive's raw bytes, containing one description.xml
        member built by build_description_xml.
    """
    description_content = build_description_xml(
        name=name,
        manufacturer=manufacturer,
        weight=weight,
        models_xml=models_xml,
        geometries_xml=geometries_xml,
        attributes_xml=attributes_xml,
    ).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("description.xml", description_content)
    return buffer.getvalue()


_fixture_uuid_counter = itertools.count(1)


def _deterministic_uuid() -> str:
    """Return a deterministic, valid-looking UUID string for test MVR nodes."""
    return f"00000000-0000-4000-8000-{next(_fixture_uuid_counter):012d}"


def fixture_xml(name: str, gdtf_spec: Optional[str], *, child_list_xml: str = "") -> str:
    """Build a raw <Fixture> element for embedding in test MVR scene XML.

    Parameters:
        name: The Fixture's name attribute.
        gdtf_spec: Text for a <GDTFSpec> child element, or None to omit it
            entirely (a fixture with no GDTF reference).
        child_list_xml: Raw XML for a nested <ChildList>, included only when
            non-empty (for a fixture that itself contains nested fixtures).

    Returns:
        A <Fixture name=... uuid=...> element as a raw XML string.
    """
    name_attr = quoteattr(name)
    uuid_attr = quoteattr(_deterministic_uuid())

    gdtf_spec_xml = ""
    if gdtf_spec is not None:
        gdtf_spec_xml = f"<GDTFSpec>{escape(gdtf_spec)}</GDTFSpec>"

    child_list = f"<ChildList>{child_list_xml}</ChildList>" if child_list_xml else ""

    return f"<Fixture name={name_attr} uuid={uuid_attr}>{gdtf_spec_xml}{child_list}</Fixture>"


def group_xml(name: str, children_xml: str) -> str:
    """Build a raw <GroupObject> element wrapping a <ChildList>, for test MVR scene XML.

    Parameters:
        name: The GroupObject's name attribute.
        children_xml: Raw XML placed inside the GroupObject's <ChildList>.

    Returns:
        A <GroupObject name=... uuid=...><ChildList>...</ChildList></GroupObject>
        element as a raw XML string, using fixture_xml's deterministic uuid
        counter.
    """
    name_attr = quoteattr(name)
    uuid_attr = quoteattr(_deterministic_uuid())
    return f"<GroupObject name={name_attr} uuid={uuid_attr}><ChildList>{children_xml}</ChildList></GroupObject>"


def child_node_xml(tag: str, name: str, children_xml: str) -> str:
    """Build a raw SceneObject/Truss/Support/VideoScreen/Projector element.

    Parameters:
        tag: The element tag name (one of "SceneObject", "Truss", "Support",
            "VideoScreen" or "Projector" -- every node type besides
            GroupObject that carries its own <ChildList>, RESEARCH Pattern 2).
        name: The node's name attribute.
        children_xml: Raw XML placed inside the node's <ChildList>.

    Returns:
        A <{tag} name=... uuid=...><ChildList>...</ChildList></{tag}> element
        as a raw XML string, using fixture_xml's deterministic uuid counter.
    """
    name_attr = quoteattr(name)
    uuid_attr = quoteattr(_deterministic_uuid())
    return f"<{tag} name={name_attr} uuid={uuid_attr}><ChildList>{children_xml}</ChildList></{tag}>"


def build_scene_xml(layers_xml: str) -> str:
    """Build a full GeneralSceneDescription.xml document around raw layers XML.

    Parameters:
        layers_xml: Raw XML inserted verbatim inside <Layers>.

    Returns:
        A UTF-8 XML document string representing a minimal, valid MVR scene.
    """
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<GeneralSceneDescription verMajor="1" verMinor="6" provider="tests" providerVersion="1">'
        f"<Scene><Layers>{layers_xml}</Layers></Scene>"
        "</GeneralSceneDescription>\n"
    )


@pytest.fixture
def make_mvr(tmp_path):
    """Factory fixture that writes .mvr (zip) archives for tests.

    Returns:
        A callable ``_make(filename, **kwargs) -> Path`` that writes
        ``tmp_path/filename`` as a ZIP_DEFLATED archive containing a
        GeneralSceneDescription.xml member (or the caller's override) plus
        any extra members, and returns the written path.
    """

    def _make(
        filename: str,
        *,
        fixtures: Sequence[Tuple[str, Optional[str]]] = (),
        layers_xml: Optional[str] = None,
        gdtf_members: Optional[Mapping[str, bytes]] = None,
        scene_xml: Optional[Union[str, bytes]] = None,
        include_scene: bool = True,
        extra_members: Optional[Mapping[str, bytes]] = None,
    ) -> Path:
        """Write a .mvr archive and return its path.

        Parameters:
            filename: Name of the archive to create under tmp_path.
            fixtures: (name, gdtf_spec) pairs placed directly in one
                `<Layer name="Layer 1" uuid=...><ChildList>...</ChildList></Layer>`.
                Ignored when layers_xml or scene_xml is given.
            layers_xml: Raw <Layers> inner XML, replacing the single-layer
                default built from fixtures -- for nested-GroupObject cases.
                Ignored when scene_xml is given.
            gdtf_members: Embedded GDTF zip members (member name -> bytes),
                typically from build_gdtf_bytes.
            scene_xml: Explicit GeneralSceneDescription.xml content (str or
                bytes). When provided, overrides the generated document
                entirely (and fixtures/layers_xml are ignored).
            include_scene: When False, no GeneralSceneDescription.xml member
                is written at all (used to test missing-file error paths).
            extra_members: Additional zip members (name -> bytes) to write.

        Returns:
            Path to the written .mvr archive.
        """
        archive_path = tmp_path / filename

        if scene_xml is not None:
            scene_content = scene_xml.encode("utf-8") if isinstance(scene_xml, str) else scene_xml
        else:
            if layers_xml is not None:
                resolved_layers_xml = layers_xml
            else:
                layer_uuid = quoteattr(_deterministic_uuid())
                child_list = "".join(fixture_xml(name, spec) for name, spec in fixtures)
                resolved_layers_xml = f'<Layer name="Layer 1" uuid={layer_uuid}><ChildList>{child_list}</ChildList></Layer>'
            scene_content = build_scene_xml(resolved_layers_xml).encode("utf-8")

        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if include_scene:
                zf.writestr("GeneralSceneDescription.xml", scene_content)
            for member_name, member_bytes in (gdtf_members or {}).items():
                zf.writestr(member_name, member_bytes)
            for member_name, member_bytes in (extra_members or {}).items():
                zf.writestr(member_name, member_bytes)

        return archive_path

    return _make


@pytest.fixture(autouse=True)
def _isolate_profile_storage(tmp_path, monkeypatch):
    """Redirect the default compare-profiles folder into tmp_path.

    No test may read or write the real per-user profiles folder: this
    autouse fixture monkeypatches gdtf_comparer.core.profile_repository's
    _default_profiles_dir() to return a path inside tmp_path, for every test
    in the suite, whether or not it touches profiles directly. It must not
    create the folder itself, since tests/core/test_repository.py::
    test_load_writes_nothing_to_disk compares tmp_path directory listings
    before and after an unrelated FixtureRepository.load() call.
    """
    import gdtf_comparer.core.profile_repository as profile_repository_module

    monkeypatch.setattr(
        profile_repository_module,
        "_default_profiles_dir",
        lambda: str(tmp_path / "gdtf-comparer-app-data"),
    )
