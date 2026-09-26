"""GUI shutdown tests: bounded closeEvent wait and prompt process exit (WR-01).

A worker stuck in an uninterruptible OS read (e.g. a stalled network mount)
cannot be cancelled from Python (T-01-28/T-01-29). These tests prove
closing the window returns within CLOSE_WAIT_TIMEOUT_MS regardless, and that
the whole process still exits promptly and cleanly (no abort) when a worker
is still stuck after the Qt event loop has ended.
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from PySide6.QtCore import Qt

from gdtf_comparer.gui.main_window import MainWindow

SRC_PATH = Path(__file__).resolve().parents[2] / "src"


def test_close_returns_promptly_when_worker_is_stuck(qtbot, make_gdtf, monkeypatch):
    import gdtf_comparer.gui.main_window as main_window_module
    import gdtf_comparer.gui.worker as worker_module

    monkeypatch.setattr(main_window_module, "CLOSE_WAIT_TIMEOUT_MS", 200)

    target = make_gdtf("target.gdtf", weight=12.5)
    a = make_gdtf("a.gdtf", weight=12.5)

    real_compare_files = worker_module.compare_files
    release = threading.Event()

    def _stuck(*args, **kwargs):
        release.wait(timeout=10)
        return real_compare_files(*args, **kwargs)

    monkeypatch.setattr(worker_module, "compare_files", _stuck)

    window = MainWindow()
    qtbot.addWidget(window)
    window.set_target_file(str(target))
    window.add_compare_files([str(a)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)

    try:
        start = time.monotonic()
        window.close()
        elapsed = time.monotonic() - start

        assert elapsed < 2
        assert window.is_comparison_running() is True
    finally:
        release.set()
        qtbot.waitUntil(lambda: not window.is_comparison_running(), timeout=15000)


def test_app_process_exits_when_worker_stuck_at_close():
    script = (
        "import sys\n"
        "import threading\n"
        "from PySide6.QtWidgets import QApplication\n"
        "from PySide6.QtCore import QTimer\n"
        "import gdtf_comparer.gui.worker as worker_module\n"
        "import gdtf_comparer.gui.main_window as main_window_module\n"
        "import gdtf_comparer.app\n"
        "\n"
        "def _stuck(*args, **kwargs):\n"
        "    threading.Event().wait()\n"
        "\n"
        "worker_module.compare_files = _stuck\n"
        "main_window_module.CLOSE_WAIT_TIMEOUT_MS = 200\n"
        "\n"
        "app = QApplication(sys.argv)\n"
        "\n"
        "def _start():\n"
        "    window = None\n"
        "    for widget in app.topLevelWidgets():\n"
        "        if isinstance(widget, main_window_module.MainWindow):\n"
        "            window = widget\n"
        "            break\n"
        "    window.set_target_file('target.gdtf')\n"
        "    window.add_compare_files(['compare.gdtf'])\n"
        "    window.run_comparison()\n"
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
            f"worker was stuck (stdout={stdout.decode(errors='replace')!r}, "
            f"stderr={stderr.decode(errors='replace')!r})"
        )

    assert proc.returncode == 0, (
        f"process exited with return code {proc.returncode}: "
        f"{stderr.decode(errors='replace')}"
    )
