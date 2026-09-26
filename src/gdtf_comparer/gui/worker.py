"""QThread worker: runs core.comparator.compare_files off the GUI thread (D-14).

Never touches a widget (RESEARCH Pitfall 4) -- only emits signals; all widget
mutation happens in MainWindow's connected slots on the GUI thread.
"""

from typing import List

from PySide6.QtCore import QObject, Signal, Slot

from gdtf_comparer.core.comparator import compare_files


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
        except Exception as exc:  # noqa: BLE001 -- Plan 01-04 replaces with typed messages
            self.comparison_failed.emit(f"Could not compare these files: {exc}")
            return
        self.comparison_ready.emit(result)
