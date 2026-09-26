"""Composition root: builds the QApplication and MainWindow.

Local run command: PYTHONPATH=src .venv/bin/python -m gdtf_comparer.app
(from the repo root, using the shared venv described in Plan 01-01).
"""

import sys
from typing import Optional, Sequence

from PySide6.QtWidgets import QApplication

from gdtf_comparer.gui.main_window import MainWindow


def create_main_window(app: QApplication) -> MainWindow:
    """Build the application's main window.

    Parameters:
        app: The QApplication this window belongs to.

    Returns:
        A new, unshown MainWindow instance.
    """
    app.setApplicationName("GDTF Comparer")
    return MainWindow()


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the GDTF Comparer application.

    Parameters:
        argv: Command-line arguments; defaults to sys.argv when None.

    Returns:
        The Qt application's exit code.
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv) if argv is not None else sys.argv)
    window = create_main_window(app)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
