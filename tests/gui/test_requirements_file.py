"""GUI tests for the requirements file: fresh-window open, and a refused
open/save leaving previous state untouched (SUB-03, D-07).
"""

from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.requirements_repository import load_requirements
from gdtf_comparer.core.substitution import describe_requirements
from gdtf_comparer.gui.substitution_window import SubstitutionWindow

from tests.conftest import build_gdtf_bytes, fixture_xml

WEIGHT_KEY = AttributeKey(CATEGORY_PHYSICAL, "", "Weight")


def _ld_mvr(make_mvr):
    """Write a minimal MVR with one "Acme Spot" fixture instance."""
    ld_bytes = build_gdtf_bytes(name="Acme Spot", manufacturer="Acme", weight=15.0)
    direct_fixture = fixture_xml("Spot 1", "Acme@Spot.gdtf")
    layers_xml = f'<Layer name="Layer 1"><ChildList>{direct_fixture}</ChildList></Layer>'
    return make_mvr("ld.mvr", layers_xml=layers_xml, gdtf_members={"Acme@Spot.gdtf": ld_bytes})


def test_saved_file_opens_in_a_fresh_window(qtbot, tmp_path, make_mvr, monkeypatch):
    mvr_path = _ld_mvr(make_mvr)

    ld = SubstitutionWindow()
    qtbot.addWidget(ld)
    monkeypatch.setattr(ld, "_ask_open_mvr_path", lambda: str(mvr_path))
    qtbot.mouseClick(ld.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: ld.import_mvr_button.isEnabled() and ld.fixture_list.count() == 1, timeout=10000
    )

    leaf = ld.requirements_editor.leaf_item(WEIGHT_KEY)
    assert leaf is not None
    leaf.setCheckState(0, Qt.CheckState.Checked)

    saved_path = tmp_path / "saved.json"
    recorded = []

    def _record_save(suggested):
        recorded.append(suggested)
        return str(saved_path)

    monkeypatch.setattr(ld, "_ask_save_requirements_path", _record_save)
    qtbot.mouseClick(ld.save_requirements_button, Qt.MouseButton.LeftButton)

    assert recorded == ["Acme Spot requirements.json"]
    assert saved_path.exists()

    fresh = SubstitutionWindow()
    qtbot.addWidget(fresh)
    monkeypatch.setattr(fresh, "_ask_open_requirements_path", lambda: str(saved_path))
    qtbot.mouseClick(fresh.open_requirements_button, Qt.MouseButton.LeftButton)

    assert fresh.requirements_summary_label.text() == describe_requirements(
        load_requirements(str(saved_path))
    )
