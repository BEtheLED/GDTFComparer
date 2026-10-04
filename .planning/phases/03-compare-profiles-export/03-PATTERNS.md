# Phase 3: Compare Profiles - Pattern Map

**Mapped:** 2026-10-04
**Files analyzed:** 6 (2 new, 4 modified) — CSV export files excluded (out of scope, D-08)
**Analogs found:** 6 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|---------------|
| `src/gdtf_comparer/core/profile_repository.py` (NEW) | service/repository | CRUD + file-I/O | `src/gdtf_comparer/core/repository.py` | exact (same role, same project layer; data flow is CRUD/file-I/O vs. analog's read-only file-I/O — close enough to copy class shape, error-wrapping, and docstring style) |
| `src/gdtf_comparer/core/errors.py` (MODIFIED — add `ProfileError`, `ProfileNotFoundError`, `ProfileStorageError`) | model/utility (typed errors) | request-response (raise/catch) | `src/gdtf_comparer/core/errors.py` (self — extend existing hierarchy) | exact |
| `src/gdtf_comparer/gui/attribute_picker.py` (MODIFIED — add `set_checked()`) | component | event-driven | `src/gdtf_comparer/gui/attribute_picker.py` (self — extend `set_catalog()`'s sibling method) | exact |
| `src/gdtf_comparer/gui/main_window.py` (MODIFIED — profile toolbar + handlers) | controller/component (Qt window) | event-driven + request-response | `src/gdtf_comparer/gui/main_window.py` (self — extend `create_widgets()`, `_apply_attribute_selection()`, `_show_error()`) | exact |
| `tests/core/test_profile_repository.py` (NEW) | test | CRUD | `tests/core/test_repository.py` | exact |
| `tests/gui/test_profile_toolbar.py` (NEW) | test | event-driven | `tests/gui/test_attribute_selection.py` + `tests/gui/test_error_handling.py` (combined pattern — status-bar assertions from the former, dialog-capture from the latter) | role-match (no single existing GUI test file covers both status-bar text and modal-dialog capture, but both patterns individually exist and apply directly) |

## Pattern Assignments

### `src/gdtf_comparer/core/profile_repository.py` (service/repository, CRUD + file-I/O)

**Analog:** `src/gdtf_comparer/core/repository.py` (77 lines, read in full)

**Module docstring pattern** (lines 1-9): opens with a one-line summary of the module's single responsibility, then a short paragraph naming the exact call chain and which requirement IDs/decisions it satisfies. Mirror this for `profile_repository.py`, citing ATTR-03 and D-01..D-06.

**Imports pattern** (lines 11-19):
```python
import io
import os

import pygdtf

from gdtf_comparer.core.errors import GDTFError, GDTFParseError, GDTFValidationError
from gdtf_comparer.core.extract import extract_attributes
from gdtf_comparer.core.hardening import prevalidate_gdtf_document
from gdtf_comparer.core.models import FixtureModel
```
Standard library first, third-party (`pygdtf`) next, then local `gdtf_comparer.core.*` imports absolute (not relative) — this is the project convention every `core/` module follows. `profile_repository.py` needs only stdlib (`json`, `os`, `tempfile`) plus the two new error classes from `core/errors.py` — no third-party import at all (RESEARCH confirms no new dependency).

**Core class-shape pattern** (lines 28-50): a single small class (`FixtureRepository`) with one explicit public method (`load`), a full docstring with Parameters/Returns/Raises sections naming every exception type it can raise and why. `ProfileRepository` must mirror this exactly: explicit `load_all`/`save`/`rename`/`delete` methods, each with a Parameters/Returns/Raises docstring, no hidden state beyond `self._dir`/`self._path` (constructor-injected like `FixtureRepository` takes no constructor args but a sibling pattern — note `ProfileRepository.__init__(self, base_dir=None)` is a deliberate, justified deviation per RESEARCH so tests can inject `tmp_path` instead of touching the real user profile — document this reason in the docstring same as this file documents its design choices in the module docstring).

**Error-wrapping pattern** (lines 67-77):
```python
except GDTFError:
    # Already a typed error (e.g. the stub-name check above) --
    # propagate unchanged so callers see the specific failure.
    raise
except Exception as exc:
    # Anything else from pygdtf/extraction on already-validated bytes
    # is propagated as a typed error so callers can show a friendly
    # message (D-12) instead of an uncaught exception.
    raise GDTFParseError(
        path, f"its GDTF data could not be parsed ({type(exc).__name__})."
    ) from exc
```
Copy this shape for `_write_all()`'s `except OSError as exc: raise ProfileStorageError(...) from exc` and `load_all()`'s `except (json.JSONDecodeError, KeyError, TypeError) as exc: raise ProfileStorageError(...) from exc` — always `raise NewTypedError(...) from exc` (never swallow the original), always lowercase sentence-fragment message interpolating `type(exc).__name__`, never the raw exception repr or a traceback.

---

### `src/gdtf_comparer/core/errors.py` (model/utility, extend in place)

**Analog:** itself, 48 lines, read in full.

**Base-class + subclass pattern** (lines 11-48):
```python
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
```
New profile errors don't have a "failing file path" the same way (profiles aren't a single file on disk from the caller's perspective — the whole JSON store is one file) — so `ProfileError` should be a lighter base, constructed directly with a friendly message string (no `path`/`reason` split needed), still exposing `.user_message` for symmetry with `GDTFError` so `MainWindow._show_error()` can treat both uniformly:
```python
class ProfileError(Exception):
    """Base error for compare-profile persistence failures (ATTR-03)."""

    def __init__(self, message: str) -> None:
        self.user_message = message
        super().__init__(message)

    def __str__(self) -> str:
        return self.user_message


class ProfileNotFoundError(ProfileError):
    """No saved profile exists under the given name."""


class ProfileStorageError(ProfileError):
    """profiles.json could not be read or written (corrupted or OSError)."""
```
Keep subclasses as bare one-line docstrings (no added methods) exactly like `GDTFValidationError`/`GDTFUnsafeFileError`/`GDTFParseError` above.

---

### `src/gdtf_comparer/gui/attribute_picker.py` (component, event-driven — add `set_checked()`)

**Analog:** itself, 230 lines, read in full. Sibling method: `set_catalog()` (lines 74-130).

**Imports already present** (lines 16-21) — no new imports needed; `set_checked()` uses only `Qt`, `self.tree`, and the already-imported `AttributePair` type alias (line 24: `AttributePair = Tuple[str, str]`).

**Signal-blocking + tree-walk pattern** (lines 97-130, `set_catalog`'s tree rebuild under `blockSignals`):
```python
self._rebuilding = True
self.tree.blockSignals(True)
try:
    self.tree.clear()
    for category, attributes in catalog:
        ...
        leaf_item.setCheckState(
            0, Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        )
        ...
finally:
    self.tree.blockSignals(False)
    self._rebuilding = False
```
`set_checked()` reuses this exact `blockSignals(True)/try/finally` shape but walks the *existing* tree (no `self.tree.clear()`, since the catalog/sections are unchanged) — iterate `topLevelItemCount()` / `childCount()` and set each leaf's `checkState()` from membership in the new `pairs` set, per the Pattern 2 code example already fully drafted in 03-RESEARCH.md (Architecture Patterns, lines 340-372) — copy that draft directly; it was derived from this exact file this session.

**Coalesced-emit pattern** (lines 67-70, 230):
```python
self._emit_timer = QTimer(self)
self._emit_timer.setSingleShot(True)
self._emit_timer.setInterval(0)
self._emit_timer.timeout.connect(self.selection_changed.emit)
...
self._emit_timer.start()
```
`set_checked()` must end with `self._emit_timer.start()` (not `self.selection_changed.emit()` directly) — same coalescing mechanism `_on_item_changed` already uses, so a profile load fires `selection_changed` exactly once just like a section-click cascade (verified by `test_section_click_is_one_coalesced_change` in `tests/gui/test_attribute_picker.py:105-123`).

**Public-method docstring convention** (lines 132-134, `checked_attributes()`):
```python
def checked_attributes(self) -> FrozenSet[AttributePair]:
    """Return the currently checked (category, attribute) set."""
    return frozenset(self._checked)
```
Short, single-sentence docstrings for simple accessors; longer Parameters-section docstrings (like `set_catalog`, lines 75-88) for methods with side effects and non-obvious bookkeeping — `set_checked()` falls into the latter category (replacement vs. merge semantics must be documented, per D-03).

---

### `src/gdtf_comparer/gui/main_window.py` (controller/component, event-driven + request-response — add profile toolbar)

**Analog:** itself, 574 lines, read in full. Three distinct sub-patterns apply from three different sections of this same file.

**Imports pattern** (lines 8-45): standard library first (`logging`, `os`, `typing`), then `PySide6.QtCore`/`PySide6.QtWidgets` (alphabetized within the `QtWidgets` import parens), then local `gdtf_comparer.core.*` / `gdtf_comparer.gui.*` absolute imports. New widgets needed (`QComboBox`, `QToolButton`, `QMenu`, `QInputDialog`) get added into the existing `QtWidgets` import block alphabetically; `ProfileRepository`, `ProfileError`/`ProfileNotFoundError`/`ProfileStorageError`, and `missing_attributes` get added to the `gdtf_comparer.core.*` import lines alongside the existing `attribute_catalog`/`ComparisonResult` imports (lines 34-35).

**Widget-construction-in-`create_widgets()` pattern** (lines 201-209, the Attributes panel block):
```python
self.attributes_group = QGroupBox("Attributes", central)
attributes_layout = QVBoxLayout(self.attributes_group)
self.attribute_picker = AttributePicker(self.attributes_group)
attributes_layout.addWidget(self.attribute_picker)
self.attributes_group.setMinimumWidth(220)
self.attribute_picker.selection_changed.connect(self._apply_attribute_selection)
```
The profile toolbar row attaches here, immediately before `self.attribute_picker = AttributePicker(...)` is constructed (per D-02/D-07 placement and RESEARCH Pattern 3's fully-drafted widget code, 03-RESEARCH.md lines 380-402) — copy that draft directly, it targets this exact insertion point. Follow the same `widget = QWidget(parent_group)` / `.clicked.connect(self._handler)` wiring style used for every other button in this file (e.g. `self.run_button = QPushButton("Run Comparison", central); self.run_button.clicked.connect(self.run_comparison)`, lines 167-168).

**Signal-to-handler delegation pattern** (lines 423-433, `_apply_attribute_selection`):
```python
def _apply_attribute_selection(self) -> None:
    """Push the picker's checked set into the selection proxy and refit.

    Connected to AttributePicker.selection_changed, and also called
    directly after on_comparison_ready seeds a fresh catalog (D-03: the
    checked set is the only thing that decides which rows show).
    """
    self.selection_proxy.set_selected_attributes(self.attribute_picker.checked_attributes())
    if self.table_model.result() is not None:
        self._fit_columns_to_contents()
    self._show_result_status()
```
This is the "existing hook" CONTEXT.md's Integration Points section names — a profile-load handler (`_load_selected_profile`) must call `self.attribute_picker.set_checked(profile.attributes)` and let this existing `selection_changed` → `_apply_attribute_selection()` chain do the rest (do not duplicate `set_selected_attributes`/`_fit_columns_to_contents`/`_show_result_status` calls in the new handler). After that chain runs, the D-06 "N of M not found" check runs as an *additional* `self.statusBar().showMessage(...)` call (per RESEARCH's Open Question 1 recommendation: show it after `_apply_attribute_selection()` completes so it is not immediately overwritten by `_show_result_status()`).

**Status-bar messaging pattern** (lines 49-64, module-level message constants + lines 451-477, `_show_result_status`):
```python
NO_ATTRIBUTES_SELECTED_MESSAGE = (
    "No attributes selected. Check attributes in the Attributes panel to show them."
)
...
def _show_result_status(self) -> None:
    """..."""
    result = self.table_model.result()
    if result is None:
        return
    if self.table_model.rowCount() > 0 and self.selection_proxy.rowCount() == 0:
        self.statusBar().showMessage(NO_ATTRIBUTES_SELECTED_MESSAGE)
        return
    ...
    self.statusBar().showMessage(
        f"Compared {len(result.comparisons)} file(s) against {result.target.file_name}"
    )
```
Module-level `UPPER_SNAKE_CASE` string constants for every user-facing status message (never inline string literals scattered through handler methods) — add a new constant for D-06's message template, e.g. a format string built at the call site (see 03-RESEARCH.md's flattening example, lines 456-475) rather than a fixed constant, since it interpolates `len(missing)`/`len(profile.attributes)`.

**Error-dialog pattern** (lines 558-574, `_show_error`):
```python
def _show_error(self, message: str) -> None:
    """Show a friendly modal, plain-text error dialog.
    ...
    """
    box = QMessageBox(
        QMessageBox.Icon.Warning,
        "GDTF Comparer",
        message,
        QMessageBox.StandardButton.Ok,
        self,
    )
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.exec()
```
Reuse `self._show_error(...)` as-is for any `ProfileStorageError`/`ProfileNotFoundError` caught from `ProfileRepository` calls (same pattern RESEARCH's "Don't Hand-Roll" table recommends) — do not build a second error-dialog helper. For D-04's overwrite-confirm and D-05's delete-confirm, there is **no existing analog in this codebase** (`QMessageBox.question` and `QInputDialog` are not used anywhere yet — confirmed via `grep -rn "QMessageBox.question\|QInputDialog" src/ tests/` returning no hits) — follow `_show_error`'s *construction* conventions (explicit `QMessageBox.Icon`, app-name title `"GDTF Comparer"`, `Qt.TextFormat.PlainText`) but use `QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No` instead of `Ok`, and compare the return value against `QMessageBox.StandardButton.Yes`, per Qt's standard `QMessageBox.question(...)` convenience-constructor idiom (RESEARCH's Don't Hand-Roll table, confirmed no in-repo precedent exists — net-new pattern, document its shape as a small private helper e.g. `_confirm(message) -> bool` beside `_show_error` so both dialog-trigger paths look the same to a future reader).

---

### `tests/core/test_profile_repository.py` (test, CRUD)

**Analog:** `tests/core/test_repository.py` (141 lines, read in full)

**Module docstring + test-function pattern** (lines 1-6, 20-30):
```python
"""Unit tests for core.repository: loader error paths, encoding, no-disk-write.

FixtureRepository.load() = prevalidate_gdtf() -> pygdtf on validated bytes ->
typed errors (RELI-01, D-12). These tests exercise the loader end to end,
including compare_files()'s all-or-nothing batch behavior (D-15).
"""
...
def test_load_valid_gdtf(make_gdtf):
    path = make_gdtf("valid.gdtf", name="Test Fixture", manufacturer="Test Co", weight=42.5)
    repo = FixtureRepository()

    model = repo.load(str(path))

    assert model.name == "Test Fixture"
    ...
```
Module docstring states the module's one-line responsibility + which requirement IDs it covers. Each test: construct the object fresh (no shared fixture-scoped repo instance), arrange/act/assert blank-line separation, one behavior per test. `test_profile_repository.py` should use `ProfileRepository(base_dir=str(tmp_path))` (built-in pytest fixture, per RESEARCH's Wave 0 Gaps — never touch the real user profile dir in tests) in place of `make_gdtf`.

**Typed-error assertion pattern** (lines 33-44, `test_invalid_zip_raises`):
```python
def test_invalid_zip_raises(tmp_path):
    path = tmp_path / "invalid.gdtf"
    path.write_text("not a zip")
    repo = FixtureRepository()

    with pytest.raises(GDTFValidationError) as exc_info:
        repo.load(str(path))

    message = str(exc_info.value)
    assert message.startswith("Could not open 'invalid.gdtf':")
    assert "Traceback" not in message
```
Copy this `pytest.raises(SpecificErrorType) as exc_info` + assert on `str(exc_info.value)` shape for `test_corrupted_file_raises_typed_error` (write a hand-corrupted `profiles.json` to `tmp_path`, assert `ProfileStorageError` raised, message does not contain "Traceback").

**monkeypatch-the-module pattern** (lines 75-87, `test_pygdtf_failure_wrapped`):
```python
def test_pygdtf_failure_wrapped(make_gdtf, monkeypatch):
    path = make_gdtf("valid.gdtf")

    def _boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(repository_module.pygdtf, "FixtureType", _boom)
    repo = FixtureRepository()

    with pytest.raises(GDTFParseError) as exc_info:
        repo.load(str(path))

    assert isinstance(exc_info.value.__cause__, RuntimeError)
```
Useful if a test needs to force an `OSError` out of `os.replace`/`tempfile.mkstemp` to exercise `ProfileStorageError`'s write-failure path — `monkeypatch.setattr(profile_repository_module.os, "replace", _boom)` mirrors this exactly, and the `assert isinstance(exc_info.value.__cause__, RuntimeError)` check confirms the `raise ... from exc` chain is preserved (don't lose the `from exc`).

---

### `tests/gui/test_profile_toolbar.py` (test, event-driven)

**Analogs:** `tests/gui/test_attribute_selection.py` (status-bar assertions) + `tests/gui/test_error_handling.py` (modal-dialog capture)

**Status-bar assertion pattern** (`tests/gui/test_attribute_selection.py:123-142`):
```python
def test_no_attributes_checked_shows_empty_table_and_hint(qtbot, make_gdtf):
    ...
    assert (
        window.statusBar().currentMessage()
        == main_window_module.NO_ATTRIBUTES_SELECTED_MESSAGE
    )
```
Use `window.statusBar().currentMessage() == <expected text or module constant>` directly — never mock `showMessage`. Apply this for D-06's "N of M spec items weren't found" assertion after loading a profile with some pairs missing from the current catalog.

**Dialog-capture fixture pattern** (`tests/gui/test_error_handling.py:23-33`):
```python
@pytest.fixture
def capture_dialogs(monkeypatch):
    """Monkeypatch QMessageBox.exec to record (text, textFormat) and return 0."""
    dialogs: List[Tuple[str, "Qt.TextFormat"]] = []

    def _fake_exec(self):
        dialogs.append((self.text(), self.textFormat()))
        return 0

    monkeypatch.setattr(QMessageBox, "exec", _fake_exec)
    return dialogs
```
Reuse for D-04 (save-over-existing-name confirm) and D-05 (delete confirm) tests: monkeypatch `QMessageBox.exec` to return a controlled value (e.g. patch to return `QMessageBox.StandardButton.Yes`/`No` rather than always `0`, since these are Yes/No dialogs not the Ok-only `_show_error` dialogs this fixture was written for — extend the fixture or add a sibling `_fake_exec` returning the desired `StandardButton` per test). For `QInputDialog.getText` (profile name entry on Save/Rename), monkeypatch `QInputDialog.getText` directly (`monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("My Profile", True))`) — same monkeypatch-the-static-method idiom, no existing in-repo precedent for `QInputDialog` specifically but the same technique already proven for `QMessageBox.exec`.

**Widget-construction test setup pattern** (`tests/gui/test_attribute_picker.py:14-17`, `_make_picker` helper):
```python
def _make_picker(qtbot) -> AttributePicker:
    picker = AttributePicker()
    qtbot.addWidget(picker)
    return picker
```
`MainWindow` tests instead construct the whole window (`window = MainWindow(); qtbot.addWidget(window)`, as every `tests/gui/test_*.py` file does, e.g. `test_error_handling.py:41-42`) since the profile toolbar lives on `MainWindow`, not a standalone widget under test.

**Coalesced-signal wait pattern** (`tests/gui/test_attribute_picker.py:114-115`):
```python
with qtbot.waitSignal(picker.selection_changed, timeout=1000):
    picker.section_item("Extra Category").setCheckState(0, Qt.CheckState.Checked)
```
Use `qtbot.waitSignal(window.attribute_picker.selection_changed, timeout=1000)` wrapping the profile-combo activation (`window.profile_combo.setCurrentIndex(...); window.profile_combo.activated.emit(...)` or a direct call to `window._load_selected_profile()`) to assert the load fires exactly one coalesced `selection_changed`, matching `test_section_click_is_one_coalesced_change`'s structure.

## Shared Patterns

### Typed errors with a `user_message`/`str()` surface
**Source:** `src/gdtf_comparer/core/errors.py` (whole file, 48 lines)
**Apply to:** `core/profile_repository.py` (raises `ProfileNotFoundError`/`ProfileStorageError`), `gui/main_window.py` (catches them in the new profile handlers and passes `str(exc)` to `self._show_error(...)`, same as the existing `GDTFError` catch pattern implied by `on_comparison_failed`/`worker.py`'s friendly-message contract)
```python
class ProfileError(Exception):
    def __init__(self, message: str) -> None:
        self.user_message = message
        super().__init__(message)
    def __str__(self) -> str:
        return self.user_message
```

### Core/GUI separation (D-16, zero Qt imports in `core/`)
**Source:** every file under `src/gdtf_comparer/core/` (verified: `repository.py`, `errors.py`, `models.py`, `comparator.py` — no `PySide6`/`Qt` import anywhere)
**Apply to:** `core/profile_repository.py` must import only `json`, `os`, `tempfile`, `dataclasses`, `typing`, and `gdtf_comparer.core.errors` — never `PySide6`. All Qt widget code (toolbar, dialogs, combo box) stays in `gui/main_window.py`.

### Friendly modal dialog construction
**Source:** `src/gdtf_comparer/gui/main_window.py:558-574` (`_show_error`)
**Apply to:** All new profile-related user-facing dialogs (error display reuses `_show_error` directly; new Yes/No confirm dialogs for D-04/D-05 should mirror its `QMessageBox.Icon`, `"GDTF Comparer"` title, and `Qt.TextFormat.PlainText` conventions even though no Yes/No analog exists yet in this codebase)
```python
box = QMessageBox(
    QMessageBox.Icon.Warning,
    "GDTF Comparer",
    message,
    QMessageBox.StandardButton.Ok,
    self,
)
box.setTextFormat(Qt.TextFormat.PlainText)
box.exec()
```

### Module-level status-message constants
**Source:** `src/gdtf_comparer/gui/main_window.py:51-64` (`NO_ATTRIBUTES_SELECTED_MESSAGE`, `NO_DIFFERENCES_MESSAGE`)
**Apply to:** Any new fixed-text status message for the profile toolbar (e.g. a "Profile loaded — run a comparison to see which items match" message for RESEARCH Pitfall 2's no-comparison-yet case, per the Open Question 1 recommendation) — define as an `UPPER_SNAKE_CASE` module constant beside the existing two, not an inline string literal.

### Coalesced Qt signal emission via a zero-interval singleShot QTimer
**Source:** `src/gdtf_comparer/gui/attribute_picker.py:67-70, 230`
**Apply to:** `AttributePicker.set_checked()` — end with `self._emit_timer.start()`, never a direct `self.selection_changed.emit()` call, so a profile load and a manual multi-checkbox edit both produce exactly one `selection_changed` emission.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| Yes/No confirmation dialog helper (D-04 overwrite confirm, D-05 delete confirm) — likely a small private method on `MainWindow`, not a separate file | controller (dialog trigger) | request-response | `QMessageBox.question(...)`/`QInputDialog.getText(...)` have zero prior usage anywhere in `src/` or `tests/` (confirmed via grep) — no in-repo analog exists; follow `_show_error`'s construction conventions (Shared Patterns above) and Qt's standard `QMessageBox.question` convenience-constructor idiom from first principles, since RESEARCH's own Don't Hand-Roll table already names this as the correct stdlib/Qt-native choice (no custom modal `QWidget`). |

## Metadata

**Analog search scope:** `src/gdtf_comparer/core/`, `src/gdtf_comparer/gui/`, `tests/core/`, `tests/gui/` (all files in the current phase's dependency graph read in full this session; no files outside these four directories are implicated by CONTEXT.md/RESEARCH.md for ATTR-03)
**Files scanned:** 11 read in full (`core/repository.py`, `core/errors.py`, `core/models.py`, `core/comparator.py`, `gui/attribute_picker.py`, `gui/main_window.py`, `tests/core/test_repository.py`, `tests/gui/test_attribute_picker.py`, `tests/gui/test_error_handling.py`); 2 grepped for test structure (`tests/gui/test_attribute_selection.py`, `tests/gui/test_differences_only_toggle.py`); 1 grep confirming no `QMessageBox.question`/`QInputDialog` precedent exists anywhere in `src/`/`tests/`
**Pattern extraction date:** 2026-10-04
**Scope note:** CSV export (EXPORT-01/EXPORT-02) is out of scope per CONTEXT.md D-08 — no export-related files, patterns, or analogs are included in this map.
