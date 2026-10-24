"""GUI tests for MVR import in SubstitutionWindow: summary wording, empty
state, friendly dialogs, one-import-at-a-time, and clean shutdown
(PARSE-02, SUB-01).
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Tuple

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from gdtf_comparer.core.models import CATEGORY_PHYSICAL, AttributeKey
from gdtf_comparer.core.mvr_repository import NO_FIXTURES_TEMPLATE, import_mvr, import_summary_message
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.substitution_window import NO_MVR_PLACEHOLDER, SubstitutionWindow

from tests.conftest import build_gdtf_bytes

SRC_PATH = Path(__file__).resolve().parents[2] / "src"

XXE_SCENE_XML = b"""<?xml version="1.0"?>
<!DOCTYPE GeneralSceneDescription [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<GeneralSceneDescription verMajor="1" verMinor="6"><Scene>&xxe;</Scene></GeneralSceneDescription>
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


def test_skipped_types_named_in_window(qtbot, make_mvr, monkeypatch):
    good_bytes = build_gdtf_bytes(name="Good Fixture")
    path = make_mvr(
        "mixed.mvr",
        fixtures=[("Good", "Good.gdtf"), ("Missing", "Missing.gdtf")],
        gdtf_members={"Good.gdtf": good_bytes},
    )

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 1
    expected = import_summary_message(import_mvr(str(path)))
    assert window.mvr_summary_label.text() == expected


def test_empty_mvr_shows_message_not_crash(qtbot, make_mvr, monkeypatch):
    path = make_mvr("empty.mvr")

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 0
    assert window.mvr_summary_label.text() == NO_FIXTURES_TEMPLATE.format(file="empty.mvr")
    assert window.save_requirements_button.isEnabled() is False
    assert window.use_for_inventory_button.isEnabled() is False


def test_single_type_is_a_single_row(qtbot, make_mvr, monkeypatch):
    spot_bytes = build_gdtf_bytes(name="Spot A", weight=10.0)
    path = make_mvr(
        "single.mvr", fixtures=[("F1", "A@Spot.gdtf")], gdtf_members={"A@Spot.gdtf": spot_bytes}
    )

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 1
    assert window.fixture_list.currentRow() == 0
    leaf = window.requirements_editor.leaf_item(AttributeKey(CATEGORY_PHYSICAL, "", "Weight"))
    assert leaf is not None


def test_summary_label_is_plain_text(qtbot, make_mvr, monkeypatch):
    bogus_spec = "<b>x</b>.gdtf"
    path = make_mvr("markup.mvr", fixtures=[("F1", bogus_spec)])

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.mvr_summary_label.textFormat() == Qt.TextFormat.PlainText
    assert bogus_spec in window.mvr_summary_label.text()


def test_accented_fixture_type_imports_in_window(qtbot, make_mvr, monkeypatch):
    spec = "Lumière@Spot.gdtf"
    spot_bytes = build_gdtf_bytes(name="Lumiere Spot")
    path = make_mvr("accented.mvr", fixtures=[("F1", spec)], gdtf_members={spec: spot_bytes})

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 1, timeout=10000
    )

    assert window.fixture_list.item(0).toolTip() == spec


def test_hostile_mvr_shows_one_friendly_dialog(qtbot, make_mvr, monkeypatch, capture_dialogs):
    path = make_mvr("xxe.mvr", scene_xml=XXE_SCENE_XML)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert len(capture_dialogs) == 1
    text, text_format = capture_dialogs[0]
    assert text.startswith("Could not open 'xxe.mvr':")
    assert text_format == Qt.TextFormat.PlainText
    assert window.fixture_list.count() == 0
    assert window.mvr_summary_label.text() == NO_MVR_PLACEHOLDER
    assert window.import_mvr_button.isEnabled()


