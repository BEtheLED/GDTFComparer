"""QThread workers: run core services off the GUI thread (D-14).

Never touch a widget (RESEARCH Pitfall 4) -- only emit signals; all widget
mutation happens in MainWindow's/SubstitutionWindow's connected slots on the
GUI thread. A typed GDTFError/SubstitutionError (RELI-01, Plan 01-04) is
mapped to its friendly user_message; any other exception is logged with a
full traceback and reported as a generic, non-crashing message. Nothing ever
escapes run() into the Qt event loop.
"""

import logging
from typing import List

from PySide6.QtCore import QObject, Signal, Slot

from gdtf_comparer.core.comparator import compare_files
from gdtf_comparer.core.errors import GDTFError, SubstitutionError
from gdtf_comparer.core.mvr_repository import import_mvr
from gdtf_comparer.core.substitution import RequirementSet, scan_candidate_folder

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


class MVRImportWorker(QObject):
    """Runs one import_mvr() call on a QThread (PARSE-02)."""

    import_ready = Signal(object)  # MVRImport
    import_failed = Signal(str)  # user-facing message

    def __init__(self, path: str) -> None:
        """Store the path this worker will import when run().

        Parameters:
            path: Path to the .mvr file to import.
        """
        super().__init__()
        self.path = path

    @Slot()
    def run(self) -> None:
        """Import the stored MVR path and emit the result or a failure message."""
        try:
            result = import_mvr(self.path)
        except GDTFError as exc:
            self.import_failed.emit(exc.user_message)
            return
        except Exception as exc:  # noqa: BLE001 -- last-resort boundary, never re-raised
            logger.exception("Unexpected error while importing an MVR file")
            self.import_failed.emit(
                f"Something went wrong while importing the MVR file ({type(exc).__name__}). "
                "Check that it is a valid MVR show file and try again."
            )
            return
        self.import_ready.emit(result)


class CandidateScanWorker(QObject):
    """Runs one scan_candidate_folder() call on a QThread (SUB-04)."""

    scan_ready = Signal(object)  # CandidateScan
    scan_failed = Signal(str)  # user-facing message

    def __init__(self, folder: str, requirement_set: RequirementSet) -> None:
        """Store the folder and requirements this worker will scan when run().

        Parameters:
            folder: Path to the inventory folder to scan.
            requirement_set: The requirements to score each candidate against.
        """
        super().__init__()
        self.folder = folder
        self.requirement_set = requirement_set

    @Slot()
    def run(self) -> None:
        """Scan the stored folder and emit the result or a failure message."""
        try:
            result = scan_candidate_folder(self.folder, self.requirement_set)
        except (SubstitutionError, GDTFError) as exc:
            self.scan_failed.emit(str(exc))
            return
        except Exception as exc:  # noqa: BLE001 -- last-resort boundary, never re-raised
            logger.exception("Unexpected error while checking an inventory folder")
            self.scan_failed.emit(
                f"Something went wrong while checking the inventory folder ({type(exc).__name__}). "
                "Try again."
            )
            return
        self.scan_ready.emit(result)
