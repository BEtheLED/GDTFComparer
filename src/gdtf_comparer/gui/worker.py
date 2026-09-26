"""QThread worker: runs core.comparator.compare_files off the GUI thread (D-14).

Never touches a widget (RESEARCH Pitfall 4) -- only emits signals; all widget
mutation happens in MainWindow's connected slots on the GUI thread. A typed
GDTFError (RELI-01, Plan 01-04) is mapped to its friendly user_message; any
other exception is logged with a full traceback and reported as a generic,
non-crashing message. Nothing ever escapes run() into the Qt event loop.
"""

import logging
from typing import List

from PySide6.QtCore import QObject, Signal, Slot

from gdtf_comparer.core.comparator import compare_files
from gdtf_comparer.core.errors import GDTFError

logger = logging.getLogger(__name__)


class ComparisonWorker(QObject):
    """Runs one target-vs-comparisons compare_files() call on a QThread."""

    comparison_ready = Signal(object)  # ComparisonResult
    comparison_failed = Signal(str)  # user-facing message

    def __init__(self, target_path: str, compare_paths: List[str]) -> None:
        """Store the paths this worker will compare when run().

        Parameters:
            target_path: Path to the target .gdtf file.
            compare_paths: Paths to the comparison .gdtf files, in order.
        """
        super().__init__()
        self.target_path = target_path
        self.compare_paths = compare_paths

    @Slot()
    def run(self) -> None:
        """Compare the stored paths and emit the result or a failure message."""
        try:
            result = compare_files(self.target_path, self.compare_paths)
        except GDTFError as exc:
            self.comparison_failed.emit(exc.user_message)
            return
        except Exception as exc:  # noqa: BLE001 -- last-resort boundary, never re-raised
            logger.exception("Unexpected error while comparing GDTF files")
            self.comparison_failed.emit(
                f"Something went wrong while comparing files ({type(exc).__name__}). "
                "Check that every selected file is a valid GDTF fixture and try again."
            )
            return
        self.comparison_ready.emit(result)
