# Phase 3: Compare Profiles - Research

**Researched:** 2026-10-04
**Domain:** Local JSON persistence of a named attribute-selection set, surfaced through a PySide6 toolbar in the existing Attributes side panel
**Confidence:** MEDIUM (core persistence design is straightforward and grounded in the actual codebase; the UI-wiring pitfalls are cross-checked against official Qt docs, but no Context7/MCP doc tool was available this session, so several findings rely on WebSearch results or training knowledge and are tagged accordingly)

## Summary

Phase 3 adds exactly one capability: save the Attributes panel's currently-checked `(category, attribute)` set under a name, and reload it later — replacing whatever is currently checked (D-03) — against a possibly unrelated fixture pair (the "spec sheet for a substitute fixture" workflow, D-01). CSV export (EXPORT-01/EXPORT-02) is confirmed out of scope (REQUIREMENTS.md, 03-CONTEXT.md D-08) and must not be planned.

The data this phase persists already exists in-memory as `AttributePicker.checked_attributes() -> FrozenSet[Tuple[str, str]]` (`src/gdtf_comparer/gui/attribute_picker.py:132-134`, read this session). Nothing new needs to be invented for *what* to save — only *where* to put it (a small JSON file in a per-user directory), *how* to write it safely (atomic replace, not a naive overwrite), and *how* to wire four new toolbar actions (load/save/rename/delete) into the existing Attributes panel and its established `selection_changed` → `_apply_attribute_selection()` signal chain (`main_window.py:209`, `:423-433`, read this session).

**Primary recommendation:** Add a new `core/profile_repository.py` module (zero Qt imports, mirrors the existing `FixtureRepository` shape in `core/repository.py`) that stores every profile in a single JSON file, keyed by name, written via a temp-file + `os.replace()` atomic swap — no new third-party dependency. Add one new `AttributePicker.set_checked()` method (replacement semantics, D-03) and one small pure function to compute D-06's "N of M spec items not found" count. Wire four widgets (a `QComboBox` + `QPushButton` "Save…" + a `QToolButton` "Manage" menu with Rename/Delete) into the toolbar row D-07 specifies, directly above the existing `AttributePicker` inside `attributes_layout`.

## User Constraints

<user_constraints>
### Locked Decisions (verbatim from 03-CONTEXT.md)

- **D-01:** A "compare profile" is a reusable *spec sheet* of required properties (e.g. color mixing, zoom, max weight, power draw) — not tied to one fixture type. The user's real use case: they know they need certain properties out of a fixture (e.g. starting from a reference like a "MAC Aura XB"), and they reuse that same spec-sheet checklist against completely unrelated candidate fixtures from other manufacturers (e.g. an "R2X Wash") to see at a glance whether a substitute measures up — replacing back-and-forth email with a vendor. This is the primary use case, not a rare edge case — profiles will routinely be loaded against fixtures with a very different attribute catalog than whatever fixture the profile was originally saved from.
- **D-02:** Saved profiles are picked for reload via a dropdown directly in the Attributes side panel (not a separate "Open Profile" dialog).
- **D-03:** Loading a profile **replaces** the currently checked attributes entirely — it does not merge/add onto whatever was already checked. Matches the "pick a spec sheet and run from scratch" workflow.
- **D-04:** Saving a profile under a name that's already in use asks for confirmation before overwriting (not silent overwrite, not a hard block).
- **D-05:** Rename and delete of saved profiles are **in scope for this phase** (not deferred) — the user wants to clean up/update spec sheets over time (e.g. "Moving Head Spec" changing as requirements evolve).
- **D-06:** When a loaded profile's saved properties don't exist on either file in the *current* comparison (i.e., neither the target nor any comparison file has that attribute at all, so no row appears), the app must tell the user explicitly — e.g. a status-bar message like "2 of 6 spec items weren't found in these files." Silently dropping unmatched spec items without telling the user was explicitly rejected: since the user is making go/no-go sourcing decisions from this, they need to know when part of their checklist wasn't actually evaluated, not just see a shorter list and assume everything checked out fine.
- **D-07:** Save and Manage (rename/delete) controls for profiles sit in the same compact toolbar row at the top of the Attributes side panel, alongside the load dropdown — one consolidated location for all profile actions, consistent with D-02's placement for loading.
- **D-08 (Scope Flag, RESOLVED):** CSV export (EXPORT-01/EXPORT-02) is DROPPED from this phase. Do not plan or implement any export/CSV work. The conditional answers gathered about CSV format are historical only and must not be acted on.

### Claude's Discretion (verbatim from 03-CONTEXT.md)

- Exact CSV column layout, file naming convention, and default save location, contingent on the Scope Flag above being resolved in favor of keeping export. **(Moot — export is dropped; nothing to decide here.)**
- Visual/layout details of the profile toolbar row (icon vs. text buttons, exact dropdown width, how "N profiles" are listed when many exist).

### Deferred Ideas (OUT OF SCOPE — verbatim from 03-CONTEXT.md)

