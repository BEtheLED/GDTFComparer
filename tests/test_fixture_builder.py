"""Toolchain + fixture-builder round-trip guard.

Confirms the pinned toolchain is installed at the expected versions, that
the make_gdtf fixture writes .gdtf archives pygdtf can parse back, and that
the offscreen Qt platform is active for headless test runs.
"""

import importlib.metadata
import sys


def test_toolchain_versions():
    assert importlib.metadata.version("PySide6") == "6.11.2"
    assert importlib.metadata.version("pygdtf") == "1.4.5"
    assert importlib.metadata.version("defusedxml") == "0.7.1"
    assert importlib.metadata.version("qt-material") == "2.17"
    assert importlib.metadata.version("pytest-qt") == "4.5.0"
    assert sys.version_info >= (3, 11)


def test_builder_roundtrips_through_pygdtf(make_gdtf):
    import pygdtf

    models_xml = '<Model Name="Body" Length="0.3" Width="0.2" Height="0.25"/>'
    geometries_xml = (
        '<Geometry Name="Body" Model="Body">'
        '<Beam Name="Beam" BeamAngle="20"/>'
        "</Geometry>"
    )

    path = make_gdtf(
        "builder_check.gdtf",
        name="Builder Check",
        manufacturer="Acme",
        weight=12.5,
        models_xml=models_xml,
        geometries_xml=geometries_xml,
    )

    with pygdtf.FixtureType(str(path)) as fixture:
        assert fixture.name == "Builder Check"
        assert fixture.manufacturer == "Acme"
        assert fixture.properties.weight == 12.5
        assert len(fixture.models) == 1
        assert fixture.models[0].name == "Body"
        assert fixture.models[0].width == 0.2
        assert fixture.geometries[0].geometries[0].beam_angle == 20.0


def test_qt_offscreen_platform(qapp):
    assert qapp.platformName() == "offscreen"
