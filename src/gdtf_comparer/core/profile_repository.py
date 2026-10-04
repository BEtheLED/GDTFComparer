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
import unicodedata
from dataclasses import dataclass
from typing import FrozenSet, Iterable, List, Mapping, Optional, Tuple

from gdtf_comparer.core.errors import ProfileNameError, ProfileNotFoundError, ProfileStorageError

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


def normalize_profile_name(name: str) -> str:
    """Validate and normalize a user-entered profile name (D-04, ASVS V5).

    Parameters:
        name: The raw, user-entered profile name.

    Returns:
        The trimmed, Unicode-NFC-normalized name, unchanged in display case
        -- name identity for matching purposes is handled separately by
        profile_name_key; this function only validates and normalizes form.

    Raises:
        ProfileNameError: name is empty/whitespace-only after trimming,
            longer than MAX_PROFILE_NAME_LENGTH characters, or contains a
            line break, tab or other control character.
    """
    normalized = unicodedata.normalize("NFC", name.strip())
    if not normalized:
        raise ProfileNameError("Enter a name for the profile.")
    if len(normalized) > MAX_PROFILE_NAME_LENGTH:
        raise ProfileNameError(
            f"Profile names can be at most {MAX_PROFILE_NAME_LENGTH} characters."
        )
    if any(unicodedata.category(character) in ("Cc", "Cs") for character in normalized):
        raise ProfileNameError(
            "Profile names can't contain line breaks, tabs or other control characters."
        )
    return normalized


