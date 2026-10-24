"""Unit tests for core.mvr_repository: dedup, nesting, order, accented names,
missing/broken/oversized embedded GDTFs, and summary wording (PARSE-02, SUB-01).

Every MVR is built in memory via the make_mvr/build_gdtf_bytes/fixture_xml/
group_xml/child_node_xml fixtures -- nothing here touches a real show file.
"""

import io
import os
import zipfile

from gdtf_comparer.core import hardening
from gdtf_comparer.core.mvr_repository import (
    MISSING_EMBEDDED_GDTF_REASON,
    NONE_IMPORTED_TEMPLATE,
    SkippedFixtureType,
    import_mvr,
    import_summary_message,
    readable_gdtf_spec,
)

from tests.conftest import build_description_xml, build_gdtf_bytes, child_node_xml, fixture_xml, group_xml


def test_dedup_by_gdtf_spec(make_mvr):
    spot_bytes = build_gdtf_bytes(name="Acme Spot", manufacturer="Acme")
    wash_bytes = build_gdtf_bytes(name="Beta Wash", manufacturer="Beta")
    path = make_mvr(
        "dedup.mvr",
        fixtures=[
            ("Spot 1", "Acme@Spot.gdtf"),
            ("Spot 2", "Acme@Spot.gdtf"),
            ("Wash 1", "Beta@Wash.gdtf"),
        ],
        gdtf_members={"Acme@Spot.gdtf": spot_bytes, "Beta@Wash.gdtf": wash_bytes},
    )

    result = import_mvr(str(path))

    assert [(entry.gdtf_spec, entry.instance_count) for entry in result.fixture_types] == [
        ("Acme@Spot.gdtf", 2),
        ("Beta@Wash.gdtf", 1),
    ]
    assert result.fixture_types[0].fixture.name == "Acme Spot"
    assert result.fixture_types[1].fixture.name == "Beta Wash"


def test_same_name_different_files_stay_separate(make_mvr):
    a_bytes = build_gdtf_bytes(name="Spot", manufacturer="Acme")
    b_bytes = build_gdtf_bytes(name="Spot", manufacturer="Acme")
    path = make_mvr(
        "separate.mvr",
        fixtures=[("F1", "A@Spot.gdtf"), ("F2", "B@Spot.gdtf")],
        gdtf_members={"A@Spot.gdtf": a_bytes, "B@Spot.gdtf": b_bytes},
    )

    result = import_mvr(str(path))

    assert [entry.gdtf_spec for entry in result.fixture_types] == ["A@Spot.gdtf", "B@Spot.gdtf"]


def test_gdtf_mode_ignored(make_mvr):
    spot_bytes = build_gdtf_bytes(name="Acme Spot", manufacturer="Acme")
    fixture_a = (
        '<Fixture name="F1" uuid="00000000-0000-4000-8000-100000000001">'
        "<GDTFSpec>Acme@Spot.gdtf</GDTFSpec><GDTFMode>Mode A</GDTFMode>"
        "</Fixture>"
    )
    fixture_b = (
        '<Fixture name="F2" uuid="00000000-0000-4000-8000-100000000002">'
        "<GDTFSpec>Acme@Spot.gdtf</GDTFSpec><GDTFMode>Mode B</GDTFMode>"
        "</Fixture>"
    )
    layers_xml = (
        '<Layer name="Layer 1" uuid="00000000-0000-4000-8000-100000000000">'
        f"<ChildList>{fixture_a}{fixture_b}</ChildList></Layer>"
    )
    path = make_mvr("mode.mvr", layers_xml=layers_xml, gdtf_members={"Acme@Spot.gdtf": spot_bytes})

    result = import_mvr(str(path))

    assert len(result.fixture_types) == 1
    assert result.fixture_types[0].instance_count == 2


