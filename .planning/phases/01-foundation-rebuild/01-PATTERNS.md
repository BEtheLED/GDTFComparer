# Phase 1: Foundation Rebuild - Pattern Map

**Mapped:** 2026-09-25
**Files analyzed:** 20 (new/modified/removed)
**Analogs found:** 8 / 16 new files (strong or partial); 8 have no codebase analog

**Important context for the planner:** This phase is an explicit full rewrite (D-03) — GUI framework swaps Tkinter → PySide6, parser swaps hand-rolled → pygdtf, and a `core/`+`gui/` package layout replaces a single script. Because of this, roughly half of the new files (QThread worker, table model, theming, hardening) have **no prior implementation anywhere in this codebase** to copy from — for those, RESEARCH.md's "Architecture Patterns" and "Code Examples" sections (already vetted, source-verified code) are the primary pattern source, not a codebase analog. Where an analog does exist, it is almost always `BEtheLD` (the script being replaced) or `tests/test_parse_gdtf.py` (the test file being replaced) — useful for *behavioral/structural* intent (what the code must do, error-propagation conventions, test-fixture conventions) even though the underlying framework/library differs.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `core/errors.py` | model/utility | transform | — | no analog |
| `core/hardening.py` | utility | file-I/O | — | no analog (use RESEARCH.md Pattern 1) |
| `core/repository.py` | service | file-I/O | `BEtheLD` `parse_gdtf()` (lines 131-182) | role-match (same responsibility, different library) |
| `core/models.py` | model | transform | `BEtheLD` `attribute_categories` dict (lines 21-24) | weak/role-match |
| `core/comparator.py` | service | transform | `BEtheLD` `run_comparison()` (lines 97-128, diff logic only) | role-match |
| `gui/main_window.py` | component | request-response | `BEtheLD` `GDTFComparerApp` class (lines 11-128) | role-match (same responsibility, different framework) |
| `gui/worker.py` | service | event-driven | — | no analog (use RESEARCH.md Pattern 2) |
| `gui/table_model.py` | component | transform | — | no analog |
| `gui/theme.py` | config | transform | — | no analog (use RESEARCH.md "OS Theme Detection" example) |
| `app.py` | config | request-response | `BEtheLD` `main()` (lines 185-188) | role-match (entry-point shape only) |
| `pyproject.toml` | config | — | — | no analog (repo has no dependency-pinning file today) |
| `tests/core/conftest.py` | test | file-I/O | `tests/test_parse_gdtf.py` `build_gdtf_zip()` (lines 17-20) | exact (explicitly named in RESEARCH.md Wave 0 Gaps as the pattern to follow) |
| `tests/core/test_repository.py` | test | file-I/O | `tests/test_parse_gdtf.py` (whole file) | exact (same domain: GDTF zip/XML parse error-path testing) |
| `tests/core/test_hardening.py` | test | file-I/O | `tests/test_parse_gdtf.py::test_parse_gdtf_malformed_xml` / `::test_parse_gdtf_invalid_zip` | role-match |
| `tests/core/test_comparator.py` | test | transform | `tests/test_parse_gdtf.py` (structural style only) | weak/role-match |
| `tests/gui/test_main_window.py` | test | request-response | — | no analog (pytest-qt is new; no GUI tests exist today) |

### Files being removed (superseded by the rewrite)

| File | Disposition | Reason |
|------|-------------|--------|
| `BEtheLD` | delete | Replaced by `app.py` + `gui/` + `core/` per D-03 (full rewrite, not incremental port) |
| `tests/test_parse_gdtf.py` | delete | Tests `BEtheLD.parse_gdtf()`, which is being removed; superseded by `tests/core/test_repository.py`. RESEARCH.md Wave 0 Gaps flags this explicitly: "should be deleted/replaced ... not left dangling against dead code." |