- **Red/Yellow/Green acceptability rating:** instead of (or alongside) binary "matches/doesn't match," rate each differing property as Red (fails outright), Yellow (different but acceptable, e.g. "5% over on max weight"), or Green (direct match). Explicitly a future-phase idea — requires tolerance/acceptability rules per attribute that don't exist anywhere in the app today.
</user_constraints>

## Phase Requirements

<phase_requirements>
| ID | Description | Research Support |
|----|-------------|------------------|
| ATTR-03 | User can save/name a subset of selected attributes as a reusable "compare profile" and reload it for future comparisons | Standard Stack (JSON persistence design), Architecture Patterns (ProfileRepository, AttributePicker.set_checked), Code Examples, Common Pitfalls (D-03 replace-not-merge, D-06 missing-attribute detection, combo signal choice) |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.7+ core app logic (actual `pyproject.toml` declares `requires-python = ">=3.11"` [VERIFIED: pyproject.toml:9] — the CLAUDE.md "3.7+" figure is stale/aspirational; plan against the actual 3.11+ floor already in the repo).
- No external runtime beyond what's already a dependency; "pip (implicit — no lockfile or requirements.txt present)" and "minimal third-party dependencies present" are explicit documented conventions — any new dependency should be justified, not added for convenience.
- GUI framework is PySide6 (the repo has already moved off Tkinter per Phase 1 — CLAUDE.md's "tkinter" framework line is stale project documentation; actual dependency is `PySide6==6.11.2` [VERIFIED: pyproject.toml:11]).
- pytest is the test runner (`pytest==9.1.1`, `pytest-qt==4.5.0` [VERIFIED: pyproject.toml:17-19]); tests live under `tests/core/` and `tests/gui/`, mirroring `src/gdtf_comparer/core/` and `src/gdtf_comparer/gui/`.
- Error handling convention: typed, specific exception classes with a `user_message`/friendly-reason property, never raw tracebacks shown to the user (`core/errors.py`, read this session — `GDTFError.user_message` pattern).
- Snake_case functions/variables, PascalCase classes, docstrings with Parameters/Returns sections, comments that explain intent not mechanism — all directly visible in every core/gui file read this session and should be matched by any new code.
- Core/GUI separation is an explicit, named architectural decision (D-16, Phase 1): `core/` must have zero Qt imports. This governs where profile-persistence logic goes (see Architecture Patterns).

## Architectural Responsibility Map

> This is a single-process desktop app, not a multi-tier web app — "tiers" below are adapted to this project's actual layering (core/business-logic vs. gui/presentation vs. local-file storage), per the existing D-16 core/GUI split.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Save/rename/delete/list named profiles (JSON read/write) | Core (`core/profile_repository.py`) | Storage (one local JSON file) | File I/O and schema must have zero Qt imports (D-16); GUI only calls in and renders the result, exactly like `FixtureRepository`/`compare_files()` today |
| Profile toolbar UI (dropdown, Save, Manage/Rename/Delete) | GUI (`gui/main_window.py` widgets) | — | Pure presentation; D-02/D-07 place it in the existing Attributes side panel toolbar |
| Replacing the checked-attribute set on profile load | GUI (`gui/attribute_picker.py`) | Core (data source: the profile's saved pairs) | Checked-set bookkeeping is already GUI-layer state (Phase 2 decision, `AttributePicker._checked`); core only supplies/consumes the plain `(category, attribute)` data |
| Detecting "N of M spec items not found" (D-06) | Core (pure set comparison) | GUI (status bar message) | The matching logic needs no Qt and is trivially unit-testable; only the final message display touches a widget (`statusBar().showMessage(...)`, same pattern as existing status messages) |

## Standard Stack

### Core

No new runtime dependency is required or recommended for this phase. Everything needed is already a project dependency or in the Python standard library.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `json` (stdlib) | 3.11+ | Profile file serialization | Already the de facto format for small structured config in this ecosystem; no parsing/writing complexity profiles need that `json` doesn't already solve |
| `os`, `tempfile` (stdlib) | 3.11+ | Atomic file replace, per-OS directory resolution | `tempfile.mkstemp()` + `os.replace()` is the standard safe-write idiom [CITED via WebSearch aggregating multiple sources incl. tempfile/os stdlib docs — see Sources]; no library beats stdlib here |
| `PySide6` | 6.11.2 [VERIFIED: pyproject.toml:11] | `QComboBox`, `QPushButton`, `QToolButton`, `QMenu`, `QInputDialog`, `QMessageBox` for the toolbar and confirmation dialogs | Already the project's GUI framework (Phase 1); no new widget-kit dependency needed |

### Supporting

None needed — this phase's scope (save/load/rename/delete a named attribute set) does not require a database, a schema-validation library, or a settings framework.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Hand-rolled 3-way OS directory branch (macOS/Windows/XDG-Linux) | `platformdirs` package | `platformdirs` is the standard, well-known solution to this exact problem — but the **Package Legitimacy Gate flagged it `SUS`** this session (see Package Legitimacy Audit below) and the project's own documented convention is minimal third-party dependencies. For a 3-branch `if`, hand-rolling is lower-risk here than pulling in a flagged new dependency. If the planner prefers `platformdirs` anyway, it must be gated behind a `checkpoint:human-verify` task per the SUS disposition, not installed directly. |
| A single JSON file keyed by profile name | `QSettings` (Qt's built-in key-value store) | `QSettings` would require Qt imports inside the persistence layer, directly violating D-16 ("core has zero Qt imports"). It also stores to the registry on Windows / a plist on macOS, which is less inspectable than a plain JSON file a user could reasonably back up or hand-edit. Rejected for this phase. |
| A single JSON file | One file per profile (filename = profile name) | Using the profile name as a filesystem path component reopens exactly the path-traversal/invalid-filename-character class of problem (Windows reserved chars `\ / : * ? " < > \|`, path traversal via `..`) for no benefit, since nothing requires per-profile files. A single JSON file keyed by a `name` field sidesteps this entirely — see Security Domain. |

**Installation:**
```bash
# No new dependencies to install for this phase.
```

**Version verification:** `PySide6==6.11.2` is already pinned and installed (`pyproject.toml:11`, read this session — no change needed). No new package versions require verification since nothing new is being added.

## Package Legitimacy Audit

> Required whenever this phase installs external packages. This phase does **not** require installing any new package — the table below documents the one candidate package that was evaluated and explicitly **not** adopted, so the disposition is on record for the planner.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|--------------|---------|-------------|
| `platformdirs` | PyPI | Registry lookup reported `publishedAt: 2026-10-03` (one day before this research), which is implausible for a project that has existed since 2017 under the `tox-dev` org — this almost certainly reflects the latest point-release date, not the project's actual age [the discrepancy itself is a direct tool observation this session, not training knowledge] | `null` (seam reported `unknown-downloads`) | `github.com/tox-dev/platformdirs` | **SUS** | **NOT USED** — hand-rolled 3-way OS path branch recommended instead (see Alternatives Considered, Code Examples). If a future planner chooses `platformdirs` over the hand-rolled approach, gate the `pip install` behind a `checkpoint:human-verify` task per the SUS protocol — do not install it un-gated. |

**Packages removed due to `[SLOP]` verdict:** none.
**Packages flagged as suspicious `[SUS]`:** `platformdirs` — not adopted in this research's primary recommendation; see Disposition above if the planner overrides that recommendation.

*Note: `platformdirs` was already present as an installed (likely transitive) package in this project's `.venv` at version 4.9.4 per `pip show`, which further suggests the registry seam's "too-new" signal is a metadata artifact (most likely checking the latest release's publish timestamp rather than first-release date) rather than evidence the package itself is new or untrustworthy. It is not being recommended for adoption regardless, since no new dependency is needed for a problem this small.*

## Architecture Patterns

### System Architecture Diagram

```
User clicks a checkbox in the         User picks a name from the
Attributes panel (existing,           "Profiles" dropdown (NEW)
Phase 2)                                      |
     |                                        v
     v                                 QComboBox.activated
AttributePicker._on_item_changed             |
     |                                        v
     v                          ProfileRepository.load_all()
selection_changed (coalesced)       reads profiles.json (JSON)
     |                                        |
     v                                        v
MainWindow._apply_attribute_      Profile found --> its saved
selection()                        (category, attribute) pairs
     |                                        |
     v                                        v
selection_proxy.set_selected_      AttributePicker.set_checked()
attributes(checked_attributes())   (NEW -- REPLACES _checked, D-03)
     |                                        |
     v                                        v
Table re-filters to checked        selection_changed fires -->
rows (existing)                    same _apply_attribute_selection()
                                    path as a manual click (no new
                                    table-filtering code needed)
                                               |
                                               v
                                    MainWindow compares the loaded
                                    profile's pairs against
                                    attribute_catalog(current_result)
                                    (NEW, pure function) --> if any
                                    pair has no matching catalog
                                    entry, statusBar().showMessage(
                                    "N of M spec items weren't found
                                    in these files.")  (D-06)

Separately: user clicks "Save..."/"Manage > Rename.../Delete" (NEW)
     |
     v
MainWindow prompts (QInputDialog / QMessageBox.question for D-04
overwrite confirm or delete confirm)
     |
     v
ProfileRepository.save()/.rename()/.delete()
     |
     v
Atomic write: tempfile in same dir as profiles.json -> os.replace()
     |
     v
Combo box repopulated from ProfileRepository.load_all() (NEW)
```

### Recommended Project Structure

```
src/gdtf_comparer/
├── core/
│   ├── profile_repository.py   # NEW -- Profile dataclass, ProfileRepository,
│   │                            #        missing_attributes() pure helper
│   ├── errors.py                # EXTEND -- ProfileError, ProfileNotFoundError,
│   │                            #           ProfileStorageError
│   ├── repository.py            # unchanged -- the sibling class this mirrors
│   └── models.py, comparator.py # unchanged
├── gui/
│   ├── attribute_picker.py      # EXTEND -- new set_checked() method
│   └── main_window.py           # EXTEND -- profile toolbar row + handlers
tests/
├── core/
│   └── test_profile_repository.py   # NEW
└── gui/
    └── test_profile_toolbar.py      # NEW
```

### Pattern 1: `ProfileRepository` mirrors `FixtureRepository`'s shape

**What:** A small, single-purpose class with explicit methods (`load_all`, `save`, `rename`, `delete`), raising typed errors from `core/errors.py` on failure, zero Qt imports — exactly the shape `FixtureRepository` already establishes in `core/repository.py` (read this session, `core/repository.py:28-78`).

**When to use:** Any time persistence logic needs to be testable without a running `QApplication` and swappable for tests.

**Example (proposed design — not existing code; derived from reading `core/repository.py:28-78` and `core/errors.py:1-49` this session):**

```python
# core/profile_repository.py
import json
import os
import sys
import tempfile
from dataclasses import dataclass
from typing import FrozenSet, List, Tuple

from gdtf_comparer.core.errors import ProfileNotFoundError, ProfileStorageError

AttributePair = Tuple[str, str]
_SCHEMA_VERSION = 1
_FILE_NAME = "profiles.json"


@dataclass(frozen=True)
class Profile:
    """A named, reusable (category, attribute) selection (D-01, ATTR-03)."""
    name: str
    attributes: FrozenSet[AttributePair]


def _app_data_dir() -> str:
    """Return the per-user app-data directory for this app, hand-rolled
    (Package Legitimacy Audit: platformdirs rejected as SUS; this 3-branch
    check is the standard convention it would otherwise provide)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "GDTF Comparer")


class ProfileRepository:
    """Loads/saves named compare profiles as one JSON file (ATTR-03, D-01..D-05)."""

    def __init__(self, base_dir: str = None) -> None:
        """
        Parameters:
            base_dir: Directory to store profiles.json in. Defaults to the
                OS-appropriate per-user app-data directory. Tests should pass
                a tmp_path here instead of touching the real user profile.
        """
        self._dir = base_dir or _app_data_dir()
        self._path = os.path.join(self._dir, _FILE_NAME)

    def load_all(self) -> List[Profile]:
        """Return every saved profile, or [] if no file exists yet.

        Raises:
            ProfileStorageError: The file exists but is not valid JSON or
                does not match the expected schema -- never raised for a
                merely-missing file.
        """
        if not os.path.exists(self._path):
            return []
        try:
            with open(self._path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return [
                Profile(name=p["name"], attributes=frozenset(tuple(pair) for pair in p["attributes"]))
                for p in data.get("profiles", [])
            ]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ProfileStorageError(
                f"the saved profiles file is corrupted ({type(exc).__name__})."
            ) from exc

    def save(self, name: str, attributes: FrozenSet[AttributePair]) -> None:
        """Create or overwrite (D-04's confirm happens in the GUI, not here) a profile."""
        profiles = {p.name: p for p in self.load_all()}
        profiles[name] = Profile(name=name, attributes=attributes)
        self._write_all(profiles.values())

    def rename(self, old_name: str, new_name: str) -> None:
        profiles = {p.name: p for p in self.load_all()}
        if old_name not in profiles:
            raise ProfileNotFoundError(f"no saved profile named '{old_name}'.")
        profile = profiles.pop(old_name)
        profiles[new_name] = Profile(name=new_name, attributes=profile.attributes)
        self._write_all(profiles.values())

    def delete(self, name: str) -> None:
        profiles = {p.name: p for p in self.load_all()}
        if name not in profiles:
            raise ProfileNotFoundError(f"no saved profile named '{name}'.")
        del profiles[name]
        self._write_all(profiles.values())

    def _write_all(self, profiles) -> None:
        os.makedirs(self._dir, exist_ok=True)
        payload = {
            "version": _SCHEMA_VERSION,
            "profiles": [
                {"name": p.name, "attributes": [list(pair) for pair in sorted(p.attributes)]}
                for p in profiles
            ],
        }
        # Atomic write (Common Pitfalls #2): temp file in the SAME directory
        # as the target, then os.replace() -- never open(path, "w") directly.
        fd, tmp_path = tempfile.mkstemp(dir=self._dir, suffix=".json.tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, indent=2)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, self._path)
        except OSError as exc:
            raise ProfileStorageError(f"could not save profiles ({type(exc).__name__}).") from exc
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


def missing_attributes(
    profile_attributes: FrozenSet[AttributePair], available_pairs: FrozenSet[AttributePair]
) -> FrozenSet[AttributePair]:
    """Return which of profile_attributes are absent from available_pairs (D-06).

    Parameters:
        profile_attributes: The loaded profile's saved (category, attribute) set.
        available_pairs: Every (category, attribute) the CURRENT comparison
            result actually has a row for (flatten core.comparator.attribute_catalog(result)
            at the call site -- this function takes no Catalog type dependency).

    Returns:
        The subset of profile_attributes with no matching row in the current
        comparison. Empty when every saved item was found.
    """
    return frozenset(pair for pair in profile_attributes if pair not in available_pairs)
```

### Pattern 2: `AttributePicker.set_checked()` — replacement, not merge (D-03)

**What:** A new method on the existing `AttributePicker` that wholesale-replaces `_checked`, re-renders every currently-rendered leaf's checkbox state, and fires the existing coalesced `selection_changed` signal — so `MainWindow._apply_attribute_selection()` (already wired at `main_window.py:209`, read this session) handles the rest without a parallel code path.

**When to use:** Exactly once, from the profile-load handler.

**Example (proposed; builds directly on the verified `set_catalog`/`_on_item_changed` methods at `attribute_picker.py:74-130` and `:213-230`, read this session):**

```python
def set_checked(self, pairs: FrozenSet[AttributePair]) -> None:
    """Replace the checked set wholesale (D-03: profile load replaces, never merges).

    Parameters:
        pairs: The (category, attribute) pairs to check. Every pair not in
            this set becomes unchecked, including anything previously
            checked by the user or a prior profile load.

    A pair not yet present in the current tree (i.e. not in self._known)
    is still recorded in self._checked -- set_catalog()'s existing
    "pair already known keeps its state" bookkeeping means it will render
    checked automatically the first time a future comparison's catalog
    includes it, with no extra plumbing needed here.

    Emits selection_changed via the same coalescing timer as a user click,
    exactly once, so this drives the identical downstream path as manual
    checkbox edits.
    """
    self._checked = set(pairs)
    self.tree.blockSignals(True)
    try:
        for section_index in range(self.tree.topLevelItemCount()):
            section = self.tree.topLevelItem(section_index)
            for child_index in range(section.childCount()):
                leaf = section.child(child_index)
                pair = tuple(leaf.data(0, _PAYLOAD_ROLE))
                leaf.setCheckState(
                    0, Qt.CheckState.Checked if pair in self._checked else Qt.CheckState.Unchecked
                )
    finally:
        self.tree.blockSignals(False)
    self._emit_timer.start()
```

### Pattern 3: Profile toolbar row in `create_widgets()`

**What:** A `QHBoxLayout` with a `QComboBox` (profile picker), `QPushButton` "Save…", and a `QToolButton` "Manage" with a popup `QMenu` (Rename…/Delete), inserted into `attributes_layout` immediately above `self.attribute_picker` — matching D-02 (dropdown in the Attributes panel) and D-07 (Save + Manage in the same row).

**Example (proposed; attaches to the verified `attributes_layout`/`self.attribute_picker` construction at `main_window.py:204-209`, read this session):**

```python
# Inside create_widgets(), right before `self.attribute_picker = AttributePicker(...)`:
profile_toolbar = QHBoxLayout()
self.profile_combo = QComboBox(self.attributes_group)
self.profile_combo.addItem(PROFILE_PLACEHOLDER)  # non-selectable "— Load profile —"
self.profile_combo.activated.connect(self._load_selected_profile)
profile_toolbar.addWidget(self.profile_combo, 1)

self.save_profile_button = QPushButton("Save…", self.attributes_group)
self.save_profile_button.clicked.connect(self._save_profile)
profile_toolbar.addWidget(self.save_profile_button)

self.manage_profile_button = QToolButton(self.attributes_group)
self.manage_profile_button.setText("Manage")
self.manage_profile_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
manage_menu = QMenu(self.manage_profile_button)
manage_menu.addAction("Rename…", self._rename_selected_profile)
manage_menu.addAction("Delete", self._delete_selected_profile)
self.manage_profile_button.setMenu(manage_menu)
profile_toolbar.addWidget(self.manage_profile_button)

attributes_layout.addLayout(profile_toolbar)
```

### Anti-Patterns to Avoid

- **Connecting profile-load to `currentIndexChanged` instead of `activated`:** `currentIndexChanged`/`currentTextChanged` fire on *programmatic* changes too, so repopulating the combo after a save/rename/delete would silently re-trigger a profile load and stomp the user's just-saved selection. Use `activated` (fires only on user interaction) [CITED: doc.qt.io/qtforpython-6/PySide6/QtWidgets/QComboBox.html — surfaced via WebSearch this session].
- **Using the profile name as a filename:** opens path-traversal / invalid-filename-character problems on no benefit. Store all profiles in one JSON file keyed by a `name` field instead (see Security Domain).
- **`open(path, "w")` directly over an existing profiles.json:** a crash or power loss mid-write leaves a truncated, unparseable JSON file and the user loses every saved profile, not just the one being edited. Always write to a temp file in the same directory, then `os.replace()`.
- **Merging instead of replacing on profile load:** D-03 explicitly rejects merge semantics — `set_checked()` must assign (`self._checked = set(pairs)`), never union.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic file replace | A custom "write new content, then rename" without same-directory temp file + `os.replace` | `tempfile.mkstemp(dir=same_dir)` + `os.replace()` (stdlib) | A naive version risks writing the temp file to a different filesystem (breaking atomicity) or using `os.rename`, which does not guarantee an atomic overwrite on Windows [CITED via WebSearch aggregating multiple sources — see Sources] |
| Confirmation dialogs (D-04 overwrite, D-05 delete) | A custom modal `QWidget` | `QMessageBox.question(...)` | The codebase already has an established `QMessageBox` pattern for exactly this (`main_window.py:558-574`, read this session, `_show_error`) — reuse the same style/icon conventions for Yes/No confirmations instead of inventing a new one |

**Key insight:** Nothing in this phase is a "deceptively complex" problem that needs a dedicated library — it's a small, fully-local, single-user JSON file with no concurrent writers and no untrusted input. The risk in this phase is entirely in *wiring* (Qt signal choice, replace-vs-merge semantics, status-message timing), not in needing unbuilt infrastructure.

## Common Pitfalls

### Pitfall 1: Checking D-06's "not found" count against the wrong catalog

**What goes wrong:** `AttributePicker._known` is a *sticky* superset that persists across comparison runs (`attribute_picker.py:89-95`, read this session: "A pair already known keeps the user's prior choice, including one missing from this catalog"). Comparing a loaded profile's pairs against `self.attribute_picker._known` (or anything picker-internal) instead of the **current** `attribute_catalog(result)` will undercount "not found" items, since `_known` can contain attributes from a *previous* comparison run that aren't in the fixture pair currently loaded.

**Why it happens:** The picker's sticky-known-set behavior is correct and desired for Phase 2's use case (don't lose a user's prior checkbox state across reruns) but is the wrong data source for D-06, which is specifically about *this comparison's* fixture pair.

**How to avoid:** Compute the "available" set fresh from `core.comparator.attribute_catalog(result)` (flattened to a `Set[(category, attribute)]`) at the moment a profile is loaded, not from any picker-internal state.

**Warning signs:** A "spec items not found" count that stays the same (or shrinks incorrectly) across different comparison runs with the same profile loaded.

### Pitfall 2: No comparison has run yet when a profile is loaded

**What goes wrong:** If the user loads a profile before ever clicking "Run Comparison," `self.table_model.result()` is `None` and there is no `attribute_catalog()` to check against — so there's nothing to report. (D-06 specifically describes counting against "either file in the *current* comparison," which does not exist yet in this state.)

**Why it happens:** The profile toolbar (D-02/D-07) is always visible in the Attributes panel, with no stated gating on "only after a comparison has run" — but `AttributePicker.set_catalog()` has not been called yet, so the tree is empty and the loaded profile's checkboxes have nothing to render against.

**How to avoid:** `set_checked()` still works correctly in this state (it just sets `_checked` with no tree rows to paint yet); the planner should decide explicitly whether to (a) skip the D-06 message entirely when `result is None` and let the normal `NO_ATTRIBUTES_SELECTED_MESSAGE`-style status stand once a comparison does run, or (b) show a distinct one-time message like "Profile loaded — run a comparison to see which items match." Document whichever is chosen; don't leave it implicit.

**Warning signs:** A D-06 message that reports "N of N not found" (100%) immediately after loading a profile with no comparison run yet, confusing the user into thinking the profile is entirely useless.

### Pitfall 3: Repopulating the combo box triggers an unwanted reload

See Anti-Patterns above (`activated` vs `currentIndexChanged`). Specifically: after `ProfileRepository.save()`/`.rename()`/`.delete()`, the combo must be repopulated (new/changed/removed name), and that repopulation itself must not fire the load handler. Using `activated` instead of `currentIndexChanged` for the load connection sidesteps this without needing `blockSignals()` gymnastics around the repopulation code.

### Pitfall 4: Using the profile name unsanitized as a dict/JSON key is fine; as a filename is not

**What goes wrong:** If a future iteration splits storage into one-file-per-profile, a name like `"Moving Head / Spec"` or `"CON..profile"` becomes a filesystem hazard (path separator injection, Windows-reserved device names).

**How to avoid:** This phase's design (single JSON file, name is just a dict/field value) makes this a non-issue by construction — keep it that way; do not introduce per-profile files without re-deriving a filename-sanitization story.

## Code Examples

See **Architecture Patterns** above for the full proposed `ProfileRepository`, `AttributePicker.set_checked()`, and toolbar-wiring examples — all derived directly from the actual, verified shapes of `core/repository.py`, `core/errors.py`, `gui/attribute_picker.py`, and `gui/main_window.py` read this session, not from an external framework example.

### Flattening `attribute_catalog()` for the D-06 check

```python
# In MainWindow, at profile-load time:
from gdtf_comparer.core.comparator import attribute_catalog
from gdtf_comparer.core.profile_repository import missing_attributes

result = self.table_model.result()
if result is not None:
    available = {
        (category, attr)
        for category, attrs in attribute_catalog(result)
        for attr in attrs
    }
    missing = missing_attributes(profile.attributes, available)
    if missing:
        self.statusBar().showMessage(
            f"{len(missing)} of {len(profile.attributes)} spec items weren't found in these files."
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| N/A | N/A | — | This is new functionality with no prior implementation in this codebase to supersede; nothing here is replacing a deprecated pattern. |

**Deprecated/outdated:** None relevant — there is no existing profile-persistence code in this project to deprecate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The hand-rolled per-OS app-data directory convention (macOS `~/Library/Application Support`, Windows `%APPDATA%`, Linux `$XDG_CONFIG_HOME` or `~/.config`) is correct and sufficient | Code Examples, `_app_data_dir()` | Low — this is extremely standard OS convention knowledge, but was not verified via an official source this session (WebFetch to python docs timed out; no Context7/MCP doc tool was available in this session's toolset). If wrong, profiles would save to an unexpected location — annoying but not destructive, and easy to fix in review. |
| A2 | `os.replace()` is atomic on both POSIX and Windows when the temp file is on the same filesystem as the target | Standard Stack, Don't Hand-Roll, Pitfall "atomic file replace" | Low — this is well-established Python stdlib behavior repeated across every source WebSearch surfaced this session, but could not be confirmed against the official `docs.python.org` page directly (fetch timed out). If subtly wrong on some platform/filesystem combination, a crash mid-save could corrupt `profiles.json` — mitigated by the try/except around the write path already in the proposed design. |
| A3 | `QComboBox.activated` fires only on user interaction, not on programmatic `setCurrentIndex`/repopulation | Anti-Patterns, Pitfall 3 | Low — confirmed by a WebSearch result surfacing the official `doc.qt.io` page's own description, but the classify-confidence seam still rates WebSearch-sourced findings LOW this session (no MCP doc tool was available to query Qt docs directly). If wrong, repopulating the combo after save/rename/delete would need explicit `blockSignals()` guarding instead. |
| A4 | `platformdirs`'s SUS verdict (publish date "2026-10-03", one day before this research) is a registry-metadata artifact (latest-release date, not project age) rather than a genuine legitimacy concern | Package Legitimacy Audit | Low — this project is not being adopted regardless, so a wrong read of *why* it's SUS has no implementation impact; it only affects how strongly the "don't adopt platformdirs" recommendation should be worded if a future planner reconsiders it. |

## Open Questions

1. **Where exactly should the D-06 "N of M not found" message live relative to the existing `_show_result_status()` precedence chain?**
   - What we know: `_show_result_status()` already has an established precedence order (no-attributes-selected > no-differences > normal summary, `main_window.py:451-477`, read this session) for *persistent* state that gets recomputed on every selection/toggle change.
   - What's unclear: D-06's message is event-triggered (fires once, at the moment of profile load) rather than a function of ongoing state — it doesn't fit cleanly into `_show_result_status()`'s recompute-every-time model without being immediately overwritten by the next `_apply_attribute_selection()` call that profile-load itself triggers (since `set_checked()` fires `selection_changed` → `_apply_attribute_selection()` → `_show_result_status()`).
   - Recommendation: Show the D-06 message via a direct `self.statusBar().showMessage(...)` call made *after* the profile-load handler's call into `_apply_attribute_selection()` completes (so it overwrites, not gets overwritten by, the routine status), OR special-case it as a new highest-precedence branch inside `_show_result_status()` that only applies immediately after a load (e.g., a short-lived instance flag cleared on the next selection change). The planner should pick one explicitly rather than let the two status-setting calls race.

2. **Should Save/Manage controls be disabled before any comparison has run?**
   - What we know: The Attributes panel toolbar is always visible per D-02/D-07; before a comparison runs, `AttributePicker.checked_attributes()` returns whatever defaults were seeded (or an empty set if no catalog has ever loaded).
   - What's unclear: 03-CONTEXT.md doesn't address whether "Save" should be allowed to persist an empty/placeholder selection before the user has ever run a comparison.
   - Recommendation: Allow it (simplest, least surprising) — an empty-attribute profile is a valid (if useless) saved state and the user can always re-save it later; don't add a gating rule not requested by the user.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-qt 4.5.0 [VERIFIED: pyproject.toml:17-19] |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["src"]`, `qt_api = "pyside6"`) [VERIFIED: pyproject.toml:21-26] |
| Quick run command | `python -m pytest tests/core/test_profile_repository.py tests/gui/test_profile_toolbar.py -x` |
| Full suite command | `python -m pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|--------------------|--------------|
| ATTR-03 | Save checked attributes under a name; file round-trips | unit | `pytest tests/core/test_profile_repository.py::test_save_and_load_round_trip -x` | ❌ Wave 0 |
| ATTR-03 | Loading a profile replaces (not merges) the checked set (D-03) | gui | `pytest tests/gui/test_profile_toolbar.py::test_load_profile_replaces_checked_set -x` | ❌ Wave 0 |
| ATTR-03 | Saving over an existing name prompts for confirmation (D-04) | gui | `pytest tests/gui/test_profile_toolbar.py::test_save_existing_name_confirms_overwrite -x` | ❌ Wave 0 |
| ATTR-03 | Rename and delete update the saved set and the dropdown (D-05) | unit + gui | `pytest tests/core/test_profile_repository.py::test_rename_and_delete -x` | ❌ Wave 0 |
| ATTR-03 | A profile pair absent from the current comparison's catalog is reported (D-06) | unit | `pytest tests/core/test_profile_repository.py::test_missing_attributes -x` | ❌ Wave 0 |
| ATTR-03 | A corrupted `profiles.json` raises a typed, friendly error instead of crashing | unit | `pytest tests/core/test_profile_repository.py::test_corrupted_file_raises_typed_error -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** quick run command above
- **Per wave merge:** full suite command
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/core/test_profile_repository.py` — covers ATTR-03's save/load/rename/delete/missing-attribute/corrupted-file behaviors; use `tmp_path` (built-in pytest fixture, no new fixture infrastructure needed) as `ProfileRepository(base_dir=str(tmp_path))` so tests never touch the real user profile directory
- [ ] `tests/gui/test_profile_toolbar.py` — covers the toolbar wiring (D-02/D-03/D-04/D-07) using the existing `qtbot` fixture (pytest-qt, already a dev dependency) the same way every other `tests/gui/*.py` file does
- [ ] No new shared fixtures needed — `tmp_path` and `qtbot` are both already available project-wide

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | Single-user local desktop app, no auth surface added by this phase |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | No multi-user access boundaries; relies on OS file permissions like every other file this app already reads/writes |
| V5 Input Validation | Yes | Profile name (free text from `QInputDialog`): validate non-empty/trimmed before calling `save`/`rename`; no filesystem-character restriction needed because the name is never used as a path component (single-JSON-file design) |
| V6 Cryptography | No | No secrets stored; profiles contain only attribute-category/name strings the user already sees on screen |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Path traversal / invalid-filename injection via profile name | Tampering | Never use the profile name as a filesystem path component — store all profiles in one JSON file keyed by a `name` field (this phase's recommended design already does this) |
| Corrupted/malformed `profiles.json` crashing the app on next launch | Tampering / Denial of Service (local) | `ProfileRepository.load_all()` catches `json.JSONDecodeError`/`KeyError`/`TypeError` and raises a typed `ProfileStorageError` with a friendly message, mirroring the existing `GDTFError` pattern — never let a bad file crash startup |
| Partial write leaving `profiles.json` truncated after a crash mid-save | Tampering | Atomic temp-file + `os.replace()` write (see Standard Stack, Don't Hand-Roll) |

## Sources

### Primary (HIGH confidence)
- None this session — no Context7/MCP documentation tool was available in this agent's toolset (the research-plan seam returned a `context7` provider for the `platformdirs` question, but no corresponding `mcp__context7__*` tool was exposed to invoke it).

### Secondary (MEDIUM confidence)
- `/Users/brandon/GDTFComparer/pyproject.toml` (read this session) — verified dependency versions and Python floor
- `/Users/brandon/GDTFComparer/src/gdtf_comparer/core/repository.py`, `core/errors.py`, `core/models.py`, `core/comparator.py` (read this session) — verified existing patterns this phase's design mirrors
- `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/attribute_picker.py`, `gui/main_window.py` (read this session) — verified existing signal chains and widget construction this phase hooks into
- `doc.qt.io/qtforpython-6/PySide6/QtWidgets/QComboBox.html` — surfaced via WebSearch this session; `activated` vs `currentIndexChanged` behavior description cross-checked against training knowledge of documented Qt behavior

### Tertiary (LOW confidence — classify-confidence seam rated websearch provider LOW this session; flagged for planner awareness, not stated as authoritative)
- WebSearch results on atomic JSON writes (tempfile + os.replace pattern) — multiple independent sources agreed, but none was fetched as an official doc page this session (a WebFetch attempt to `docs.python.org` timed out)
- WebSearch results on `platformdirs` package purpose — general package description only; the legitimacy verdict itself came from the `package-legitimacy check` seam (tool-verified), not WebSearch

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependency is needed; the stdlib-only design was derived directly from verified, in-repo code patterns, not external research
- Architecture: HIGH — every new method/class signature is grounded in actually-read source files (`core/repository.py`, `gui/attribute_picker.py`, `gui/main_window.py`), not assumed
- Pitfalls: MEDIUM — the D-03/D-06 pitfalls are grounded in verified code; the Qt-signal pitfall (`activated` vs `currentIndexChanged`) rests on a WebSearch finding the classify-confidence seam rated LOW, despite aligning with well-documented Qt behavior

**Research date:** 2026-10-04
**Valid until:** 2026-11-03 (30 days — nothing in this research depends on a fast-moving ecosystem; PySide6/stdlib behavior here is stable)