def test_fixtures_found_everywhere_in_walk_order(make_mvr):
    gdtf_members = {f"S{i}.gdtf": build_gdtf_bytes(name=f"Fixture {i}") for i in range(1, 10)}

    f1a = fixture_xml("F1a", "S2.gdtf")
    f1 = fixture_xml("F1", "S1.gdtf", child_list_xml=f1a)

    g2 = fixture_xml("G2", "S3.gdtf")
    inner_group = group_xml("Inner Group", g2)
    outer_group = group_xml("Outer Group", inner_group)

    scene_object = child_node_xml("SceneObject", "Scene1", fixture_xml("SceneFix", "S4.gdtf"))
    truss = child_node_xml("Truss", "Truss1", fixture_xml("TrussFix", "S5.gdtf"))
    support = child_node_xml("Support", "Support1", fixture_xml("SupportFix", "S6.gdtf"))
    video_screen = child_node_xml("VideoScreen", "Video1", fixture_xml("VideoFix", "S7.gdtf"))
    projector = child_node_xml("Projector", "Proj1", fixture_xml("ProjFix", "S8.gdtf"))

    layer1_children = f1 + outer_group + scene_object + truss + support + video_screen + projector
    layer1 = (
        '<Layer name="Layer 1" uuid="00000000-0000-4000-8000-900000000001">'
        f"<ChildList>{layer1_children}</ChildList></Layer>"
    )

    layer2_children = fixture_xml("F9", "S9.gdtf") + fixture_xml("F1-repeat", "S1.gdtf")
    layer2 = (
        '<Layer name="Layer 2" uuid="00000000-0000-4000-8000-900000000002">'
        f"<ChildList>{layer2_children}</ChildList></Layer>"
    )

    path = make_mvr("walk.mvr", layers_xml=layer1 + layer2, gdtf_members=gdtf_members)

    result = import_mvr(str(path))

    assert [entry.gdtf_spec for entry in result.fixture_types] == [f"S{i}.gdtf" for i in range(1, 10)]
    counts = {entry.gdtf_spec: entry.instance_count for entry in result.fixture_types}
    assert counts["S1.gdtf"] == 2
    for i in range(2, 10):
        assert counts[f"S{i}.gdtf"] == 1


def test_accented_gdtf_name_is_found(make_mvr):
    spec = "Lumière@Spot.gdtf"
    gdtf_bytes = build_gdtf_bytes(name="Lumiere Spot", manufacturer="Acme")
    path = make_mvr("accented.mvr", fixtures=[("Spot 1", spec)], gdtf_members={spec: gdtf_bytes})

    result = import_mvr(str(path))

    assert len(result.fixture_types) == 1
    assert result.fixture_types[0].gdtf_spec == spec

    mangled = spec.encode("utf-8").decode("cp437")
    assert readable_gdtf_spec(mangled) == spec
    assert readable_gdtf_spec("Acme@Spot.gdtf") == "Acme@Spot.gdtf"


def test_missing_embedded_gdtf_is_skipped_and_named(make_mvr):
    spot_bytes = build_gdtf_bytes(name="Acme Spot", manufacturer="Acme")
    path = make_mvr(
        "missing.mvr",
        fixtures=[("Spot 1", "Acme@Spot.gdtf"), ("Wash 1", "Ghost@Wash.gdtf")],
        gdtf_members={"Acme@Spot.gdtf": spot_bytes},
    )

    result = import_mvr(str(path))

    assert len(result.fixture_types) == 1
    assert result.skipped == (SkippedFixtureType("Ghost@Wash.gdtf", 1, MISSING_EMBEDDED_GDTF_REASON),)

    summary = import_summary_message(result)
    assert "Ghost@Wash.gdtf" in summary
    assert "not included in this MVR" in summary


def test_broken_embedded_gdtf_is_skipped_with_reason(make_mvr):
    good_bytes = build_gdtf_bytes(name="Good Fixture")
    path = make_mvr(
        "broken.mvr",
        fixtures=[("Good", "Good.gdtf"), ("Broken", "Broken.gdtf")],
        gdtf_members={"Good.gdtf": good_bytes, "Broken.gdtf": b"not a zip"},
    )

    result = import_mvr(str(path))

    assert len(result.fixture_types) == 1
    assert len(result.skipped) == 1
    assert result.skipped[0].gdtf_spec == "Broken.gdtf"
    assert "not a valid GDTF file" in result.skipped[0].reason


