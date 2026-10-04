"""Loads/saves named compare profiles as one JSON file (ATTR-03, D-01..D-05).

A compare profile is a reusable spec sheet of (category, attribute) pairs
the user has checked in the Attributes panel -- saved once, reloaded later
against a completely unrelated fixture pair (D-01's "substitute fixture"
workflow). Every profile lives in a single JSON file keyed by name, so a
profile name is never a filesystem path component (RESEARCH Pitfall 4).
Writes are atomic: a same-folder temp file is written, flushed, fsynced and
then moved over the old file with os.replace (T-03-02). This module has
zero Qt imports (Phase 1 D-16) and never imports tempfile or shutil (the
Phase 1 architecture guard, tests/test_architecture.py, forbids both in
core/ -- the atomic write below uses os.open(O_EXCL) instead of
tempfile.mkstemp, per this plan's assumption_delta_decision).
"""

import json
import os
import sys
from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Mapping, Optional, Tuple

from gdtf_comparer.core.errors import ProfileNotFoundError, ProfileStorageError

AttributePair = Tuple[str, str]

# Per-user app-data subfolder name, under whichever OS-appropriate base
# directory app_data_dir() resolves (RESEARCH A1).
APP_DATA_DIR_NAME = "GDTF Comparer"

PROFILES_FILE_NAME = "profiles.json"

# Bumped only if the on-disk profiles.json layout ever changes shape. A file
# written by a newer version than this one is refused outright (never
# partially read or silently coerced) so an old app build can never corrupt
# a newer file's data.
PROFILES_SCHEMA_VERSION = 1

# Discretion value (03-01-PLAN.md): a profile name longer than this is
# refused with a friendly message.
MAX_PROFILE_NAME_LENGTH = 80

# Discretion value (03-01-PLAN.md): a profiles.json larger than this is
# treated as damaged rather than read into memory.
MAX_PROFILES_FILE_BYTES = 5 * 1024 * 1024


@dataclass(frozen=True)
class Profile:
    """A named, reusable (category, attribute) selection -- a spec sheet (D-01)."""

    name: str
    attributes: FrozenSet[AttributePair]


def app_data_dir(platform: str, environ: Mapping[str, str], home: str) -> str:
    """Return the per-user app-data directory for this app, hand-rolled.

    Parameters:
        platform: sys.platform's value (e.g. "darwin", "win32", "linux").
        environ: The environment mapping to read APPDATA/XDG_CONFIG_HOME from.
        home: The user's home directory.

    Returns:
        The OS-appropriate per-user config directory (RESEARCH A1):
        %APPDATA% on Windows (falling back to home when unset), macOS's
        ~/Library/Application Support, or $XDG_CONFIG_HOME (when it is a
        non-empty absolute path) else ~/.config on other platforms, joined
        with APP_DATA_DIR_NAME. platformdirs was evaluated and NOT adopted
        (Package Legitimacy Audit: SUS) -- this hand-rolled 3-way branch is
        the deliberate replacement.
    """
    if platform == "win32":
        base = environ.get("APPDATA") or home
    elif platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        xdg = environ.get("XDG_CONFIG_HOME", "")
        if xdg and os.path.isabs(xdg):
            base = xdg
        else:
            base = os.path.join(home, ".config")
    return os.path.join(base, APP_DATA_DIR_NAME)


def _default_profiles_dir() -> str:
    """Return the real per-user profiles directory.

    Computed fresh from sys.platform/os.environ/os.path.expanduser("~") at
    call time, never cached at import time, so tests/conftest.py's autouse
    fixture can monkeypatch this function itself to redirect every test's
    default ProfileRepository into tmp_path -- no test may read or write
    the real per-user profiles folder.
    """
    return app_data_dir(sys.platform, os.environ, os.path.expanduser("~"))


