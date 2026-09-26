"""End-to-end tracer tests: headless core, pytest-qt GUI, and a launch smoke test.

Never asserts a total row count -- Plan 01-03 adds Beam/model rows to the
same fixture files used here.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from gdtf_comparer.core.comparator import compare_files
from gdtf_comparer.core.models import CATEGORY_PHYSICAL
from gdtf_comparer.gui.main_window import MainWindow

SRC_PATH = str(Path(__file__).resolve().parents[1] / "src")


def test_compare_files_headless(make_gdtf):
    target = make_gdtf("target.gdtf", name="Target Fixture", weight=12.5)
    a = make_gdtf("a.gdtf", name="A Fixture", weight=12.5)
    b = make_gdtf("b.gdtf", name="B Fixture", weight=14.0)

    result = compare_files(str(target), [str(a), str(b)])

    weight_rows = [
        row
        for row in result.rows
        if row.key.category == CATEGORY_PHYSICAL
        and row.key.element_path == ""
        and row.key.attribute == "Weight"
    ]
    assert len(weight_rows) == 1
    weight_row = weight_rows[0]
    assert weight_row.target_value == 12.5
    assert weight_row.comparison_values == (12.5, 14.0)
    assert weight_row.differs == (False, True)

    assert result.target.name == "Target Fixture"
    assert hasattr(result.target.fixture_type, "dmx_modes")
    assert hasattr(result.target.fixture_type, "geometries")


def test_core_imports_without_qt():
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC_PATH
    snippet = (
        "import sys\n"
        "import gdtf_comparer.core.comparator\n"
        "assert 'PySide6' not in sys.modules\n"
    )
    proc = subprocess.run([sys.executable, "-c", snippet], env=env)
    assert proc.returncode == 0


def test_gui_run_comparison_populates_table(qtbot, make_gdtf):
    target = make_gdtf("target.gdtf", name="Target Fixture", weight=12.5)
    a = make_gdtf("a.gdtf", weight=12.5)
    b = make_gdtf("b.gdtf", weight=14.0)

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target))
    window.add_compare_files([str(a), str(b)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    model = window.table_model
    row_index = model.find_row(CATEGORY_PHYSICAL, "", "Weight")
    assert row_index >= 0

    assert model.data(model.index(row_index, model.COL_CATEGORY)) == "Physical Properties"
    assert model.data(model.index(row_index, model.COL_ELEMENT)) == "Fixture"
    assert model.data(model.index(row_index, model.COL_ATTRIBUTE)) == "Weight"
    assert model.data(model.index(row_index, model.COL_TARGET)) == "12.5"
    assert model.data(model.index(row_index, model.COL_TARGET + 1)) == "12.5"
    assert model.data(model.index(row_index, model.COL_TARGET + 2)) == "14"

    headers = [
        model.headerData(col, Qt.Orientation.Horizontal)
        for col in range(model.columnCount())
    ]
    assert "Target: target.gdtf" in headers
    assert "a.gdtf" in headers
    assert "b.gdtf" in headers


def test_comparison_runs_off_ui_thread(qtbot, make_gdtf, monkeypatch):
    target = make_gdtf("target.gdtf", weight=12.5)
    a = make_gdtf("a.gdtf", weight=12.5)

    test_thread_ident = threading.get_ident()
    recorded = {}

    import gdtf_comparer.gui.worker as worker_module

    real_compare_files = worker_module.compare_files

    def _wrapped(*args, **kwargs):
        recorded["ident"] = threading.get_ident()
        return real_compare_files(*args, **kwargs)

    monkeypatch.setattr(worker_module, "compare_files", _wrapped)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(a)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    assert "ident" in recorded
    assert recorded["ident"] != test_thread_ident


def test_run_button_disabled_until_worker_thread_stops(qtbot, make_gdtf):
    target = make_gdtf("target.gdtf", weight=12.5)
    a = make_gdtf("a.gdtf", weight=12.5)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(a)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    assert window.run_button.isEnabled() is False
    assert window.is_comparison_running() is True

    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)
    assert window.is_comparison_running() is False


def test_close_during_comparison_does_not_crash(qtbot, make_gdtf, monkeypatch):
    target = make_gdtf("target.gdtf", weight=12.5)
    a = make_gdtf("a.gdtf", weight=12.5)

    import gdtf_comparer.gui.worker as worker_module

    real_compare_files = worker_module.compare_files

    def _slow(*args, **kwargs):
        time.sleep(0.3)
        return real_compare_files(*args, **kwargs)

    monkeypatch.setattr(worker_module, "compare_files", _slow)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(a)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    window.close()

    assert window.is_comparison_running() is False


def test_app_module_launches():
    env = dict(os.environ)
    env["PYTHONPATH"] = SRC_PATH
    env["QT_QPA_PLATFORM"] = "offscreen"

    proc = subprocess.Popen(
        [sys.executable, "-m", "gdtf_comparer.app"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            pass
        else:
            _, stderr = proc.communicate()
            pytest.fail(
                "gdtf_comparer.app exited early with code "
                f"{proc.returncode}: {stderr.decode(errors='replace')}"
            )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
