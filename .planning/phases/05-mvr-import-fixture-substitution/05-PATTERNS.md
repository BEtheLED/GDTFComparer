# Phase 5: MVR Import & Fixture Substitution - Pattern Map

**Mapped:** 2026-10-24
**Files analyzed:** 14 (7 core, 7 gui/test)
**Analogs found:** 14 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `core/mvr_hardening.py` | utility (security/validation) | file-I/O | `core/hardening.py` | exact |
| `core/mvr_repository.py` | service/repository | file-I/O + transform | `core/repository.py` (load pipeline) + `core/comparator.py` (walk/dedup shape) | exact |
| `core/requirements_repository.py` | model/repository | CRUD (file-based) | `core/profile_repository.py` | exact |
| `core/substitution.py` | service (pure scoring) | transform/batch | `core/comparator.py` (`compare`/`values_equal`) | exact |
| `core/errors.py` (extend) | model (typed errors) | — | `core/errors.py` (existing `GDTFError`/`ProfileError` families) | exact (same file) |
| `core/models.py` (extend, maybe) | model | — | `core/models.py` (`AttributeKey`/`FixtureModel` dataclasses) | exact (same file) |
| `gui/mvr_import_panel.py` | component (list view) | request-response | `gui/attribute_picker.py` | role-match |
| `gui/requirements_editor.py` | component (per-item editor) | request-response | `gui/attribute_picker.py` | exact |
| `gui/candidate_results_view.py` | component (ranked table) | request-response | `gui/table_model.py` (`ComparisonTableModel` + `BackgroundBrushDelegate`) | exact |
| `gui/worker.py` (extend: MVR parse worker, folder-scan worker) | component (QThread worker) | event-driven/async | `gui/worker.py` (`ComparisonWorker`) | exact |
| `tests/core/test_mvr_hardening.py` | test | — | `tests/core/test_hardening.py` (if present) else mirrors `core/hardening.py` test shape | role-match |
| `tests/core/test_requirements_repository.py` | test | — | `tests/core/test_profile_repository.py` (if present) | role-match |
| `tests/core/test_substitution.py` | test | — | `tests/core/test_comparator.py` (if present) | role-match |
| `tests/conftest.py` (extend: `make_mvr`) | test fixture/utility | file-I/O | `tests/conftest.py` existing `make_gdtf` fixture | exact |

## Pattern Assignments

### `core/mvr_hardening.py` (utility, file-I/O)

**Analog:** `src/gdtf_comparer/core/hardening.py` (full file, 317 lines — already read in full this session)

**Module docstring / intent pattern** (lines 1-18): explain *why* a hardening layer exists in front of an external parser lacking XXE/size/zip-bomb protection, and name the exact RESEARCH pitfall it closes.

