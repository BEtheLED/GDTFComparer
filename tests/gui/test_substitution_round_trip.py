"""End-to-end MVR import -> fixture substitution round trip (PARSE-02, SUB-01..04).

An LD imports an MVR, picks its one fixture type, marks one attribute with a
direction and a tolerance, and saves a requirements file. A second, fresh
window opens that file, points at a folder of three candidate GDTFs, and
sees them ranked with one green, one yellow and one red light (D-07, D-08,
D-09, D-10, D-11).
"""

import json

from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush

from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.requirements_repository import REQUIREMENTS_FORMAT_ID
from gdtf_comparer.core.substitution import TOLERANCE_KIND, Direction, MatchState
from gdtf_comparer.gui.candidate_results import COL_FIXTURE, FIRST_REQUIREMENT_COLUMN, MATCH_STATE_ROLE
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.requirements_editor import VALUE_ROLE
from gdtf_comparer.gui.substitution_window import SubstitutionWindow
from gdtf_comparer.gui.table_model import BackgroundBrushDelegate

from tests.conftest import build_gdtf_bytes, fixture_xml

_LD_GEOMETRIES = '<Geometry Name="Head"><Beam Name="Beam" BeamAngle="20" FieldAngle="25"/></Geometry>'
WEIGHT_KEY = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")

# Task 2 decision: option a (absolute units, outer-limit rule). 2.0 puts
# 16.5 kg in yellow and 20 kg in red against a 15 kg, lower-is-better target.
TOLERANCE = 2.0

_LAYER_UUID = "11111111-1111-4111-8111-111111111111"
_GROUP_UUID = "22222222-2222-4222-8222-222222222222"


def _ld_mvr(make_mvr):
    """Write an MVR with two Acme Spot instances (one direct, one grouped)."""
    ld_bytes = build_gdtf_bytes(
        name="Acme Spot", manufacturer="Acme", weight=15.0, geometries_xml=_LD_GEOMETRIES
    )
    direct_fixture = fixture_xml("Spot 1", "Acme@Spot.gdtf")
    grouped_fixture = fixture_xml("Spot 2", "Acme@Spot.gdtf")
    group_xml = (
        f'<GroupObject name="Truss Group" uuid="{_GROUP_UUID}">'
        f"<ChildList>{grouped_fixture}</ChildList>"
        "</GroupObject>"
    )
    layers_xml = (
        f'<Layer name="Layer 1" uuid="{_LAYER_UUID}">'
        f"<ChildList>{direct_fixture}{group_xml}</ChildList>"
        "</Layer>"
    )
    return make_mvr("ld.mvr", layers_xml=layers_xml, gdtf_members={"Acme@Spot.gdtf": ld_bytes})


def _inventory(tmp_path, make_gdtf):
    """Write three candidate GDTFs (one green, one yellow, one red against WEIGHT_KEY)."""
    folder = tmp_path / "inventory"
    folder.mkdir()
    make_gdtf(
        "inventory/Beta Spot.gdtf", name="Beta Spot", manufacturer="Beta", weight=14.0,
        geometries_xml=_LD_GEOMETRIES,
    )
    make_gdtf(
        "inventory/Gamma Spot.gdtf", name="Gamma Spot", manufacturer="Gamma", weight=16.5,
        geometries_xml=_LD_GEOMETRIES,
    )
    make_gdtf(
        "inventory/Delta Spot.gdtf", name="Delta Spot", manufacturer="Delta", weight=20.0,
        geometries_xml=_LD_GEOMETRIES,
    )
    return folder


def test_find_substitutes_button_opens_one_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    qtbot.mouseClick(window.substitutes_button, Qt.MouseButton.LeftButton)
    first = window.substitution_window
    assert isinstance(first, SubstitutionWindow)
    assert first.isVisible()

    qtbot.mouseClick(window.substitutes_button, Qt.MouseButton.LeftButton)
    assert window.substitution_window is first