class ProfileRepository:
    """Loads/saves/lists named compare profiles as one JSON file (ATTR-03)."""

    def __init__(self, base_dir: Optional[str] = None) -> None:
        """
        Parameters:
            base_dir: Directory to store profiles.json in. Defaults to the
                real per-user app-data directory (_default_profiles_dir())
                when None. Unlike FixtureRepository's no-argument
                constructor, this one takes an explicit base_dir so tests
                can inject tmp_path directly instead of touching the real
                user profile folder (03-PATTERNS.md: a deliberate,
                documented deviation from the sibling repository's shape).
                The default is resolved here, at construction time -- never
                as a default-argument value evaluated once at import time --
                so tests/conftest.py's monkeypatch of _default_profiles_dir
                takes effect for every ProfileRepository() constructed after
                the patch is applied.
        """
        self._dir = base_dir if base_dir is not None else _default_profiles_dir()
        self._path = os.path.join(self._dir, PROFILES_FILE_NAME)

    @property
    def path(self) -> str:
        """Return the full path to this repository's profiles.json."""
        return self._path

    def load_all(self) -> List[Profile]:
        """Return every saved profile, or [] if no file exists yet.

        Returns:
            Every saved Profile, sorted by name (casefold).

        Raises:
            ProfileStorageError: The file exists but could not be read.
        """
        if not os.path.exists(self._path):
            return []
        with open(self._path, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return sorted(
            (
                Profile(
                    name=entry["name"],
                    attributes=frozenset(tuple(pair) for pair in entry["attributes"]),
                )
                for entry in payload.get("profiles", [])
            ),
            key=lambda profile: profile.name.casefold(),
        )

    def get(self, name: str) -> Profile:
        """Return the saved profile named exactly name.

        Parameters:
            name: The profile name to look up.

        Returns:
            The matching Profile.

        Raises:
            ProfileNotFoundError: No saved profile has this exact name.
        """
        for profile in self.load_all():
            if profile.name == name:
                return profile
        raise ProfileNotFoundError(
            f"There is no saved profile named '{name}'. It may have been renamed or deleted."
        )

    def save(self, name: str, attributes: Iterable[AttributePair]) -> Profile:
        """Create or replace the profile named name with attributes.

        Parameters:
            name: The profile name to store under.
            attributes: The (category, attribute) pairs to save.

        Returns:
            The stored Profile.
        """
        profiles = {profile.name: profile for profile in self.load_all()}
        stored = Profile(name=name, attributes=frozenset(tuple(pair) for pair in attributes))
        profiles[name] = stored
        self._write_all(profiles.values())
        return stored

    def _write_all(self, profiles: Iterable[Profile]) -> None:
        """Atomically replace profiles.json with exactly these profiles.

        Parameters:
            profiles: Every profile that should exist after this call.

        Writes a same-folder temp file (never tempfile.mkstemp -- the Phase
        1 architecture guard forbids importing tempfile in core/), flushes
        and fsyncs it, then moves it over the real path with os.replace.
        os.replace is only atomic within one filesystem, which is why the
        temp file is created in self._dir rather than any other temp
        location (T-03-02).

        Raises:
            ProfileStorageError: The write failed for any reason (OSError).
        """
        os.makedirs(self._dir, mode=0o700, exist_ok=True)
        ordered = sorted(profiles, key=lambda profile: (profile.name.casefold(), profile.name))
        payload = {
            "version": PROFILES_SCHEMA_VERSION,
            "profiles": [
                {
                    "name": profile.name,
                    "attributes": [list(pair) for pair in sorted(profile.attributes)],
                }
                for profile in ordered
            ],
        }
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"

        tmp_path = os.path.join(
            self._dir, "." + PROFILES_FILE_NAME + "." + os.urandom(8).hex() + ".tmp"
        )
        try:
            fd = os.open(
                tmp_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                0o600,
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(text)
                    fh.flush()
                    os.fsync(fh.fileno())
                os.replace(tmp_path, self._path)
            except OSError as exc:
                raise ProfileStorageError(
                    f"Could not save compare profiles to '{self._path}' "
                    f"({type(exc).__name__})."
                ) from exc
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