**Constants pattern** (lines 33-41):
```python
MAX_GDTF_FILE_BYTES = 100 * 1024 * 1024
MAX_DESCRIPTION_XML_BYTES = 64 * 1024 * 1024
MAX_TOTAL_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100
RATIO_CHECK_FLOOR_BYTES = 10 * 1024 * 1024
DESCRIPTION_MEMBER = "description.xml"
```
Copy this shape verbatim for MVR: `MAX_MVR_FILE_BYTES`, `MAX_GSD_XML_BYTES`, `MAX_EMBEDDED_GDTF_BYTES` (reuse `MAX_GDTF_FILE_BYTES`), `GSD_XML_MEMBER = "GeneralSceneDescription.xml"`. Module-level constants, never captured as default-argument values, so tests can monkeypatch them directly (per the same file's own doc comment, lines 10-11).

**Safe single-read-with-size-cap pattern** (lines 54-139, `read_gdtf_bytes`): open with `O_NONBLOCK`, `fstat`+`S_ISREG` check before trusting it's a regular file, size-check against the stat result AND re-check the actual read length (`len(data) > limit`) since a file can grow between stat and read. Reuse near-verbatim for `read_mvr_bytes`.

**Capped, exact-member-only zip read pattern** (lines 142-217, `extract_description_bytes`): never `extractall`; `zf.getinfo(member)` + capped `member.read(limit+1)`; compression-ratio and total-uncompressed-size guard before any member read. Generalize this into a `extract_member_bytes(data, member_name, max_bytes, path)` helper (per RESEARCH's own recommendation) so MVR's `GeneralSceneDescription.xml` extraction and the later embedded-`.gdtf`-member extraction in `mvr_repository.py` both call the same guarded primitive — do not hand-roll a second zip-bomb guard.

**defusedxml parse pattern** (lines 220-264, `parse_description_safely`): `DET.fromstring(xml_bytes, forbid_dtd=True, forbid_entities=True, forbid_external=True)`, catching `DefusedXmlException` → unsafe-file typed error, `ET.ParseError` → validation typed error with line/column. Copy directly for `GeneralSceneDescription.xml`.

**Orchestration/NamedTuple-result pattern** (lines 267-316, `ValidatedGDTF`/`prevalidate_gdtf_document`): one function that does read→extract→parse and returns both the raw bytes (for the real parser) and the parsed root (for cross-checking) from a single disk read. Mirror as `ValidatedMVR`/`prevalidate_mvr_document`.

---

### `core/mvr_repository.py` (service/repository, file-I/O + transform)

**Analog 1 — load/wrap pipeline shape:** `src/gdtf_comparer/core/repository.py` (full file, 78 lines)

**Validate-then-parse-then-wrap-with-typed-errors pattern** (lines 31-77, `FixtureRepository.load`):
```python
validated = prevalidate_gdtf_document(path)
try:
    with pygdtf.FixtureType(io.BytesIO(validated.archive_bytes)) as fixture_type:
        ...
        return FixtureModel(...)
except GDTFError:
    raise
except Exception as exc:
    raise GDTFParseError(path, f"its GDTF data could not be parsed ({type(exc).__name__}).") from exc
```
Mirror this exact try/except shape in `mvr_repository.py`'s MVR-parse entry point: catch the library's own bare `AttributeError`/`KeyError` (RESEARCH Pitfalls 1-2) and re-raise as a typed `MVRParseError`/`MVRValidationError`, never letting a raw exception type surface.

**Bytes-accepting sibling entry point** (RESEARCH Code Examples, proposed `load_gdtf_bytes`): add a sibling to `FixtureRepository.load(path)` that accepts already-extracted bytes (from the MVR zip) and runs the identical `prevalidate → pygdtf → extract_attributes` pipeline with no second disk read and no temp file (`core/` forbids `tempfile`/`shutil` — enforced by `tests/test_architecture.py`).

**Analog 2 — recursive-walk/dedup pure-transform shape:** `src/gdtf_comparer/core/comparator.py` (full file, 220 lines), specifically `_cross_file_attributes` (lines 56-101) and `compare` (lines 104-162): build a new dict/view by walking an input structure once, keying/re-keying entries, never mutating the source. Apply the same "pure function over an already-validated structure, dict keyed by an identity, first-seen ordering" discipline to `iter_fixtures`/`by_gdtf_spec` dedup (RESEARCH Patterns 2-3) — these are already fully worked out in RESEARCH.md and should be copied close to verbatim:
```python
def iter_fixtures(child_list):
    if child_list is None:
        return
    yield from child_list.fixtures
    for group in child_list.group_objects:
        yield from iter_fixtures(group.child_list)
    for node_list in (child_list.trusses, child_list.supports,
                      child_list.video_screens, child_list.projectors):
        for node in node_list:
            yield from iter_fixtures(getattr(node, "child_list", None))
```

**Error handling pattern:** extend `core/errors.py`'s `GDTFError`-style base (see below) with `MVRError`/`MVRValidationError`/`MVRParseError`, same `user_message` property shape, same "never a traceback, lowercase reason fragment" discipline (errors.py lines 12-49).

---

### `core/requirements_repository.py` (model/repository, CRUD file-based)

**Analog:** `src/gdtf_comparer/core/profile_repository.py` (full file, 536 lines — already read in full this session)

**Schema-versioned payload + refuse-newer-version pattern** (lines 33-37, 246-258):
```python
PROFILES_SCHEMA_VERSION = 1
...
version = payload.get("version")
if type(version) is not int:
    raise self._damaged("unexpected layout")
if version > PROFILES_SCHEMA_VERSION:
    raise ProfileStorageError(f"...saved by a newer version... left unchanged.")
if version != PROFILES_SCHEMA_VERSION:
    raise self._damaged("unexpected layout")
```
Copy directly: `REQUIREMENTS_SCHEMA_VERSION = 1`, same three-way version check, so an older app build never silently misreads a newer requirements file (explicitly called out in CONTEXT.md's Claude's Discretion section).

**Size-capped read + damaged-file typed error pattern** (lines 171-225, `load_all`/`_damaged`): read with `MAX_..._FILE_BYTES + 1` cap, reject on oversize, reject on JSON/UTF-8 decode failure, one `_damaged(detail)` helper building a consistent `"...could not be read: '<path>' is damaged (<detail>). It was left unchanged."` message. **Important deviation to plan for:** unlike `profiles.json` (one app-data-dir file keyed by many names), SUB-03/D-08/D-09 require the requirements file to be a **single caller-supplied path** scoped to **one fixture type** — so `requirements_repository.py` should expose `save_requirements(path, requirement_set)` / `load_requirements(path) -> RequirementSet` taking an explicit path (like `ProfileRepository.__init__(base_dir=...)`'s test-injection pattern, lines 147-164), not an app-data-dir-resolving default, since the real "base dir" here is wherever the user's Save dialog points.

**Atomic same-folder temp-file write pattern** (lines 453-508, `_write_all`): `os.open(tmp_path, O_WRONLY|O_CREAT|O_EXCL, 0o600)` → write → `flush()` → `os.fsync(fh.fileno())` → `os.replace(tmp_path, self._path)`, wrapped in try/finally that removes the temp file on any failure. Copy verbatim (adjusted for a single caller-supplied path rather than `self._dir`/`self._path`). Never uses `tempfile`/`shutil` (architecture guard).

**Validation-before-write / never-destroy-on-damaged-read pattern** (`save()` docstring, lines 339-367): every write starts by loading/validating the existing file first, so a damaged or too-new file is never silently overwritten. For a single-fixture sidecar file this reduces to: never partially write — write the whole validated `RequirementSet` or nothing.

**Trust-boundary note (Security Domain, RESEARCH.md line 571):** this file is loaded by a *different* person/machine (D-07) — apply the same `MAX_PROFILES_FILE_BYTES`-style cap and strict shape validation profiles.json uses, since a requirements file crossing a trust boundary must not be trusted more than an arbitrary JSON blob.

---

### `core/substitution.py` (service, pure scoring/ranking)

**Analog:** `src/gdtf_comparer/core/comparator.py`, specifically `values_equal` (models.py lines 177-195) and the row-building loop in `compare()` (comparator.py lines 148-160)

**Pure-function-over-already-loaded-data pattern:**
```python
def values_equal(a, b):
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=1e-12)
    return a == b
```
`substitution.score()` is a direction+tolerance variant of this exact function: same `AttributeKey → AttributeValue` mapping (`core/models.py` `FixtureModel.attributes`) as its input shape, same "None means not declared, never treated as a value" semantics (models.py docstring lines 85-91). Do not introduce a parallel attribute-identity type — reuse `AttributeKey`.

**Row-building / tuple-of-flags-per-comparison pattern** (comparator.py lines 148-160):
```python
for key in ordered_keys:
    target_value = target_view.get(key)
    comparison_values = tuple(view.get(key) for view in comparison_views)
    differs = tuple(not values_equal(target_value, value) for value in comparison_values)
    rows.append(ComparisonRow(key=key, target_value=target_value,
                               comparison_values=comparison_values, differs=differs))
```
Mirror this shape for scoring: one `MatchResult`-style dataclass per (requirement, candidate) pair carrying a `state` (green/yellow/red) instead of a boolean `differs`; aggregate into a per-candidate ranked tuple the same way `ComparisonResult.rows` aggregates per-key rows.

**Direction/tolerance data model:** add a `Direction` enum (`HIGHER_IS_BETTER`, `LOWER_IS_BETTER`, `CLOSER_IS_BETTER`) and a `Requirement` dataclass (`attribute: AttributeKey`, `target_value`, `direction: Direction`, `tolerance: float`) in `core/models.py` or `core/substitution.py`, following the existing `@dataclass(frozen=True)` convention used by every model in `core/models.py` (lines 47-154).

**Open design gap to carry into planning (flagged by RESEARCH, not resolved):** D-06 locks one tolerance value, D-10 requires three states — RESEARCH's Assumption A4 proposes `tolerance * 0.5` as the green/yellow boundary for "closer-to-target" attributes and the target value itself as the boundary for higher/lower-is-better. This is explicitly unconfirmed; the planner should either carry this assumption forward with a `checkpoint:human-verify` or resolve it before the scoring function's final boundary math is written.

---

### `gui/requirements_editor.py` (component, request-response) and `gui/mvr_import_panel.py`

**Analog:** `src/gdtf_comparer/gui/attribute_picker.py` (full file, 286 lines)

**Checkable-tree-over-a-catalog pattern** (lines 80-141, `set_catalog`): build a `QTreeWidget` from a `(category, attribute_names)` catalog, track `_known`/`_checked` sets separately from the Qt widget state, block signals during rebuild, restore prior checked state for items seen before. The requirements editor is structurally the same widget with two more per-leaf fields (direction combo-box, tolerance spin-box) instead of a plain checkbox — reuse the section/leaf `QTreeWidgetItem` structure and the `_PAYLOAD_ROLE` (`Qt.ItemDataRole.UserRole`) convention for storing the `(category, attribute)` identity on each leaf (lines 28, 129, 206).

**Coalesced-signal-emission pattern** (lines 73-76, 268-285): a single-shot `QTimer` with `setInterval(0)` coalesces a cascade of per-leaf `itemChanged` signals (e.g. a section checkbox toggling many leaves) into exactly one `selection_changed` emission per event-loop turn. Reuse directly for a `requirements_changed` signal.

**"Replace wholesale, not merge" pattern** (lines 147-189, `set_checked`): loading a profile/requirement set replaces the current selection entirely and disables default-seeding for the rest of the session (`self._defaults_enabled = False`). Apply the same discipline when loading a previously-saved requirements file back into the editor.

**Search/visibility-only filtering pattern** (lines 210-266): search box only hides/shows tree items, never mutates checked state — directly reusable for `mvr_import_panel.py`'s fixture-type list if it needs search/filter.

---

### `gui/candidate_results_view.py` (component, ranked table)

**Analog:** `src/gdtf_comparer/gui/table_model.py` (full file, 419 lines)

**QAbstractTableModel-over-a-pure-result pattern** (lines 65-280, `ComparisonTableModel`): model wraps an immutable result object (`ComparisonResult` → here, a ranked list of per-candidate `MatchResult`s), `beginResetModel()`/`endResetModel()` bracket `set_result()`, `data()` dispatches by role (`DisplayRole`, `ToolTipRole`, a custom role, `BackgroundRole`). Reuse this exact shape for `CandidateResultsModel`, with a custom role publishing each cell's traffic-light state (green/yellow/red) for `BackgroundRole` lookup.

**BackgroundBrushDelegate — REQUIRED, not optional** (lines 367-385):
```python
class BackgroundBrushDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index) -> None:
        brush = index.data(Qt.ItemDataRole.BackgroundRole)
        if brush is not None:
            painter.fillRect(option.rect, brush)
        super().paint(painter, option, index)
```
RESEARCH flags (Architecture table, Test Map) that qt-material's stylesheet silently suppresses `BackgroundRole` painting without this delegate (a Phase 2 finding, already proven in production). The 3-state traffic-light cells in `candidate_results_view.py` MUST install this same delegate (or reuse it directly by import) on the results `QTableView`, or the colors will not render at all under the app's theme.

**Model→brush mapping:** follow `_background()`'s pattern (lines 162-176) of reading only typed state (never display text) to decide the brush — map `state == GREEN/YELLOW/RED` to three fixed `QColor`s the same way `_background` maps `row.differs[i]` to the highlight brush.

---

### `gui/worker.py` (extend: MVR-parse worker, folder-scan worker)

**Analog:** `src/gdtf_comparer/gui/worker.py` (full file, 54 lines) — `ComparisonWorker`

**QThread-worker-with-two-signals pattern** (full file):
```python
class ComparisonWorker(QObject):
    comparison_ready = Signal(object)
    comparison_failed = Signal(str)

    def __init__(self, target_path, compare_paths):
        super().__init__()
        self.target_path = target_path
        self.compare_paths = compare_paths

    @Slot()
    def run(self):
        try:
            result = compare_files(self.target_path, self.compare_paths)
        except GDTFError as exc:
            self.comparison_failed.emit(exc.user_message)
            return
        except Exception as exc:
            logger.exception("Unexpected error while comparing GDTF files")
            self.comparison_failed.emit(f"Something went wrong... ({type(exc).__name__}). ...")
            return
        self.comparison_ready.emit(result)
```
Copy this exact shape twice: an `MVRImportWorker` (wraps `core.mvr_repository`'s import call, emits `import_ready`/`import_failed`) and a `CandidateScanWorker` (wraps the folder-scan + `core.substitution.score`/`rank` call, emits `scan_ready`/`scan_failed`). Never touch a widget from `run()` — only emit signals; catch the typed error family first (`MVRError`, `RequirementsStorageError`), then a catch-all `Exception` that logs with `logger.exception` and emits a generic non-crashing message, exactly as done here.

---

## Shared Patterns

### Typed error family with friendly `user_message`
**Source:** `src/gdtf_comparer/core/errors.py` (full file, 82 lines)
**Apply to:** `core/mvr_hardening.py`, `core/mvr_repository.py`, `core/requirements_repository.py`

Two existing shapes to extend, not replace:
```python
class GDTFError(Exception):
    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        super().__init__(self.user_message)
    @property
    def user_message(self) -> str:
        return f"Could not open '{self.file_name}': {self.reason}"
```
```python
class ProfileError(Exception):
    def __init__(self, message: str) -> None:
        self.user_message = message
        super().__init__(message)
```
Add `MVRError(GDTFError-style, path+reason)` → `MVRValidationError`, `MVRUnsafeFileError`, `MVRParseError` (mirrors the `GDTFValidationError`/`GDTFUnsafeFileError`/`GDTFParseError` hierarchy, lines 40-49). Add `RequirementsStorageError`-style family mirroring `ProfileError`/`ProfileNameError`/`ProfileNotFoundError`/`ProfileStorageError` (lines 52-82) since the requirements file has no single failing path the same way a profile set doesn't.

### Zero-Qt, no-tempfile/shutil discipline in `core/`
**Source:** `tests/test_architecture.py` (AST-based guard, referenced throughout `core/hardening.py` and `core/profile_repository.py` docstrings)
**Apply to:** every new `core/` module (`mvr_hardening.py`, `mvr_repository.py`, `requirements_repository.py`, `substitution.py`)

This guard runs automatically against any new file placed under `core/` — no changes needed to the test itself, but every new module must avoid `import tempfile`, `import shutil`, any `PySide6`/`Qt` import, and `zipfile.ZipFile.extractall()`.

### Atomic file write (same-folder temp + os.replace)
**Source:** `src/gdtf_comparer/core/profile_repository.py` lines 453-508 (`_write_all`)
**Apply to:** `core/requirements_repository.py`'s save function

### Pre-validate bytes once, hand the same bytes to the external parser
**Source:** `src/gdtf_comparer/core/hardening.py` lines 280-299 (`prevalidate_gdtf_document`) + `core/repository.py` lines 51-54
**Apply to:** `core/mvr_hardening.py` + `core/mvr_repository.py` — read once, validate, hand `io.BytesIO(validated_bytes)` to `pymvr`, never a second disk read, never `pymvr._package`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `core/direction_defaults.py` (optional, or inline table in `substitution.py`) | utility (pure lookup table) | transform | No prior "attribute name → enum default" lookup table exists in this codebase; RESEARCH.md's Smart Default Direction Table proposal is the closest available reference (tagged `[ASSUMED]`, not a codebase analog) |
| `tests/conftest.py` `make_mvr` fixture | test fixture | file-I/O | No prior MVR-building test helper exists; mirror the shape of the existing `make_gdtf`/`build_description_xml` helpers referenced in RESEARCH.md Sources (read this session but not reproduced here — planner/executor should read `tests/conftest.py` directly when writing `make_mvr`) |

## Metadata

**Analog search scope:** `src/gdtf_comparer/core/`, `src/gdtf_comparer/gui/`, full file reads (all ≤ 540 lines, no large-file truncation needed)
**Files scanned:** `core/hardening.py`, `core/repository.py`, `core/comparator.py`, `core/models.py`, `core/errors.py`, `core/profile_repository.py`, `gui/attribute_picker.py`, `gui/worker.py`, `gui/table_model.py` (9 files read in full)
**Pattern extraction date:** 2026-10-24