def test_failed_import_clears_previous_list(qtbot, make_mvr, tmp_path, monkeypatch, capture_dialogs):
    spot_bytes = build_gdtf_bytes(name="Spot A")
    wash_bytes = build_gdtf_bytes(name="Wash A")
    good_path = make_mvr(
        "good.mvr",
        fixtures=[("F1", "A@Spot.gdtf"), ("F2", "B@Wash.gdtf")],
        gdtf_members={"A@Spot.gdtf": spot_bytes, "B@Wash.gdtf": wash_bytes},
    )

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(good_path))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 2, timeout=10000
    )

    bad_path = tmp_path / "bad.mvr"
    bad_path.write_bytes(b"not a zip")
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(bad_path))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.import_mvr_button.isEnabled(), timeout=10000)

    assert window.fixture_list.count() == 0
    assert window.requirements_editor.requirement_set() is None


def test_import_button_disabled_while_importing(qtbot, make_mvr, monkeypatch):
    """PARSE-02 concurrency: Import MVR... is disabled for the whole import,
    and a second click while one is running never asks for a second path."""
    import gdtf_comparer.gui.worker as worker_module

    good_bytes = build_gdtf_bytes(name="Spot A")
    path = make_mvr(
        "gated.mvr", fixtures=[("F1", "A@Spot.gdtf")], gdtf_members={"A@Spot.gdtf": good_bytes}
    )

    real_import_mvr = worker_module.import_mvr
    release = threading.Event()

    def _gated(*args, **kwargs):
        release.wait(timeout=10)
        return real_import_mvr(*args, **kwargs)

    monkeypatch.setattr(worker_module, "import_mvr", _gated)

    window = SubstitutionWindow()
    qtbot.addWidget(window)

    ask_calls = []

    def _ask():
        ask_calls.append(1)
        return str(path)

    monkeypatch.setattr(window, "_ask_open_mvr_path", _ask)

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.is_busy(), timeout=5000)

    assert window.import_mvr_button.isEnabled() is False
    assert window.is_busy() is True

    window.import_mvr()
    assert len(ask_calls) == 1

    release.set()
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 1, timeout=10000
    )
    assert len(ask_calls) == 1


def test_no_partial_list_while_import_runs(qtbot, make_mvr, monkeypatch):
    """SUB-01 concurrency: the fixture list stays empty for the whole import,
    then appears complete in one step -- never a half-built list."""
    import gdtf_comparer.gui.worker as worker_module

    good_bytes = build_gdtf_bytes(name="Spot A")
    path = make_mvr(
        "gated2.mvr", fixtures=[("F1", "A@Spot.gdtf")], gdtf_members={"A@Spot.gdtf": good_bytes}
    )

    real_import_mvr = worker_module.import_mvr
    release = threading.Event()

    def _gated(*args, **kwargs):
        release.wait(timeout=10)
        return real_import_mvr(*args, **kwargs)

    monkeypatch.setattr(worker_module, "import_mvr", _gated)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.wait(100)
    assert window.fixture_list.count() == 0

    release.set()
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 1, timeout=10000
    )


def test_reimport_replaces_list_wholesale(qtbot, make_mvr, monkeypatch):
    a_bytes = build_gdtf_bytes(name="A Spot")
    b_bytes = build_gdtf_bytes(name="B Spot")
    c_bytes = build_gdtf_bytes(name="C Wash")
    path_a = make_mvr(
        "a.mvr",
        fixtures=[("F1", "A@Spot.gdtf"), ("F2", "B@Spot.gdtf")],
        gdtf_members={"A@Spot.gdtf": a_bytes, "B@Spot.gdtf": b_bytes},
    )
    path_b = make_mvr("b.mvr", fixtures=[("F1", "C@Wash.gdtf")], gdtf_members={"C@Wash.gdtf": c_bytes})

    window = SubstitutionWindow()
    qtbot.addWidget(window)

    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path_a))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 2, timeout=10000
    )

    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path_b))
    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(
        lambda: window.import_mvr_button.isEnabled() and window.fixture_list.count() == 1, timeout=10000
    )

    assert window.fixture_list.item(0).data(Qt.ItemDataRole.UserRole) == "C@Wash.gdtf"


