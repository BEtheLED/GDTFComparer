"""Typed GDTF loading errors carrying a friendly user_message (RELI-01, D-12).

GDTFError.user_message names the failing file and a lowercase reason
fragment only -- never a traceback or exception repr (T-01-17) -- so it is
always safe to show directly in a GUI dialog.
"""

import os


class GDTFError(Exception):
    """Base error for a GDTF file that could not be loaded.

    Parameters:
        path: Path to the file that failed to load.
        reason: Lowercase sentence fragment describing why, safe to show to
            the user (no tracebacks, no exception reprs).
    """

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(self.user_message)

    @property
    def file_name(self) -> str:
        """Return the basename of the failing file."""
        return os.path.basename(self.path)

    @property
    def user_message(self) -> str:
        """Return the friendly, user-facing message for this error."""
        return f"Could not open '{self.file_name}': {self.reason}"

    def __str__(self) -> str:
        return self.user_message


class GDTFValidationError(GDTFError):
    """The file is not a readable, valid GDTF archive."""


class GDTFUnsafeFileError(GDTFValidationError):
    """The file was rejected by a RELI-02 safety limit (size, ratio, XXE)."""


class GDTFParseError(GDTFError):
    """pygdtf itself failed to parse an already-validated file."""
