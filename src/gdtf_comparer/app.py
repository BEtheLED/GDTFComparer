"""Composition root: builds the QApplication and MainWindow.

Local run command: PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app
(from the repo root, using the shared venv described in Plan 01-01).
"""

import logging
import os
import sys
from typing import Optional, Sequence

from PySide6.QtWidgets import QApplication

from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.theme import install_os_theme

_LOGGER = logging.getLogger(__name__)


def create_main_window(app: QApplication) -> MainWindow:
    """Build the application's main window.

    Parameters:
        app: The QApplication this window belongs to.

    Returns:
        A new, unshown MainWindow instance.
    """
    app.setApplicationName("GDTF Comparer")
    install_os_theme(app)
    return MainWindow()


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the GDTF Comparer application.

    Parameters:
        argv: Command-line arguments; defaults to sys.argv when None.

    Returns:
        The application's exit code. Normally the Qt event loop's own exit
        code; see the note below for the one case where the process ends via
        os._exit instead.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else sys.argv)
    window = create_main_window(app)
    window.show()
    exit_code = app.exec()

    if window.is_comparison_running() or window.is_substitution_running():
        # Qt aborts the process if a still-running QThread is destroyed
        # during interpreter shutdown, and a thread blocked in a kernel read
        # cannot be stopped from Python (WR-01, T-01-29). This path only runs
        # once the event loop has already ended (closeEvent's bounded wait,
        # CLOSE_WAIT_TIMEOUT_MS / SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS, gave up
        # on a stuck worker) -- normal closes never reach here. Nothing is
        # lost by skipping the rest of normal shutdown: comparison work and
        # the Find Substitutes window's MVR import/inventory scan workers
        # (Phase 5 Task 3) only read files, and a compare-profile save
        # (core.profile_repository, Phase 3) or a requirements-file save
        # (core.requirements_repository, Phase 5) runs synchronously on the
        # GUI thread and finishes -- atomically -- well before the event loop
        # returns, so this path can never cut one short.
        _LOGGER.warning(
            "A comparison or Find Substitutes worker is still running at "
            "shutdown; exiting the process directly instead of risking a "
            "Qt abort."
        )
        logging.shutdown()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(exit_code)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
