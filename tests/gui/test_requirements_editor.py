"""Requirements editor: per-type memory, defaults, units, search (SUB-02, D-04..D-06).

Widens the single-attribute tracer proven in test_substitution_round_trip.py
to the editor's full working surface: each fixture type keeps its own
independent checklist (D-04), a sensible overridable direction/tolerance per
attribute (D-05, D-06), honest text-attribute handling, declared-only rows,
and a search box that only narrows visibility.
"""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_PHYSICAL, CATEGORY_BEAM, AttributeKey
from gdtf_comparer.core.substitution import Direction
from gdtf_comparer.gui.requirements_editor import VALUE_ROLE
from gdtf_comparer.gui.substitution_window import SubstitutionWindow

from tests.conftest import build_gdtf_bytes

# Shared test data (05-03-PLAN.md).
_GEOMETRIES = (
    '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="20" FieldAngle="25" '
    'PowerConsumption="450" LuminousFlux="18000" ColorTemperature="6500" BeamType="Spot"/></Geometry>'
)
_PAN_XML = '<Attribute Name="Pan" Pretty="P" ActivationGroup="PanTilt" Feature="Position.PanTilt" PhysicalUnit="Angle"/>'

WEIGHT_KEY = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")
BEAM_ANGLE_KEY = AttributeKey(CATEGORY_BEAM, "Beam 1", "BeamAngle")
PAN_PRETTY_KEY = AttributeKey("DMX: Position", "Pretty", "Pan")


def _two_type_mvr(make_mvr):
    """Write an MVR with two distinct fixture types: Acme Spot and Beta Wash."""
    acme_bytes = build_gdtf_bytes(
        name="Acme Spot", manufacturer="Acme", weight=15.0,
        geometries_xml=_GEOMETRIES, attributes_xml=_PAN_XML,
    )
    beta_bytes = build_gdtf_bytes(
        name="Beta Wash", manufacturer="Beta", weight=9.0,
        geometries_xml='<Geometry Name="Head"><Beam Name="Beam" BeamAngle="40"/></Geometry>',
    )
    return make_mvr(
        "show.mvr",
        fixtures=[("A1", "Acme@Spot.gdtf"), ("B1", "Beta@Wash.gdtf")],
        gdtf_members={"Acme@Spot.gdtf": acme_bytes, "Beta@Wash.gdtf": beta_bytes},
    )


def _open_mvr(qtbot, window, mvr_path, monkeypatch, expected_count=2):
    """Import mvr_path into window and wait for the fixture list to populate."""
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(mvr_path))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == expected_count,
        timeout=10000,
    )


def test_each_fixture_type_keeps_its_own_requirements(qtbot, make_mvr, monkeypatch):
    mvr_path = _two_type_mvr(make_mvr)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    _open_mvr(qtbot, window, mvr_path, monkeypatch)

    assert window.fixture_list.item(0).data(Qt.ItemDataRole.UserRole) == "Acme@Spot.gdtf"
    assert window.fixture_list.item(1).data(Qt.ItemDataRole.UserRole) == "Beta@Wash.gdtf"

    editor = window.requirements_editor

    # Row 0 (Acme Spot): tick Weight and set its tolerance to 3.
    weight_leaf = editor.leaf_item(WEIGHT_KEY)
    assert weight_leaf is not None
    weight_leaf.setCheckState(0, Qt.CheckState.Checked)
    editor.tolerance_spin(WEIGHT_KEY).setValue(3.0)

    # Row 1 (Beta Wash): Weight is unticked (its own, never-before-shown
    # checklist); tick BeamAngle.
    window.fixture_list.setCurrentRow(1)
    assert editor.leaf_item(WEIGHT_KEY).checkState(0) == Qt.CheckState.Unchecked
    beam_leaf = editor.leaf_item(BEAM_ANGLE_KEY)
    assert beam_leaf is not None
    beam_leaf.setCheckState(0, Qt.CheckState.Checked)

    beta_set = editor.requirement_set()
    assert [requirement.key.attribute for requirement in beta_set.requirements] == ["BeamAngle"]
    assert beta_set.gdtf_file == "Beta@Wash.gdtf"

    # Back to row 0: Weight is ticked, tolerance 3.0, BeamAngle unticked
    # (Acme Spot also declares BeamAngle -- the leaf exists, just unchecked).
    window.fixture_list.setCurrentRow(0)
    weight_leaf = editor.leaf_item(WEIGHT_KEY)
    assert weight_leaf.checkState(0) == Qt.CheckState.Checked
    assert editor.tolerance_spin(WEIGHT_KEY).value() == 3.0
    assert editor.leaf_item(BEAM_ANGLE_KEY).checkState(0) == Qt.CheckState.Unchecked

    acme_set = editor.requirement_set()
    assert [requirement.key.attribute for requirement in acme_set.requirements] == ["Weight"]
    assert acme_set.requirements[0].tolerance == 3.0
    assert acme_set.gdtf_file == "Acme@Spot.gdtf"


