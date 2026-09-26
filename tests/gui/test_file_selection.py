"""Target-vs-comparison self-selection guard tests (WR-02, RELI-01 family).

A file can never end up as both the target and a comparison file: adding
the current target as a comparison is refused, and choosing a listed
comparison file as the new target evicts it from the list. Both cases are
reported in the status bar so a self-comparison never silently produces a
misleading "no differences" table.
"""

import os
import sys
from typing import List, Tuple

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from gdtf_comparer.gui.main_window import MainWindow


@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs: List[Tuple[str, "Qt.TextFormat"]] = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs


def test_target_file_is_not_added_as_comparison(qtbot, make_gdtf, capture_dialogs):
    target = make_gdtf("target.gdtf", weight=10.0)
    other = make_gdtf("other.gdtf", weight=20.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(target), str(other)])

    assert window.compare_files == [str(other)]
    assert window.compare_list.count() == 1
    assert "already selected as the target" in window.statusBar().currentMessage()

    window2 = MainWindow()
    qtbot.addWidget(window2)
    window2.set_target_file(str(target))
    window2.add_compare_files([str(target)])

    assert window2.compare_files == []

    qtbot.mouseClick(window2.run_button, Qt.MouseButton.LeftButton)

    assert len(capture_dialogs) == 1
    text, _ = capture_dialogs[0]
    assert text == "Add at least one GDTF file to compare against the target."
    assert window2.is_comparison_running() is False


def test_new_target_is_removed_from_comparison_list(qtbot, make_gdtf):
    a = make_gdtf("a.gdtf", weight=10.0)
    b = make_gdtf("b.gdtf", weight=20.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.add_compare_files([str(a), str(b)])
    window.set_target_file(str(a))

    assert window.compare_files == [str(b)]
    assert window.compare_list.count() == 1
    remaining_item = window.compare_list.item(0)
    assert remaining_item.data(Qt.ItemDataRole.UserRole) == str(b)
    assert "now the target" in window.statusBar().currentMessage()


def test_same_file_via_alternate_path_is_detected(qtbot, make_gdtf, tmp_path):
    target = make_gdtf("target.gdtf", weight=10.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))

    alternate = os.path.join(str(target.parent), ".", target.name)
    window.add_compare_files([alternate])
    assert window.compare_files == []

    if hasattr(os, "symlink") and sys.platform != "win32":
        link = tmp_path / "target_link.gdtf"
        os.symlink(target, link)
        window.add_compare_files([str(link)])
        assert window.compare_files == []


def test_distinct_comparison_files_are_still_added(qtbot, make_gdtf):
    target = make_gdtf("target.gdtf", weight=10.0)
    a = make_gdtf("a.gdtf", weight=20.0)
    b = make_gdtf("b.gdtf", weight=30.0)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.statusBar().clearMessage()
    window.add_compare_files([str(a), str(b), str(a)])

    assert window.compare_files == [str(a), str(b)]
    assert window.statusBar().currentMessage() == ""
