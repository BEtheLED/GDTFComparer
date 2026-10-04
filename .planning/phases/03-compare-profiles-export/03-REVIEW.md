---
phase: 03-compare-profiles-export
reviewed: 2026-10-04T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - src/gdtf_comparer/app.py
  - src/gdtf_comparer/core/errors.py
  - src/gdtf_comparer/core/profile_repository.py
  - src/gdtf_comparer/gui/attribute_picker.py
  - src/gdtf_comparer/gui/main_window.py
  - tests/conftest.py
  - tests/core/test_profile_repository.py
  - tests/gui/test_profile_manage.py
  - tests/gui/test_profile_portability.py
  - tests/gui/test_profile_toolbar.py
  - tests/test_architecture.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-10-04T00:00:00Z
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

This phase adds named compare profiles (save/load/rename/delete) backed by a
single `profiles.json` file (`core/profile_repository.py`), a profile toolbar
and Manage menu in `gui/main_window.py`, and `AttributePicker.set_checked()` /
`_defaults_enabled` to make a profile load a true "replace, never merge"
operation. The persistence layer is unusually careful: atomic same-folder
writes via `os.open(O_EXCL)` + `fsync` + `os.replace`, a versioned schema that
refuses newer-than-known files outright, strict size/UTF-8/shape validation,
and 20+ unit tests covering idempotency, Unicode case-folding, path-safety of
profile names, and crash-injection (`os.replace`/`os.fsync` failures). The GUI
wiring (toolbar, Manage menu, D-06 "spec items not found" status reporting)
is similarly well covered by three end-to-end test files.

No crashes, injection vectors, or data-loss paths were found. The issues below
are all in the "quality/correctness" tier: a validation routine whose
normalized return value is silently discarded on load, two Unicode
control-character validation gaps relative to the module's own stated ASVS
goal, and a few minor display/robustness nits. None of these corrupt stored
data or crash the app; all are concrete, fixable in `core/profile_repository.py`.

## Warnings

### WR-01: Loaded profile names are validated but never actually normalized

**File:** `src/gdtf_comparer/core/profile_repository.py:270-277, 297`

**Issue:** `_parse_payload` calls `normalize_profile_name(name)` purely to
validate (catching `ProfileNameError`), then discards its return value and
builds the `Profile` from the raw, un-normalized `name` string read from JSON:

```python
name = entry.get("name")
...
try:
    normalize_profile_name(name)          # <-- return value discarded
except ProfileNameError:
    raise self._damaged("a profile has an invalid name") from None
...
profiles.append(Profile(name=name, attributes=frozenset(pairs)))   # raw name
```

