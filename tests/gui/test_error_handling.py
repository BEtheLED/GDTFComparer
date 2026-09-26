"""GUI error-handling tests: friendly dialogs, no partial tables, recovery (RELI-01).

Dialogs are captured by monkeypatching QMessageBox.exec so no modal actually
blocks the test; text/textFormat are read directly off the QMessageBox
instance before the fake exec() returns.
"""

from typing import List, Tuple

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from gdtf_comparer.core.models import CATEGORY_PHYSICAL
from gdtf_comparer.gui.main_window import MainWindow

XXE_PAYLOAD = b"""<?xml version="1.0"?>
<!DOCTYPE GDTF [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<GDTF DataVersion="1.2"><FixtureType Name="&xxe;"/></GDTF>
"""


@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs: List[Tuple[str, "Qt.TextFormat"]] = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs


def test_corrupt_target_shows_friendly_error(qtbot, tmp_path, make_gdtf, capture_dialogs):
    target = tmp_path / "corrupt.gdtf"
    target.write_text("not a zip")
    compare = make_gdtf("good.gdtf", weight=10.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(compare)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert "Could not open 'corrupt.gdtf'" in text
    assert "not a zip archive" in text
    assert "Traceback" not in text
    assert text_format == Qt.TextFormat.PlainText
    assert window.table_model.rowCount() == 0


def test_malformed_xml_comparison_file_names_the_file(qtbot, make_gdtf, capture_dialogs):
    target = make_gdtf("target.gdtf", weight=10.0)
    good = make_gdtf("good.gdtf", weight=10.0)
    broken = make_gdtf("broken.gdtf", description="<GDTF><FixtureType></GDTF>")

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(good), str(broken)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    assert len(capture_dialogs) == 1
    text, _ = capture_dialogs[0]
    assert "broken.gdtf" in text
    assert window.table_model.rowCount() == 0


def test_unsafe_file_message_mentions_safety(qtbot, make_gdtf, capture_dialogs):
    target = make_gdtf("target.gdtf", weight=10.0)
    unsafe = make_gdtf("unsafe.gdtf", description=XXE_PAYLOAD)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(unsafe)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    assert len(capture_dialogs) == 1
    text, _ = capture_dialogs[0]
    assert "rejected for safety" in text


def test_app_usable_after_error(qtbot, make_gdtf, capture_dialogs):
    target = make_gdtf("target.gdtf", weight=10.0)
    bad = make_gdtf("bad.gdtf", description="<GDTF><FixtureType></GDTF>")
    good_compare = make_gdtf("good-compare.gdtf", weight=10.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(bad)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)
    assert len(capture_dialogs) == 1

    window.compare_list.selectAll()
    window.remove_selected_files()
    window.add_compare_files([str(good_compare)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    weight_row = window.table_model.find_row(CATEGORY_PHYSICAL, "", "Weight")
    assert weight_row >= 0
    assert window.run_button.isEnabled()


def test_no_target_selected_message(qtbot, make_gdtf, capture_dialogs):
    compare = make_gdtf("good.gdtf", weight=10.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.add_compare_files([str(compare)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)

    assert len(capture_dialogs) == 1
    text, _ = capture_dialogs[0]
    assert text == "Select a target GDTF file before running a comparison."
    assert window.is_comparison_running() is False


def test_no_comparison_files_message(qtbot, make_gdtf, capture_dialogs):
    target = make_gdtf("target.gdtf", weight=10.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)

    assert len(capture_dialogs) == 1
    text, _ = capture_dialogs[0]
    assert text == "Add at least one GDTF file to compare against the target."
    assert window.is_comparison_running() is False


def test_unexpected_exception_reported_not_raised(qtbot, make_gdtf, monkeypatch, capture_dialogs):
    import gdtf_comparer.gui.worker as worker_module

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(worker_module, "compare_files", _boom)

    target = make_gdtf("target.gdtf", weight=10.0)
    compare = make_gdtf("good.gdtf", weight=10.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(compare)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    assert len(capture_dialogs) == 1
    text, _ = capture_dialogs[0]
    assert text.startswith("Something went wrong while comparing files (RuntimeError)")