def test_requirements_follow_attribute_panel_order(qtbot, make_mvr, monkeypatch):
    mvr_path = _two_type_mvr(make_mvr)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    _open_mvr(qtbot, window, mvr_path, monkeypatch)

    editor = window.requirements_editor
    assert window.fixture_list.currentRow() == 0  # Acme Spot

    # Tick in a deliberately scrambled order: Weight, then Pan (Pretty), then BeamAngle.
    editor.leaf_item(WEIGHT_KEY).setCheckState(0, Qt.CheckState.Checked)
    editor.leaf_item(PAN_PRETTY_KEY).setCheckState(0, Qt.CheckState.Checked)
    editor.leaf_item(BEAM_ANGLE_KEY).setCheckState(0, Qt.CheckState.Checked)

    requirement_set = editor.requirement_set()
    keys = [requirement.key for requirement in requirement_set.requirements]
    assert keys == [BEAM_ANGLE_KEY, WEIGHT_KEY, PAN_PRETTY_KEY]


def test_new_import_forgets_previous_show(qtbot, make_mvr, monkeypatch):
    mvr_path = _two_type_mvr(make_mvr)
    second_mvr_path = make_mvr(
        "second.mvr",
        fixtures=[("A2", "Acme@Spot.gdtf")],
        gdtf_members={
            "Acme@Spot.gdtf": build_gdtf_bytes(
                name="Acme Spot", manufacturer="Acme", weight=15.0,
                geometries_xml=_GEOMETRIES, attributes_xml=_PAN_XML,
            )
        },
    )

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    _open_mvr(qtbot, window, mvr_path, monkeypatch)

    editor = window.requirements_editor
    editor.leaf_item(WEIGHT_KEY).setCheckState(0, Qt.CheckState.Checked)

    _open_mvr(qtbot, window, second_mvr_path, monkeypatch, expected_count=1)

    weight_leaf = editor.leaf_item(WEIGHT_KEY)
    assert weight_leaf is not None
    assert weight_leaf.checkState(0) == Qt.CheckState.Unchecked


def test_remembered_direction_survives_switching(qtbot, make_mvr, monkeypatch):
    mvr_path = _two_type_mvr(make_mvr)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    _open_mvr(qtbot, window, mvr_path, monkeypatch)

    editor = window.requirements_editor
    weight_leaf = editor.leaf_item(WEIGHT_KEY)
    assert weight_leaf.data(0, VALUE_ROLE) == 15.0
    weight_leaf.setCheckState(0, Qt.CheckState.Checked)

    combo = editor.direction_combo(WEIGHT_KEY)
    combo.setCurrentIndex(combo.findData(Direction.HIGHER.value))

    window.fixture_list.setCurrentRow(1)
    window.fixture_list.setCurrentRow(0)

    assert editor.direction_combo(WEIGHT_KEY).currentData() == Direction.HIGHER.value