def test_ld_to_shop_round_trip(qtbot, tmp_path, make_mvr, make_gdtf, monkeypatch):
    mvr_path = _ld_mvr(make_mvr)
    mvr_bytes_before = mvr_path.read_bytes()
    inventory_folder = _inventory(tmp_path, make_gdtf)

    ld = SubstitutionWindow()
    qtbot.addWidget(ld)
    monkeypatch.setattr(ld, "_ask_open_mvr_path", lambda: str(mvr_path))

    qtbot.mouseClick(ld.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: ld.import_mvr_button.isEnabled() and ld.fixture_list.count() == 1, timeout=10000
    )

    item = ld.fixture_list.item(0)
    assert item.text() == "Acme Spot — Acme (2 in this show)"
    assert item.data(Qt.ItemDataRole.UserRole) == "Acme@Spot.gdtf"

    leaf = ld.requirements_editor.leaf_item(WEIGHT_KEY)
    assert leaf is not None
    assert leaf.data(0, VALUE_ROLE) == 15.0

    leaf.setCheckState(0, Qt.CheckState.Checked)

    combo = ld.requirements_editor.direction_combo(WEIGHT_KEY)
    assert combo is not None
    combo.setCurrentIndex(combo.findData(Direction.LOWER.value))
    spin = ld.requirements_editor.tolerance_spin(WEIGHT_KEY)
    assert spin is not None
    spin.setValue(TOLERANCE)

    saved_path = tmp_path / "reqs.json"
    recorded = []

    def _record_save(suggested):
        recorded.append(suggested)
        return str(saved_path)

    monkeypatch.setattr(ld, "_ask_save_requirements_path", _record_save)
    qtbot.mouseClick(ld.save_requirements_button, Qt.MouseButton.LeftButton)

    assert recorded == ["Acme Spot requirements.json"]
    assert saved_path.exists()

    payload = json.loads(saved_path.read_text())
    assert set(payload.keys()) == {"format", "version", "tolerance_kind", "fixture", "requirements"}
    assert payload["format"] == REQUIREMENTS_FORMAT_ID
    assert payload["version"] == 1
    assert payload["tolerance_kind"] == TOLERANCE_KIND
    assert payload["fixture"] == {"name": "Acme Spot", "manufacturer": "Acme", "gdtf_file": "Acme@Spot.gdtf"}
    assert payload["requirements"] == [
        {
            "category": CATEGORY_PHYSICAL,
            "element": "",
            "attribute": "Weight",
            "target": 15.0,
            "direction": "lower",
            "tolerance": TOLERANCE,
        }
    ]

    assert mvr_path.read_bytes() == mvr_bytes_before

    shop = SubstitutionWindow()
    qtbot.addWidget(shop)
    monkeypatch.setattr(shop, "_ask_open_requirements_path", lambda: str(saved_path))
    qtbot.mouseClick(shop.open_requirements_button, Qt.MouseButton.LeftButton)
    assert "Acme Spot" in shop.requirements_summary_label.text()

    monkeypatch.setattr(shop, "_ask_inventory_folder", lambda: str(inventory_folder))
    qtbot.mouseClick(shop.choose_folder_button, Qt.MouseButton.LeftButton)
    qtbot.mouseClick(shop.check_inventory_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: shop.check_inventory_button.isEnabled() and shop.results_model.rowCount() == 3,
        timeout=10000,
    )

    model = shop.results_model
    fixture_texts = [model.index(row, COL_FIXTURE).data() for row in range(3)]
    assert fixture_texts[0].startswith("Beta Spot")
    assert fixture_texts[1].startswith("Gamma Spot")
    assert fixture_texts[2].startswith("Delta Spot")

    expected_states = [MatchState.GREEN, MatchState.YELLOW, MatchState.RED]
    for row, expected_state in enumerate(expected_states):
        index = model.index(row, FIRST_REQUIREMENT_COLUMN)
        assert index.data(MATCH_STATE_ROLE) == expected_state
        assert isinstance(index.data(Qt.ItemDataRole.BackgroundRole), QBrush)

    assert isinstance(shop.results_view.itemDelegate(), BackgroundBrushDelegate)


def test_check_inventory_with_these_sends_current_requirements(qtbot, make_mvr, monkeypatch):
    mvr_path = _ld_mvr(make_mvr)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(mvr_path))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 1,
        timeout=10000,
    )

    leaf = window.requirements_editor.leaf_item(WEIGHT_KEY)
    assert leaf is not None
    leaf.setCheckState(0, Qt.CheckState.Checked)

    qtbot.mouseClick(window.use_for_inventory_button, Qt.MouseButton.LeftButton)

    assert window.tabs.currentWidget() is window.check_inventory_tab
    assert "Acme Spot" in window.requirements_summary_label.text()
    assert "Weight" in window.requirements_summary_label.text()
