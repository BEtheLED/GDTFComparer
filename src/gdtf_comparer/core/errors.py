"""Typed GDTF loading errors carrying a friendly user_message (RELI-01, D-12).

GDTFError.user_message names the failing file and a lowercase reason
fragment only -- never a traceback or exception repr (T-01-17) -- so it is
always safe to show directly in a GUI dialog. This module also holds the
compare-profile errors (ATTR-03) raised by core.profile_repository, the MVR
import errors (PARSE-02) raised by core.mvr_repository, and the
fixture-substitution errors (SUB-01..04) raised by core.substitution and
core.requirements_repository.
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


class MVRError(GDTFError):
    """An MVR show file could not be imported (PARSE-02); same path + reason + user_message shape as GDTFError."""


class MVRValidationError(MVRError):
    """The file is not a readable, valid MVR archive."""


class MVRUnsafeFileError(MVRValidationError):
    """The file was rejected by a safety limit (size, ratio, XXE)."""


class MVRParseError(MVRError):
    """pymvr itself failed to parse an already-validated file."""


class ProfileError(Exception):
    """Base error for compare-profile persistence failures (ATTR-03).

    Unlike GDTFError, a profile error has no single failing file path to
    name -- every saved profile lives in one shared profiles.json -- so this
    is constructed directly with a friendly, complete message string.

    Parameters:
        message: The friendly, user-facing message, safe to show directly in
            a GUI dialog (no tracebacks, no exception reprs).
    """

    def __init__(self, message: str) -> None:
        self.user_message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.user_message


class ProfileNameError(ProfileError):
    """A profile name is invalid, or conflicts with a reserved rule."""


class ProfileNotFoundError(ProfileError):
    """No saved profile exists under the given name."""


class ProfileStorageError(ProfileError):
    """profiles.json could not be read, is damaged or too new, or could not be written."""


class SubstitutionError(Exception):
    """Base error for fixture-substitution failures (SUB-01..04).

    Shaped exactly like ProfileError: there is no single failing file path
    to name for a requirements-file or inventory-folder failure, so this is
    constructed directly with a friendly, complete message string.

    Parameters:
        message: The friendly, user-facing message, safe to show directly in
            a GUI dialog (no tracebacks, no exception reprs).
    """

    def __init__(self, message: str) -> None:
        self.user_message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.user_message


class RequirementsFileError(SubstitutionError):
    """A requirements file could not be read, is damaged or too new, or could not be written."""


class CandidateFolderError(SubstitutionError):
    """The inventory folder could not be listed."""