def _oversized_gdtf_bytes() -> bytes:
    """Build an in-memory GDTF zip whose own archive bytes exceed 2048 bytes.

    Uses ZIP_STORED (no compression) with an incompressible padding member,
    so the result is reliably large regardless of DEFLATE's handling of
    repetitive text -- unlike padding build_gdtf_bytes's XML text, which
    compresses away to almost nothing.
    """
    description = build_description_xml(
        name="Big Fixture", manufacturer="Test Co", weight=10.0, models_xml="", geometries_xml=""
    ).encode("utf-8")
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_STORED) as zf:
        zf.writestr("description.xml", description)
        zf.writestr("padding.bin", os.urandom(4096))
    return buffer.getvalue()


def test_oversized_embedded_gdtf_is_skipped(make_mvr, monkeypatch):
    monkeypatch.setattr(hardening, "MAX_GDTF_FILE_BYTES", 2048)
    small_bytes = build_gdtf_bytes(name="Small Fixture")
    big_bytes = _oversized_gdtf_bytes()
    path = make_mvr(
        "oversized.mvr",
        fixtures=[("Small", "Small.gdtf"), ("Big", "Big.gdtf")],
        gdtf_members={"Small.gdtf": small_bytes, "Big.gdtf": big_bytes},
    )

    result = import_mvr(str(path))

    assert len(result.fixture_types) == 1
    assert result.fixture_types[0].gdtf_spec == "Small.gdtf"
    assert len(result.skipped) == 1
    assert result.skipped[0].gdtf_spec == "Big.gdtf"
    assert "safety reasons" in result.skipped[0].reason


def test_fixture_without_gdtf_spec_is_counted(make_mvr):
    path = make_mvr("practical.mvr", fixtures=[("Practical", None)])

    result = import_mvr(str(path))

    assert result.unreferenced_fixture_count == 1
    assert result.fixture_types == ()

    summary = import_summary_message(result)
    assert "1 fixture in the show names no GDTF file" in summary


def test_empty_scene(make_mvr):
    path = make_mvr("empty.mvr")

    result = import_mvr(str(path))

    assert result.fixture_types == ()
    assert result.skipped == ()
    assert import_summary_message(result) == "'empty.mvr' doesn't contain any fixtures."


def test_all_types_fail(make_mvr):
    path = make_mvr(
        "allfail.mvr",
        fixtures=[("Spot 1", "Missing@Spot.gdtf"), ("Wash 1", "Missing@Wash.gdtf")],
    )

    result = import_mvr(str(path))

    assert result.fixture_types == ()
    summary = import_summary_message(result)
    assert summary.startswith(NONE_IMPORTED_TEMPLATE.format(file="allfail.mvr"))


def test_found_summary_wording(make_mvr):
    spot_bytes = build_gdtf_bytes(name="Spot A")
    wash_bytes = build_gdtf_bytes(name="Wash A")
    path = make_mvr(
        "show.mvr",
        fixtures=[("F1", "A@Spot.gdtf"), ("F2", "A@Spot.gdtf"), ("F3", "B@Wash.gdtf")],
        gdtf_members={"A@Spot.gdtf": spot_bytes, "B@Wash.gdtf": wash_bytes},
    )
    result = import_mvr(str(path))
    assert import_summary_message(result).startswith("Found 2 fixture types in 'show.mvr' (3 fixtures).")

    path_one = make_mvr(
        "one.mvr", fixtures=[("F1", "A@Spot.gdtf")], gdtf_members={"A@Spot.gdtf": spot_bytes}
    )
    result_one = import_mvr(str(path_one))
    assert import_summary_message(result_one).startswith("Found 1 fixture type in 'one.mvr' (1 fixture).")


def test_import_never_writes_or_modifies(make_mvr, tmp_path):
    spot_bytes = build_gdtf_bytes(name="Spot A")
    path = make_mvr(
        "untouched.mvr", fixtures=[("F1", "A@Spot.gdtf")], gdtf_members={"A@Spot.gdtf": spot_bytes}
    )
    before_bytes = path.read_bytes()
    before_listing = sorted(p.name for p in tmp_path.iterdir())

    import_mvr(str(path))

    assert path.read_bytes() == before_bytes
    assert sorted(p.name for p in tmp_path.iterdir()) == before_listing