def profile_name_key(name: str) -> str:
    """Return the case/whitespace/Unicode-form-insensitive identity of name.

    Parameters:
        name: A profile name, raw or already normalized.

    Returns:
        unicodedata.normalize("NFC", name.strip()).casefold(). Never raises
        -- two names are the same profile exactly when this key matches for
        both (D-04: "Moving Head Spec" and "  moving head spec " collide;
        "Façade" typed with a combining cedilla matches its precomposed
        form).
    """
    return unicodedata.normalize("NFC", name.strip()).casefold()


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
            Every saved Profile, sorted by profile_name_key (case,
            surrounding whitespace and Unicode-form insensitive), then by
            name, for deterministic output.

        Raises:
            ProfileStorageError: The file exists but is too large, not
                valid UTF-8/JSON, an unexpected shape, or was written by a
                newer version of this app -- never for a missing file.
                Because save() starts from load_all(), any of these also
                stops every write before anything is written: a damaged,
                oversized or newer-version file is never silently replaced.
        """
        if not os.path.exists(self._path):
            return []

        try:
            with open(self._path, "rb") as fh:
                raw = fh.read(MAX_PROFILES_FILE_BYTES + 1)
        except OSError as exc:
            raise self._damaged(type(exc).__name__) from exc

        if len(raw) > MAX_PROFILES_FILE_BYTES:
            raise ProfileStorageError(
                f"Your saved compare profiles could not be read: '{self._path}' is too "
                "large to be a profiles file. It was left unchanged."
            )

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            raise self._damaged(type(exc).__name__) from exc

        return self._parse_payload(payload)

    def _damaged(self, detail: str) -> ProfileStorageError:
        """Build the typed error for a damaged profiles.json (T-03-01).

        Parameters:
            detail: A short, lowercase-friendly reason fragment (a caught
                exception's type name, or a shape-validation detail such as
                "unexpected layout" or "duplicate profile names").

        Returns:
            A ProfileStorageError naming self._path and detail. The caller
            raises it, optionally chained with "from exc" to preserve the
            original cause.
        """
        return ProfileStorageError(
            f"Your saved compare profiles could not be read: '{self._path}' is damaged "
            f"({detail}). It was left unchanged."
        )

    def _parse_payload(self, payload: object) -> List[Profile]:
        """Validate a decoded profiles.json payload's shape and build Profiles.

        Parameters:
            payload: The json.loads() result of the file's contents.

        Returns:
            Every Profile the payload describes, sorted by profile_name_key
            then name.

        Raises:
            ProfileStorageError: The payload is not a dict; "version" is
                missing, not a plain int (a JSON true is refused), or newer
                than PROFILES_SCHEMA_VERSION (reported distinctly as "newer
                version"), or older/other than this version; "profiles" is
                not a list; an entry is not a dict, has a non-string or
                invalid name, or an "attributes" value that is not a list of
                2-item string pairs; or two entries share a profile_name_key.
        """
        if not isinstance(payload, dict):
            raise self._damaged("unexpected layout")

        version = payload.get("version")
        if type(version) is not int:
            raise self._damaged("unexpected layout")
        if version > PROFILES_SCHEMA_VERSION:
            raise ProfileStorageError(
                f"Your saved compare profiles at '{self._path}' were saved by a newer "
                "version of GDTF Comparer. They were left unchanged."
            )
        if version != PROFILES_SCHEMA_VERSION:
            raise self._damaged("unexpected layout")

        entries = payload.get("profiles")
        if not isinstance(entries, list):
            raise self._damaged("unexpected layout")

        profiles: List[Profile] = []
        seen_keys = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise self._damaged("unexpected layout")

            name = entry.get("name")
            if not isinstance(name, str):
                raise self._damaged("unexpected layout")
            try:
                normalize_profile_name(name)
            except ProfileNameError:
                raise self._damaged("a profile has an invalid name") from None

            attributes = entry.get("attributes")
            if not isinstance(attributes, list):
                raise self._damaged("unexpected layout")
            pairs = []
            for pair in attributes:
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    raise self._damaged("unexpected layout")
                category, attribute = pair
                if not isinstance(category, str) or not category:
                    raise self._damaged("unexpected layout")
                if not isinstance(attribute, str) or not attribute:
                    raise self._damaged("unexpected layout")
                pairs.append((category, attribute))

            key = profile_name_key(name)
            if key in seen_keys:
                raise self._damaged("duplicate profile names")
            seen_keys.add(key)

            profiles.append(Profile(name=name, attributes=frozenset(pairs)))

        return sorted(
            profiles, key=lambda profile: (profile_name_key(profile.name), profile.name)
        )

    def find(self, name: str) -> Optional[Profile]:
        """Return the saved profile matching name, or None.

        Parameters:
            name: The profile name to look up. Matched by profile_name_key,
                so surrounding whitespace, letter case and Unicode
                normalization form are all ignored (D-04).

        Returns:
            The matching Profile, or None if no saved profile matches.
        """
        key = profile_name_key(name)
        for profile in self.load_all():
            if profile_name_key(profile.name) == key:
                return profile
        return None

    def get(self, name: str) -> Profile:
        """Return the saved profile matching name (profile_name_key identity).

        Parameters:
            name: The profile name to look up.

        Returns:
            The matching Profile.

        Raises:
            ProfileNotFoundError: No saved profile matches name.
        """
        profile = self.find(name)
        if profile is None:
            raise ProfileNotFoundError(
                f"There is no saved profile named '{name}'. It may have been renamed or deleted."
            )
        return profile

    def save(self, name: str, attributes: Iterable[AttributePair]) -> Profile:
        """Create or replace the profile matching name with attributes.

        Parameters:
            name: The profile name to store under. Validated and normalized
                by normalize_profile_name (D-04 overwrite confirmation
                itself happens in the GUI, not here -- this always writes).
            attributes: The (category, attribute) pairs to save.

        Returns:
            The stored Profile, under its normalized name.

        Raises:
            ProfileNameError: name fails normalize_profile_name's rules.
            ProfileStorageError: profiles.json could not be written, OR
                could not be read in the first place -- since this method
                starts from load_all(), a damaged, oversized or
                newer-version file stops the save before anything is
                written, rather than being silently replaced (prohibition:
                a save can never destroy profiles it could not parse).
        """
        normalized = normalize_profile_name(name)
        profiles = {profile_name_key(profile.name): profile for profile in self.load_all()}
        stored = Profile(
            name=normalized, attributes=frozenset(tuple(pair) for pair in attributes)
        )
        profiles[profile_name_key(normalized)] = stored
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
        ordered = sorted(profiles, key=lambda profile: (profile_name_key(profile.name), profile.name))
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
            try:
                fd = os.open(
                    tmp_path,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0),
                    0o600,
                )
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


def missing_attributes(
    profile_attributes: Iterable[AttributePair], available_pairs: Iterable[AttributePair]
) -> FrozenSet[AttributePair]:
    """Return which of profile_attributes are absent from available_pairs (D-06).

    Parameters:
        profile_attributes: The loaded profile's checked (category,
            attribute) pairs -- the spec sheet being evaluated.
        available_pairs: Every (category, attribute) the CURRENT comparison
            actually has a row for. Callers MUST flatten this from the
            current result's core.comparator.attribute_catalog(result), never
            from gui.attribute_picker.AttributePicker._known -- that set is a
            sticky superset across comparison runs (RESEARCH Pitfall 1) and
            comparing against it would undercount items genuinely missing
            from the files currently loaded. This function takes no Catalog
            type dependency, so core stays independent of the picker.

    Returns:
        The subset of profile_attributes with no matching entry in
        available_pairs, as a frozenset. Empty when every profile_attributes
        item was found. Accepts a list or a set for either argument; neither
        input is mutated.
    """
    available = frozenset(available_pairs)
    return frozenset(pair for pair in profile_attributes if pair not in available)