def test_close_during_import_returns_promptly(qtbot, make_mvr, monkeypatch):
    import gdtf_comparer.gui.substitution_window as substitution_window_module
    import gdtf_comparer.gui.worker as worker_module

    monkeypatch.setattr(substitution_window_module, "SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS", 200)

    path = make_mvr("stuck.mvr")
    real_import_mvr = worker_module.import_mvr
    release = threading.Event()

    def _stuck(*args, **kwargs):
        release.wait(timeout=10)
        return real_import_mvr(*args, **kwargs)

    monkeypatch.setattr(worker_module, "import_mvr", _stuck)

    window = SubstitutionWindow()
    qtbot.addWidget(window)
    monkeypatch.setattr(window, "_ask_open_mvr_path", lambda: str(path))

    qtbot.mouseClick(window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.wait(100)

    try:
        start = time.monotonic()
        window.close()
        elapsed = time.monotonic() - start

        assert elapsed < 2
        assert window.fixture_list.count() == 0
    finally:
        release.set()
        qtbot.waitUntil(lambda: not window.is_busy(), timeout=15000)


def test_closing_main_window_closes_substitution_window(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    qtbot.mouseClick(window.substitutes_button, Qt.MouseButton.LeftButton)
    assert window.substitution_window.isVisible()

    window.close()

    assert window.substitution_window.isVisible() is False


def test_is_substitution_running_reflects_worker(qtbot, make_mvr, monkeypatch):
    import gdtf_comparer.gui.worker as worker_module

    window = MainWindow()
    qtbot.addWidget(window)
    assert window.is_substitution_running() is False

    path = make_mvr("gated3.mvr")
    real_import_mvr = worker_module.import_mvr
    release = threading.Event()

    def _gated(*args, **kwargs):
        release.wait(timeout=10)
        return real_import_mvr(*args, **kwargs)

    monkeypatch.setattr(worker_module, "import_mvr", _gated)

    window.open_substitution_window()
    monkeypatch.setattr(window.substitution_window, "_ask_open_mvr_path", lambda: str(path))
    qtbot.mouseClick(window.substitution_window.import_mvr_button, Qt.MouseButton.LeftButton)
    qtbot.wait(100)

    assert window.is_substitution_running() is True

    release.set()
    qtbot.waitUntil(lambda: window.is_substitution_running() is False, timeout=10000)


def test_app_process_exits_when_substitution_worker_stuck():
    script = (
        "import sys\n"
        "import threading\n"
        "from PySide6.QtWidgets import QApplication\n"
        "from PySide6.QtCore import QTimer\n"
        "import gdtf_comparer.gui.worker as worker_module\n"
        "import gdtf_comparer.gui.substitution_window as substitution_window_module\n"
        "import gdtf_comparer.gui.main_window as main_window_module\n"
        "import gdtf_comparer.app\n"
        "\n"
        "def _stuck(*args, **kwargs):\n"
        "    threading.Event().wait()\n"
        "\n"
        "worker_module.import_mvr = _stuck\n"
        "substitution_window_module.SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS = 200\n"
        "\n"
        "app = QApplication(sys.argv)\n"
        "\n"
        "def _start():\n"
        "    window = None\n"
        "    for widget in app.topLevelWidgets():\n"
        "        if isinstance(widget, main_window_module.MainWindow):\n"
        "            window = widget\n"
        "            break\n"
        "    window.open_substitution_window()\n"
        "    window.substitution_window._ask_open_mvr_path = lambda: 'show.mvr'\n"
        "    window.substitution_window.import_mvr()\n"
        "    QTimer.singleShot(300, window.close)\n"
        "\n"
        "QTimer.singleShot(0, _start)\n"
        "sys.exit(gdtf_comparer.app.main([]))\n"
    )

    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_PATH)
    env["QT_QPA_PLATFORM"] = "offscreen"

    proc = subprocess.Popen(
        [sys.executable, "-c", script],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        stdout, stderr = proc.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()
        raise AssertionError(
            "app did not exit within 20 s after its window was closed while a "
            f"substitution worker was stuck (stdout={stdout.decode(errors='replace')!r}, "
            f"stderr={stderr.decode(errors='replace')!r})"
        )

    assert proc.returncode == 0, (
        f"process exited with return code {proc.returncode}: "
        f"{stderr.decode(errors='replace')}"
    )