`blender_addon/__init__.py` is out of scope for Phase 1 (untouched register/unregister stub, not part of this phase's file list).

## Pattern Assignments

### `core/repository.py` (service, file-I/O)

**Analog:** `BEtheLD` `parse_gdtf()` function

**Behavioral pattern to preserve** (lines 142-182 of `BEtheLD`):
```python
def parse_gdtf(file_path: str) -> Dict[str, Any]:
    """Parse a GDTF file.

    Parameters:
        file_path: Path to the ``.gdtf`` file to parse.

    Returns:
        Dictionary of attributes extracted from ``description.xml`` inside the
        archive. If ``description.xml`` is not found, an empty dictionary is
        returned.
    """
    temp_dir = tempfile.mkdtemp()
    try:
        ...
        try:
            with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile as exc:
            # Propagate the error so callers can handle it (e.g. tests)
            raise exc
        ...
        try:
            tree = ET.parse(description_path)
        except ET.ParseError as exc:
            # Propagate parse errors to the caller
            raise exc
        ...
    finally:
        shutil.rmtree(temp_dir)
```

**What to keep from this pattern:**
- Docstring style: summary line + `Parameters:`/`Returns:` sections (matches CLAUDE.md's documented docstring convention) — apply to `FixtureRepository.load()`.
- Error-propagation convention: catch a specific low-level exception only to re-raise it (`raise exc`), preserving traceback and intent, documented via a same-line comment ("Propagate ... so callers can handle it"). `core/repository.py` should follow this same explicit-propagation style for `zipfile.BadZipFile` and the new `GDTFValidationError` from `core/hardening.py`, per D-12 and RESEARCH.md Pitfall 2 (the `KeyError` from a missing/mis-cased `description.xml` should be caught the same explicit way and re-raised or wrapped, not silently swallowed).
- `finally`-block cleanup convention (`shutil.rmtree(temp_dir)` always runs) — **do not port the temp-dir extraction itself**: RESEARCH.md's "Deprecated/outdated" note and CONCERNS.md both flag `tempfile.mkdtemp()` + `shutil.copyfile()` + `extractall()` as an unnecessary double-I/O step. `core/repository.py` should read the zip in place (`zipfile.ZipFile(path)` directly, no copy/extract) as shown in RESEARCH.md Pattern 1's `validate_and_extract_description()`.
- **What changes:** replace the flat `parsed_data[key] = value` dict-building loop with pygdtf's structured `FixtureType(path)` call plus `core/hardening.py`'s pre-validation step (RESEARCH.md Pattern 1) — this is the entire point of PARSE-01/D-11, the flat-dict approach is the bug being fixed, not a pattern to copy.

---

### `core/comparator.py` (service, transform)

**Analog:** `BEtheLD` `GDTFComparerApp.run_comparison()` (diff-building portion only, lines 124-128)

**Core diff pattern to preserve the intent of:**
```python
# Populate treeview with comparison data
for category, attributes in self.attribute_categories.items():
    for attr in attributes:
        row = [attr, target_data.get(attr, "N/A")] + [data.get(attr, "N/A") for data in compare_data]
        self.tree.insert("", tk.END, values=row)
```
**What to keep:** the shape of "iterate category → attribute → build one row per attribute with target value + N comparison values", and the `.get(attr, "N/A")` fallback-for-missing-value idiom (use an equivalent sentinel/None-handling convention in the new `ComparisonResult` dataclass per D-13).
**What changes:** this must move from being GUI-embedded (mixed into a Tkinter event handler) into a pure, framework-agnostic function `compare(target: FixtureModel, comparisons: list[FixtureModel]) -> ComparisonResult` per D-13/D-16/UI-02 — the anti-pattern being fixed here is documented in CLAUDE.md's "Tightly Coupled GUI and Business Logic" anti-pattern and ARCHITECTURE.md. Comparison must operate on namespaced attribute paths (per D-11/Pattern 3 in RESEARCH.md), not flat attribute names, so the `attr` key in the loop above becomes a `(category, element_path, attr_name)` composite key, not a bare string.

---

### `core/models.py` (model, transform)

**Analog:** `BEtheLD` `attribute_categories` dict (lines 21-24)

```python
self.attribute_categories = {
    'Beam': ['BeamAngle', 'FieldAngle', 'PowerConsumption', 'LuminousFlux', 'ColorTemperature', 'BeamType'],
    'Physical Properties': ['Weight', 'Width', 'Height', 'Length'],
}
```
**What to keep:** the two category names and their attribute membership — CONTEXT.md D-10 explicitly locks Phase 1 to keep exactly these two categories. This is the one piece of `BEtheLD` state that should be **re-derived, not ported verbatim** (per CONTEXT.md code_context note): the new `FixtureModel` dataclass needs to express that `Beam` attributes are per-`GeometryBeam` (N values) and `Physical Properties` splits into a single `weight` scalar plus per-`Model` width/height/length (N values) — see RESEARCH.md Pitfall 3 and its illustrative dataclass sketch in Pattern 3. Do not reuse the flat list-of-strings shape.

---

### `gui/main_window.py` (component, request-response)

**Analog:** `BEtheLD` `GDTFComparerApp` class (lines 11-128)

**Structural pattern to preserve** (class shape, lines 11-31):
```python
class GDTFComparerApp:
    def __init__(self, master):
        self.master = master
        master.title("GDTF Comparer")
        master.resizable(True, True)

        self.target_file = ""
        self.compare_files = []
        ...
        self.selected_attributes = []

        # Create UI components
        self.create_widgets()
```
**What to keep:** overall widget/state responsibilities — target-file state, compare-files list, a `create_widgets()`-equivalent setup method called from `__init__`, and the file-selection → listbox-population → run-button flow (lines 74-95: `select_target_file`, `select_compare_files`, `remove_selected_files` map directly to `QFileDialog.getOpenFileName`/`getOpenFileNames` equivalents in PySide6). CLAUDE.md's documented Class Design convention ("`__init__()` first, defining all instance attributes"; "action methods grouped logically") applies directly to the new `MainWindow`.
**What must NOT be kept** (this is the anti-pattern CLAUDE.md explicitly documents as "Tightly Coupled GUI and Business Logic" and RESEARCH.md's architecture map fixes): `run_comparison()` (lines 97-128) directly calling `parse_gdtf()` synchronously and writing results straight into the tree widget. The new `MainWindow.run_comparison()` must only construct a `ComparisonWorker`, wire its `finished`/`failed` signals, and start the `QThread` (see `gui/worker.py` below) — no direct `core` calls, no direct pygdtf/zipfile imports (UI-02, verified via `grep -rn "import pygdtf\|import zipfile" src/gui/` per RESEARCH.md's test map).
**Also fixes:** the missing `messagebox` import bug (`BEtheLD` line 100/103 references `messagebox.showerror` without importing it — CLAUDE.md's own "No Error Messages to User" anti-pattern, and ARCHITECTURE.md's documented gap) — replaced by `QMessageBox` invoked from the `worker.failed` slot.

---

### `app.py` (config/entry point)

**Analog:** `BEtheLD` `main()` (lines 185-188)

```python
def main():
    root = tk.Tk()
    app = GDTFComparerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
```
**What to keep:** the `if __name__ == "__main__":` entry-point convention (CLAUDE.md Module Design: "Main entry point via `if __name__ == "__main__":` block") and the "build root/app object, construct main window, hand off to event loop" shape. In `app.py` this becomes the composition root: build `QApplication`, apply `gui/theme.py`'s theming, construct `MainWindow`, call `app.exec()`.

---

### `tests/core/conftest.py` (test fixture)

**Analog:** `tests/test_parse_gdtf.py` `build_gdtf_zip()` helper (lines 17-20)

```python
def build_gdtf_zip(path: Path, xml_content: str) -> None:
    """Create a minimal GDTF zip containing description.xml."""
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("description.xml", xml_content)
```
**What to keep:** this exact helper shape — minimal in-memory zip construction via `zipfile.ZipFile(path, "w").writestr(...)`, parameterized by XML content string, used with `tmp_path`. RESEARCH.md's Wave 0 Gaps explicitly calls this out: "`tests/core/conftest.py` — shared fixtures ... following the existing `build_gdtf_zip()` helper pattern already in `tests/test_parse_gdtf.py`." Extend it with variants needed for the new test surface: an oversized-file builder and a malicious-entity (`<!ENTITY>`) XML builder for `test_hardening.py`'s zip-bomb/XXE cases.

---

### `tests/core/test_repository.py` (test, file-I/O)

**Analog:** `tests/test_parse_gdtf.py` (whole file, 48 lines)

**Pattern to preserve** (import + test shape, lines 1-14, 23-38):
```python
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest

def test_parse_gdtf_success(tmp_path):
    xml = '<Root Attr1="Value1"><Child Attr2="Value2" /></Root>'
    gdtf_file = tmp_path / "sample.gdtf"
    build_gdtf_zip(gdtf_file, xml)

    result = parse_gdtf(str(gdtf_file))
    assert result["Attr1"] == "Value1"
    assert result["Attr2"] == "Value2"


def test_parse_gdtf_invalid_zip(tmp_path):
    bad_zip = tmp_path / "invalid.gdtf"
    bad_zip.write_text("not a zip")

    with pytest.raises(zipfile.BadZipFile):
        parse_gdtf(str(bad_zip))
```
**What to keep:** `tmp_path`-based fixture construction (no manual tempdir cleanup needed, pytest handles it — cleaner than `BEtheLD`'s own manual `tempfile.mkdtemp()`/`shutil.rmtree`), `pytest.raises(...)` for negative-path assertions, and one test function per behavior. Note the import hack at lines 8-14 (`importlib.machinery.SourceFileLoader` to load the extensionless `BEtheLD` script) is itself an artifact of the anti-pattern being fixed — `core/repository.py` will be a normal importable module, so `tests/core/test_repository.py` can just `from core.repository import FixtureRepository` directly; do not port the loader hack.
**What changes:** `test_parse_gdtf_malformed_xml` (lines 41-47) currently asserts `pytest.raises(ET.ParseError)` directly from the parse call — per RESEARCH.md Pitfall 1, this exact assertion pattern will NOT hold against `pygdtf.FixtureType()` (it silently swallows malformed XML instead of raising). The equivalent new test belongs in `test_hardening.py` against the `defusedxml`-based pre-validation step, asserting `GDTFValidationError` instead.

---

### `tests/core/test_hardening.py` (test, file-I/O)

**Analog:** `tests/test_parse_gdtf.py::test_parse_gdtf_malformed_xml` and `::test_parse_gdtf_invalid_zip` (lines 33-47)

Same `tmp_path` + `pytest.raises(...)` shape as above, but exercising `core/hardening.py`'s `validate_and_extract_description()` (already fully sketched in RESEARCH.md Pattern 1) rather than pygdtf directly — assert `GDTFValidationError` for malformed XML, oversized files, and XXE/entity payloads (RESEARCH.md's Phase Requirements → Test Map lists these as `test_malformed_xml_raises`, `test_oversized_file_rejected`, `test_xxe_rejected`).

---

## Shared Patterns

### Error propagation ("catch specific, re-raise explicitly")
**Source:** `BEtheLD` `parse_gdtf()`, lines 150-152 and 169-171 (`except zipfile.BadZipFile as exc: raise exc` / `except ET.ParseError as exc: raise exc`, each with an intent-explaining comment)
**Apply to:** `core/repository.py`, `core/hardening.py` — every place a low-level exception (`zipfile.BadZipFile`, `KeyError` from missing `description.xml` per Pitfall 2, `defusedxml` exceptions) is caught, it should be caught either to re-raise as-is or to wrap into a typed `core/errors.py` exception (`GDTFValidationError`), never silently swallowed. This mirrors CLAUDE.md's documented "Error Handling" convention: "Specific exception types caught and re-raised to allow caller handling" + "Exception context preserved when re-raising."

### Docstring style
**Source:** `BEtheLD` `parse_gdtf()` docstring, lines 132-141
**Apply to:** All new public functions/methods in `core/` (per CLAUDE.md Comments convention: "Docstrings present on public functions using triple-quoted format," "descriptive summary with Parameters and Returns sections").

### Test-fixture construction (`tmp_path` + zip-builder helper)
**Source:** `tests/test_parse_gdtf.py`, lines 17-20 (`build_gdtf_zip`) and every test function's use of `tmp_path`
**Apply to:** `tests/core/conftest.py` (shared fixture), `tests/core/test_repository.py`, `tests/core/test_hardening.py`, `tests/core/test_comparator.py`.

### Naming/style conventions (project-wide, from CLAUDE.md)
**Source:** CLAUDE.md "Naming Patterns" / "Code Style" sections (not a single file, but the documented convention derived from `BEtheLD`)
**Apply to:** all new files — snake_case functions/variables (`parse_gdtf`, `target_file`), PascalCase classes (`GDTFComparerApp` → `MainWindow`, `FixtureRepository`, `ComparisonWorker`), type hints via `typing`/PEP 585 generics on function signatures, 4-space indentation, standard-library-first import ordering (for `core/`, which per D-16 has zero Qt imports; for `gui/`, PySide6 imports follow standard-library imports).

## No Analog Found

Files with no close match in this codebase — planner should build these directly from RESEARCH.md's "Architecture Patterns" (Pattern 1/2/3) and "Code Examples" sections, which contain complete, source-verified illustrative implementations, not just descriptions:

| File | Role | Data Flow | Reason | Use Instead |
|------|------|-----------|--------|--------------|
| `core/errors.py` | model/utility | transform | No custom exception types exist anywhere in the current codebase (only bare stdlib exceptions are re-raised) | Define `GDTFValidationError` etc. fresh; no shape to copy beyond standard `class X(Exception): """docstring"""` |
| `core/hardening.py` | utility | file-I/O | No pre-validation/security-hardening layer exists today (CONCERNS.md flags this as a gap, not something to port) | RESEARCH.md "Pattern 1: Pre-Validation Before pygdtf" — full working code already provided |
| `gui/worker.py` | service | event-driven | Current app is fully synchronous/single-threaded (CONCERNS.md "Single-threaded UI"); no threading code exists to adapt | RESEARCH.md "Pattern 2: QThread Worker for Non-Blocking Parse+Compare" — full working code already provided |
| `gui/table_model.py` | component | transform | Current app renders directly into a `ttk.Treeview` with no model/view separation | RESEARCH.md "Don't Hand-Roll" table (row: "Comparison table widget") — build against `QAbstractTableModel`'s standard `rowCount`/`columnCount`/`data`/`headerData` contract |
| `gui/theme.py` | config | transform | No theming of any kind exists in `BEtheLD` (stock Tkinter look) | RESEARCH.md "OS Theme Detection + qt-material Wiring" code example — full working code already provided |
| `pyproject.toml` | config | — | Repo has no dependency-pinning file today (CONCERNS.md "Missing Dependency Management") | RESEARCH.md "Standard Stack" Installation block for exact pins; add `[tool.pytest.ini_options]` per Wave 0 Gaps |
| `tests/gui/test_main_window.py` | test | request-response | No GUI tests exist; pytest-qt is a new dependency this phase | pytest-qt's `qtbot` fixture (RESEARCH.md Standard Stack table) — standard smoke-test pattern, no in-repo precedent |
| `core/models.py` (dataclass shapes specifically, beyond category naming) | model | transform | No dataclass-based model exists in the current flat-dict design | RESEARCH.md "Pattern 3: Namespaced Attribute Keys" dataclass sketch — illustrative shape provided, exact key format is Claude's discretion (Open Question 1) |

## Metadata

**Analog search scope:** Entire repository (`git ls-files`, excluding `.claude/` and `.planning/`) — `BEtheLD`, `blender_addon/__init__.py`, `tests/test_parse_gdtf.py`. No `src/`, `core/`, or `gui/` directories exist yet (confirmed via `find . -maxdepth 2 -type d`) — this is a genuinely greenfield package layout, consistent with D-03's full-rewrite decision.
**Files scanned:** 3 source/test files (all read in full; all git-tracked, verified via `git ls-files`)
**Pattern extraction date:** 2026-09-25