`normalize_profile_name` trims surrounding whitespace and NFC-normalizes
Unicode form (that's the whole point of its name) -- but none of that is
applied here. A `profiles.json` entry with `"name": "  Spec  "` (valid by the
rules: non-empty after trimming, under 80 chars, no control characters) loads
as a `Profile` whose `.name` is literally `"  Spec  "`, not `"Spec"`. That
string is then shown verbatim in `profile_combo` (the dropdown), in
`RENAME_PROFILE_PROMPT`'s pre-filled default, in `PROFILE_SAVED_TEMPLATE`/
`PROFILE_RENAMED_TEMPLATE` status messages, and -- because `save()`/`rename()`/
`delete()` all round-trip through `load_all()` and re-serialize every
*other* profile unchanged via `_write_all` -- it is written back out
untouched on every subsequent save of any other profile, perpetuating the
un-normalized name forever.

This can't be produced by this app's own GUI today (`save()`/`rename()` both
call `normalize_profile_name()` and use *its* return value correctly), so the
only way to trigger it is a hand-edited or externally-written
`profiles.json` -- but the surrounding module explicitly documents defending
against exactly that case (the whole versioned-schema, size-capped,
shape-validated design exists because "every saved profile lives in one
shared profiles.json" that other tools/versions might touch). Matching
keys (`find`/`get`/`rename`/`delete`) still work correctly since
`profile_name_key()` re-normalizes on every call regardless -- only the
*display* string drifts, but it drifts permanently and silently.

**Fix:** Use the normalized return value:

```python
try:
    name = normalize_profile_name(name)
except ProfileNameError:
    raise self._damaged("a profile has an invalid name") from None
```

### WR-02: Profile names allow Unicode bidi/format control characters

**File:** `src/gdtf_comparer/core/profile_repository.py:79`

**Issue:** `normalize_profile_name`'s own docstring and module header cite
"ASVS V5" as the bar for name validation, and it does block `Cc` (control)
and `Cs` (surrogate) Unicode categories:

```python
if any(unicodedata.category(character) in ("Cc", "Cs") for character in normalized):
    raise ProfileNameError(...)
```

It does not block the `Cf` ("format") category, which includes bidirectional
control characters such as U+202E RIGHT-TO-LEFT OVERRIDE, U+200E/U+200F
directional marks, and zero-width joiners/non-joiners. A profile name
containing these (e.g. crafted into a shared/hand-edited `profiles.json`, or
pasted from an untrusted source into the Save/Rename dialog) can render
misleadingly in the dropdown, the Rename/Delete confirmation dialogs, and
status-bar messages -- the exact "Trojan Source"-style spoofing class ASVS
V5 input-validation guidance is meant to catch. Impact here is limited (this
is a local, single-user JSON file, not a network-shared or multi-tenant
store), but the gap is real and inconsistent with the standard the code
itself invokes.

**Fix:** Extend the blocked-category check to include `Cf`, or more
narrowly strip/reject the specific bidi-control code points:

```python
_BIDI_CONTROL_CHARS = {"‎", "‏", "‪", "‫", "‬", "‭", "‮"}
if any(
    unicodedata.category(character) in ("Cc", "Cs", "Cf")
    or character in _BIDI_CONTROL_CHARS
    for character in normalized
):
    raise ProfileNameError(
        "Profile names can't contain line breaks, tabs, directional marks or other "
        "control characters."
    )
```

### WR-03: Attribute/category pair strings loaded from disk have no character-class validation

**File:** `src/gdtf_comparer/core/profile_repository.py:286-289`

**Issue:** Unlike profile *names* (validated by `normalize_profile_name`,
modulo WR-02), the `(category, attribute)` pair strings read from a saved
profile's `"attributes"` list are checked only for "is a string and is
non-empty":

```python
if not isinstance(category, str) or not category:
    raise self._damaged("unexpected layout")
if not isinstance(attribute, str) or not attribute:
    raise self._damaged("unexpected layout")
```

Nothing rejects embedded control characters (including a literal `"\n"`),
surrogates, or bidi overrides. These strings are later rendered directly as
`QTreeWidgetItem` leaf/section labels in `AttributePicker.set_catalog`
(`gui/attribute_picker.py:113,123`) and joined into the D-06 "spec items not
found" status message (`names=", ".join(attribute for _, attribute in
sorted(missing))` in `main_window.py:605`). A hand-edited or externally
produced `profiles.json` can therefore inject a multi-line or
visually-misleading label into the Attributes tree or status bar. This is a
UI-integrity gap, not a code-execution risk (Qt widgets don't interpret these
as markup), but it is the same validation gap as WR-02, applied to a second
field that the module's own design treats as equally untrusted input (it
already validates shape, size, and name content this strictly for exactly
that reason).

**Fix:** Reuse (or factor out) the same control/format-character check used
for names, e.g. a shared `_is_display_safe(text: str) -> bool` helper called
for `category` and `attribute` alongside the existing non-empty check.

## Info

### IN-01: App-data directory permissions aren't retroactively tightened

**File:** `src/gdtf_comparer/core/profile_repository.py:469`

**Issue:** `os.makedirs(self._dir, mode=0o700, exist_ok=True)` only applies
`mode=0o700` when it actually creates the directory; if `self._dir` already
exists with broader permissions (e.g. created by a different process or a
permissive umask before this app ever ran), `exist_ok=True` leaves its mode
untouched. `profiles.json` itself is still written with `0o600` (verified by
`test_profiles_file_is_owner_only`), so file *contents* stay owner-only
regardless -- this only affects whether other local users can list the
directory's file names.

**Fix:** Optionally `os.chmod(self._dir, 0o700)` after `makedirs` regardless
of whether it already existed, if directory-listing privacy is a stated goal.

### IN-02: A profiles.json deleted mid-read is reported as "damaged" rather than missing

**File:** `src/gdtf_comparer/core/profile_repository.py:187-194`

**Issue:** `load_all()` checks `os.path.exists(self._path)` and returns `[]`
if absent, but if the file is removed by another process between that check
and the subsequent `open()` call, the resulting `FileNotFoundError` is caught
by the generic `except OSError as exc: raise self._damaged(...)` handler,
producing a misleading "...is damaged (FileNotFoundError). It was left
unchanged." message for a file that was simply deleted, not corrupted. Low
probability (requires a second process/instance racing this one) and not
reachable in this app's own single-process flow.

**Fix:** Special-case `FileNotFoundError` in the `except OSError` branch to
return `[]` (treat as "no file") instead of raising `_damaged`.

### IN-03: Renaming a profile to its unchanged name still reports a rename

**File:** `src/gdtf_comparer/gui/main_window.py:823-837`

**Issue:** `ProfileRepository.rename()` correctly no-ops (returns the
existing `Profile`, writes nothing) when the new name normalizes to exactly
the same stored name. `_rename_selected_profile`, however, always shows
`PROFILE_RENAMED_TEMPLATE.format(old=old_name, new=profile.name)` after a
successful call, so confirming the rename dialog with the exact same text
(or a change that normalizes away, e.g. adding only trailing whitespace)
shows "Renamed profile 'Spec' to 'Spec'." in the status bar even though
nothing changed on disk.

**Fix:** Compare `profile_name_key(old_name) == profile_name_key(profile.name)`
and `old_name == profile.name` before choosing the status message; show a
neutral "No change." message (or nothing) when both match exactly.

---

_Reviewed: 2026-10-04T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
