# Phase 2: Attribute Browsing & Diff Highlighting - Pattern Map

**Mapped:** 2026-09-29
**Files analyzed:** 13 (5 modified core/GUI source, 5 modified/new tests, 1 new GUI widget, 2 new GUI test files counted separately below)
**Analogs found:** 13 / 13 (all files have a same-repo analog; several are "self-analogs" — the file being extended is its own best pattern source)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/gdtf_comparer/core/models.py` (modify) | model | transform | itself (existing `DISPLAY_CATEGORIES`/`AttributeKey`) | exact (self-analog) |
| `src/gdtf_comparer/core/extract.py` (modify) | service (pure extraction) | transform | itself (existing `BEAM_ATTRIBUTES`/`MODEL_ATTRIBUTES` loops) | exact (self-analog) |
| `src/gdtf_comparer/core/comparator.py` (modify) | service | transform / request-response | itself (existing `compare()`) | exact (self-analog) |
| `src/gdtf_comparer/gui/attribute_picker.py` (new) | component (Qt widget) | event-driven | `src/gdtf_comparer/gui/main_window.py` (`compare_list` QListWidget construction + item data pattern) | role-match |
| `src/gdtf_comparer/gui/table_model.py` (modify: `BackgroundRole` + 2 new proxy classes) | model/component (Qt model + proxy) | request-response (Qt paint queries) | itself — `ComparisonTableModel.data()` for the role branch; `UppercaseHeaderProxyModel` for the new proxy classes | exact (self-analog) |
| `src/gdtf_comparer/gui/main_window.py` (modify) | controller (Qt window) | event-driven | itself (existing `create_widgets`/`on_comparison_ready`) | exact (self-analog) |
| `tests/conftest.py` (modify) | test fixture/utility | file-I/O | itself (`build_description_xml`/`make_gdtf` `models_xml=`/`geometries_xml=` params) | exact (self-analog) |
| `tests/core/test_extract.py` (modify) | test | transform | itself (`test_omitted_weight_is_none_not_zero`, `test_beam_attribute_set_and_order`) | exact (self-analog) |
| `tests/core/test_comparator.py` (modify) | test | request-response | itself (`test_only_display_categories`, `test_rows_ordered_beam_then_physical`) | exact (self-analog) |
| `tests/gui/test_attribute_picker.py` (new) | test | event-driven | `tests/gui/test_namespaced_rows.py` (qtbot + `MainWindow()` pattern) | role-match |
| `tests/gui/test_attribute_selection.py` (new) | test | event-driven | `tests/gui/test_namespaced_rows.py` | role-match |
| `tests/gui/test_diff_highlighting.py` (new) | test | request-response | `tests/gui/test_namespaced_rows.py` (Qt-model assertions) + `tests/core/test_models.py` (`any_differs` precedent) | role-match |
| `tests/test_architecture.py` (conditionally modify — only if a new core module is added) | test (import-boundary guard) | transform | itself (`APPROVED_CORE_SURFACE`) | exact (self-analog, only touch if scope requires it — see Shared Patterns) |

## Pattern Assignments

### `src/gdtf_comparer/core/models.py` (model, transform)

**Analog:** itself, `/Users/brandon/GDTFComparer/src/gdtf_comparer/core/models.py`

**Current constants to relax/extend** (lines 17-19):
```python
CATEGORY_BEAM = "Beam"
CATEGORY_PHYSICAL = "Physical Properties"
DISPLAY_CATEGORIES: tuple = (CATEGORY_BEAM, CATEGORY_PHYSICAL)
```
Per Pitfall 2 in RESEARCH.md: `tests/core/test_comparator.py` imports `DISPLAY_CATEGORIES` directly (`from gdtf_comparer.core.models import (..., DISPLAY_CATEGORIES, ...)`). Deleting it breaks that import. Recommended: keep `DISPLAY_CATEGORIES` (rename optional, e.g. `LEGACY_DEFAULT_CATEGORIES`) as the D-04 "first-use default selection" source, add new `CATEGORY_*` constants for each new category (e.g. `CATEGORY_DMX_ATTRIBUTES = "DMX Attributes"`), and stop using `DISPLAY_CATEGORIES` as `compare()`'s row filter.

**`AttributeKey` reuse — no changes needed** (lines 23-43): `category`/`element_path`/`attribute` fields are already generic; new categories plug in without a schema change.

**`ComparisonRow.any_differs` — reuse directly, do not reimplement** (lines 99-108):
```python
@property
def any_differs(self) -> bool:
    """Return True if any comparison value differs from the target. ..."""
    return any(self.differs)
```
This is the exact predicate for DIFF-01's cell highlighting input and D-06's differences-only toggle. `differs: tuple` (line 97) is the per-comparison-column boolean already used for the highlight decision.

---

### `src/gdtf_comparer/core/extract.py` (service, transform)

**Analog:** itself, `/Users/brandon/GDTFComparer/src/gdtf_comparer/core/extract.py`

**Imports pattern** (lines 44-55):
```python
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from xml.etree.ElementTree import Element

from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    FIXTURE_LEVEL_PATH,
    AttributeKey,
    AttributeValue,
)

from pygdtf.geometries import TAG_TO_GEOMETRY_CLASS, GeometryBeam
```

**Core pattern to generalize — the declared-vs-default presence-check loop** (lines 279-290, `BEAM_ATTRIBUTES` loop):
```python
BEAM_ATTRIBUTES: Tuple[Tuple[str, str], ...] = (
    ("BeamAngle", "beam_angle"),
    ("FieldAngle", "field_angle"),
    ("PowerConsumption", "power_consumption"),
    ("LuminousFlux", "luminous_flux"),
    ("ColorTemperature", "color_temperature"),
    ("BeamType", "beam_type"),
)
...
for gdtf_name, field_name in BEAM_ATTRIBUTES:
    if gdtf_name not in element.attrib:
        value: AttributeValue = None
    else:
        raw_value = getattr(node, field_name, None)
        if gdtf_name == "BeamType":
            value = raw_value.value if raw_value is not None else None
        else:
            value = float(raw_value) if raw_value is not None else None
    attributes[AttributeKey(CATEGORY_BEAM, element_path, gdtf_name)] = value
```
Per RESEARCH.md Pattern 1, generalize this (and the near-identical `MODEL_ATTRIBUTES` loop at lines 305-311) into one shared helper parameterized by `(gdtf_name, field_name, value_transform)` triples — RESEARCH.md's "Code Examples" section has a full sketch (`_extract_scalar_attributes`) to copy from directly; do not hand-write a fourth near-duplicate loop for the new DMX-Attributes category.

**Presence-check contract to preserve for every new field** (module docstring, lines 25-41): every new attribute this phase adds (e.g. `fixture_type.attributes` entries) must apply the same "declared in XML, not just present in pygdtf's backfilled object model" check — `gdtf_name not in element.attrib` before trusting `getattr(node, field_name)`. `_weight_declared()` (lines 200-226) is the reference pattern for a nested/optional-ancestor presence check if the new category needs multi-level XML lookups (e.g. `<AttributeDefinitions><Attributes>`).

**Error handling pattern** (lines 58-70, `DescriptionMismatchError`): raised, never caught internally, fixed non-file-content message text; reuse this exception type (don't invent a new one) if a new category's lockstep walk can mismatch.

---

### `src/gdtf_comparer/core/comparator.py` (service, transform/request-response)

**Analog:** itself, `/Users/brandon/GDTFComparer/src/gdtf_comparer/core/comparator.py`

**Imports pattern** (lines 8-17):
```python
from typing import Optional, Sequence

from gdtf_comparer.core.models import (
    DISPLAY_CATEGORIES,
    ComparisonResult,
    ComparisonRow,
    FixtureModel,
    values_equal,
)
from gdtf_comparer.core.repository import FixtureRepository
```

**Core pattern — the filter to relax** (lines 32-45):
```python
ordered_keys = []
seen = set()
for model in (target, *comparisons):
    for key in model.attributes:
        if key.category not in DISPLAY_CATEGORIES:
            continue
        if key in seen:
            continue
        seen.add(key)
        ordered_keys.append(key)

ordered_keys.sort(key=lambda k: DISPLAY_CATEGORIES.index(k.category))
```
Per Integration Points in CONTEXT.md and Anti-Patterns in RESEARCH.md: remove the `key.category not in DISPLAY_CATEGORIES: continue` filter (or a `sort by DISPLAY_CATEGORIES.index` that would `ValueError` on new categories) so `compare()` produces rows for **all** categories — selection/filtering moves to a GUI-layer proxy model, keeping `compare()` a pure, selection-unaware function. Replace the category sort key with something that tolerates arbitrary categories (e.g. sort by first-seen order, or an explicit category-priority list that includes every category, not just the legacy two).

**New function to add — "available (category, attribute) catalog for the picker"**: follow `compare()`'s own signature/docstring style (Google-style Parameters/Returns, pure function of already-loaded models) and put it in this file (or `core/models.py`) — **not** a new module — per Pitfall 1 (`APPROVED_CORE_SURFACE` allow-list in `tests/test_architecture.py` would reject a brand-new `core/catalog.py` module unless that test is also updated in the same wave). Per RESEARCH.md Pattern 2, the returned catalog must be keyed by `(category, attribute)` pairs — never full `AttributeKey` — deduplicating across geometry-instance element paths.

**`compare_files()` batch entry point — unchanged, no new pattern needed** (lines 64-86): the GUI's only call into this module goes through here already; no signature change required by this phase.

---

### `src/gdtf_comparer/gui/attribute_picker.py` (new component, event-driven)

**Analog:** `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/main_window.py` (QListWidget + per-item data pattern, lines 114-125, 208-237) and `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/table_model.py` (module/docstring conventions)

**Imports pattern** (main_window.py lines 12-33, trim to what a new widget module needs):
```python
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)
```
For the picker itself, RESEARCH.md's "Don't Hand-Roll" section specifies `QTreeWidget` with `Qt.ItemFlag.ItemIsUserCheckable` + `QTreeWidgetItem.setCheckState` (not `QListWidget`) — the analog above is for *style* (module docstring convention, per-item payload via `setData(Qt.ItemDataRole.UserRole, ...)`), not the exact widget class.

**Per-item payload pattern to copy** (main_window.py lines 234-237):
```python
item = QListWidgetItem(os.path.basename(path))
item.setToolTip(path)
item.setData(Qt.ItemDataRole.UserRole, path)
self.compare_list.addItem(item)
```
Apply the same `setData(Qt.ItemDataRole.UserRole, <payload>)` idiom to each `QTreeWidgetItem`, storing the `(category, attribute)` tuple as the payload so the checked-state read-back never re-parses the item's display text.

**Search-narrows-visibility pattern**: RESEARCH.md's Don't-Hand-Roll table recommends `QSortFilterProxyModel`-style filtering elsewhere in this phase, but for a `QTreeWidget` (not a model/view pair) the idiomatic equivalent is per-item `setHidden(bool)` driven by a `QLineEdit.textChanged` signal — follow `main_window.py`'s existing signal-connection idiom (`self.add_button.clicked.connect(self.select_compare_files)`, line 120) for wiring `search_edit.textChanged.connect(self._on_search_changed)`.

**Module docstring convention** (table_model.py lines 1, extract.py lines 1-42): a one-line summary docstring referencing the relevant decision IDs (D-01/D-02/D-03), followed by a longer explanation of any non-obvious invariant (here: checkbox state is per-`(category, attribute)`, not per-`AttributeKey` — Pattern 2 in RESEARCH.md).

---

### `src/gdtf_comparer/gui/table_model.py` (modify: add `BackgroundRole` + 2 new proxy classes)

**Analog:** itself — `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/table_model.py`

**Core pattern — `data()` role branch to extend** (lines 95-109):
```python
def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
    """Return display/tooltip data for a cell."""
    if not index.isValid() or self._result is None:
        return None

    row = self._result.rows[index.row()]
    column = index.column()

    if role == Qt.ItemDataRole.DisplayRole:
        return self._display_value(row, column)
    if role == Qt.ItemDataRole.ToolTipRole:
        if column == self.COL_ELEMENT:
            return row.key.element_path
        return self._display_value(row, column)
    return None
```
Add a third `if role == Qt.ItemDataRole.BackgroundRole:` branch here (RESEARCH.md Pattern 3's exact sketch):
```python
if role == Qt.ItemDataRole.BackgroundRole:
    if column > self.COL_TARGET:
        comparison_index = column - self.COL_TARGET - 1
        if 0 <= comparison_index < len(row.differs) and row.differs[comparison_index]:
            return self._highlight_color  # cached QColor — see Shared Patterns
    return None
```
Reuses the exact `comparison_index = column - self.COL_TARGET - 1` bounds-checked indexing idiom already used in `_display_value()` (line 121) — copy it, don't reinvent.

**Proxy-model pattern to replicate exactly** (lines 215-246, `UppercaseHeaderProxyModel`):
```python
class UppercaseHeaderProxyModel(QIdentityProxyModel):
    """View-only proxy that uppercases horizontal header DisplayRole text.
    ...
    """

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Return the source header value, uppercased for horizontal DisplayRole text."""
        value = super().headerData(section, orientation, role)
        if (
            orientation == Qt.Orientation.Horizontal
            and role == Qt.ItemDataRole.DisplayRole
            and isinstance(value, str)
        ):
            return value.upper()
        return value
```
For the two new proxies (attribute-selection filter, differences-only filter), subclass `QSortFilterProxyModel` instead of `QIdentityProxyModel` and override `filterAcceptsRow(source_row, source_parent)` instead of `headerData` — same one-purpose-per-class, docstring-first convention, same "never touch the source model" philosophy stated in the class docstring above. The differences-only proxy's predicate is a one-liner: `self.sourceModel().result().rows[source_row].any_differs`.

---

### `src/gdtf_comparer/gui/main_window.py` (controller, event-driven)

**Analog:** itself — `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/main_window.py`

**Imports pattern** (lines 8-33) — extend, don't replace:
```python
from PySide6.QtCore import QThread, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QTableView, QVBoxLayout, QWidget,
)

from gdtf_comparer.core.models import ComparisonResult
from gdtf_comparer.gui.table_model import ComparisonTableModel, UppercaseHeaderProxyModel
from gdtf_comparer.gui.worker import ComparisonWorker
```
Add `QCheckBox` (or chosen toggle widget) to the `QtWidgets` import block and `from gdtf_comparer.gui.attribute_picker import AttributePicker` (new module) alongside the existing `table_model`/`worker` imports — same "core.models + gui.table_model + gui.worker" three-tier import shape, no new external dependency.

**Widget-construction pattern to extend** (`create_widgets()`, lines 94-156): the picker panel attaches here, following the existing `QGroupBox` + layout composition style (`files_group = QGroupBox("Files", central)` at line 100 is the template for a new `QGroupBox("Attributes", central)` or similar side panel), and the proxy-chaining pattern at lines 140-144:
```python
self.table_model = ComparisonTableModel(central)
self.header_proxy = UppercaseHeaderProxyModel(central)
self.header_proxy.setSourceModel(self.table_model)
self.table_view = QTableView(central)
self.table_view.setModel(self.header_proxy)
```
Per the Architecture Diagram in RESEARCH.md, insert the two new proxies **before** `header_proxy` in this chain: `table_model → AttributeSelectionProxy → DifferencesOnlyProxy → header_proxy → table_view`.

**State-ownership pattern** (`__init__`, lines 83-92): `self.target_file`, `self.compare_files` are the existing precedent for "new instance state owned by MainWindow" — the checked-`(category, attribute)`-set state and the diff-only-toggle boolean belong here the same way, initialized in `__init__` before `create_widgets()`.

**Wiring-a-fresh-result pattern** (`on_comparison_ready`, lines 297-307):
```python
def on_comparison_ready(self, result: ComparisonResult) -> None:
    """Render a successful comparison result. ..."""
    self.table_model.set_result(result)
    self._fit_columns_to_contents()
    self.statusBar().showMessage(
        f"Compared {len(result.comparisons)} file(s) against {result.target.file_name}"
    )
```
This is where the picker's catalog gets (re)populated from the new result (via the core catalog function) and where D-04's first-use default-selection gets applied if no prior selection exists yet.

**Signal-connection idiom** (lines 108, 120, 122, 136): `self.<button>.clicked.connect(self.<handler>)` — apply the same style for the picker's checkbox-changed signal and the diff-only-toggle's `stateChanged`/`toggled` signal.

---

### `tests/conftest.py` (test fixture/utility, file-I/O)

**Analog:** itself — `/Users/brandon/GDTFComparer/tests/conftest.py`

**Pattern to extend** (lines 15-75, `build_description_xml` signature and lines 89-100, `_make` factory signature):
```python
def build_description_xml(
    *,
    name: str,
    manufacturer: str,
    weight: Optional[float],
    models_xml: str,
    geometries_xml: str,
) -> str:
    ...
    "    <AttributeDefinitions>\n"
    "      <ActivationGroups/>\n"
    "      <FeatureGroups/>\n"
    "      <Attributes/>\n"
    "    </AttributeDefinitions>\n"
    "    <Wheels/>\n"
```
Add `attributes_xml: str = ""` (and `wheels_xml: str = ""` if Wheels is in scope) as new keyword-only parameters, following the exact same "raw XML string injected verbatim into a hardcoded empty element" idiom already used for `models_xml`/`geometries_xml` — replace the hardcoded `<Attributes/>` line with `f"      {attributes_xml}\n"` the same way `<Models>{models_xml}</Models>` already works (line 67). Thread the new parameter through `make_gdtf`'s `_make(...)` factory signature (lines 89-100) identically to how `models_xml`/`geometries_xml` already pass through.

---

### `tests/core/test_extract.py` (test, transform)

**Analog:** itself — `/Users/brandon/GDTFComparer/tests/core/test_extract.py`

**Presence-vs-default test pattern to mirror** (lines 23-34):
```python
def test_omitted_weight_is_none_not_zero(make_gdtf):
    path = make_gdtf("fixture.gdtf", weight=None)

    with pygdtf.FixtureType(str(path)) as fixture_type:
        # pygdtf itself backfills 0 for an omitted Weight -- proves the
        # substitution this test guards against is real.
        assert fixture_type.properties.weight == 0

    attributes = _extract(path)

    weight_key = AttributeKey(CATEGORY_PHYSICAL, FIXTURE_LEVEL_PATH, "Weight")
    assert attributes[weight_key] is None
```
Every new category's extraction needs an equivalent "prove pygdtf backfills a default, then prove extraction reports `None` for the undeclared case" test pair (declared vs. omitted), using the `_extract(path)` helper (lines 16-20) unchanged.

**Ordering/set test pattern** (lines 64-80, `test_beam_attribute_set_and_order`): mirror for the new category's attribute list.

---

### `tests/core/test_comparator.py` (test, request-response)

**Analog:** itself — `/Users/brandon/GDTFComparer/tests/core/test_comparator.py`

**Test requiring an update, not just extension** (lines 163-180):
```python
def test_only_display_categories(make_gdtf):
    ...
    result = compare_files(str(target), [str(comparison)])
    assert all(row.key.category in DISPLAY_CATEGORIES for row in result.rows)
```
Per Pitfall 2, this assertion is inverted by this phase's change (rows now cover *all* categories, not just `DISPLAY_CATEGORIES`) — rename/rewrite it to assert the new behavior (e.g. `test_all_categories_present` asserting a new category's rows are present too), and fix the `DISPLAY_CATEGORIES` import at the top of the file (lines 4-9) if the constant is renamed in `core/models.py`.

**Row-shape assertion pattern to reuse for new-category rows** (lines 21-52, `test_no_attribute_collision`): `row.target_value`, `row.comparison_values`, `row.differs` field access pattern — identical for any new category's rows.

---

### `tests/gui/test_attribute_picker.py`, `tests/gui/test_attribute_selection.py`, `tests/gui/test_diff_highlighting.py` (new tests, event-driven / request-response)

**Analog:** `/Users/brandon/GDTFComparer/tests/gui/test_namespaced_rows.py`

**Full pattern to copy (qtbot + MainWindow + make_gdtf composition)** (lines 1-59):
```python
from PySide6.QtCore import Qt

from gdtf_comparer.core.models import CATEGORY_BEAM, CATEGORY_PHYSICAL
from gdtf_comparer.gui.main_window import MainWindow

def test_table_shows_distinct_element_paths(qtbot, make_gdtf):
    target = make_gdtf("target.gdtf", name="Target Fixture", geometries_xml=_GEOMETRIES_XML)
    comparison = make_gdtf("comparison.gdtf", name="Comparison Fixture", geometries_xml=_GEOMETRIES_XML)

    window = MainWindow()
    qtbot.addWidget(window)

    window.set_target_file(str(target))
    window.add_compare_files([str(comparison)])

    qtbot.mouseClick(window.run_button, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: window.run_button.isEnabled(), timeout=10000)

    model = window.table_model
    ...
    assert model.data(model.index(head1_row, model.COL_ELEMENT)) == "Body/Head1/Beam"
```
This is the exact `qtbot.addWidget(window)` → `set_target_file`/`add_compare_files` → `qtbot.mouseClick(run_button)` → `qtbot.waitUntil(run_button.isEnabled)` → assert-on-`window.table_model` recipe every new GUI test in this phase should follow, substituting `window.table_model.data(..., role=Qt.ItemDataRole.BackgroundRole)` for the highlight test and `window.attribute_picker`/checked-set state for the picker tests.

**`any_differs` precedent for the highlight test's input** (`tests/core/test_models.py`, lines 13-20):
```python
def test_any_differs_true_when_any_comparison_differs():
    ...
    assert row.any_differs is True
```
`test_diff_highlighting.py` is the GUI-layer counterpart: same boolean, now asserted via `BackgroundRole` presence/absence instead of the raw property.

## Shared Patterns

### Core/GUI Import Boundary (architecture guard)
**Source:** `/Users/brandon/GDTFComparer/tests/test_architecture.py` lines 20-24, 148-161
**Apply to:** `core/comparator.py`'s new catalog function, and every new/modified `gui/*.py` file
```python
APPROVED_CORE_SURFACE = {
    "gdtf_comparer.core.comparator",
    "gdtf_comparer.core.models",
    "gdtf_comparer.core.errors",
}
```
Any GUI file (`attribute_picker.py`, `table_model.py`, `main_window.py`) may only import from these three core modules. The new "available attributes for the picker" function **must** live in `core/comparator.py` or `core/models.py` — putting it in a new `core/catalog.py` fails `test_gui_uses_only_core_service_surface` unless that same plan/wave also adds the new module name to `APPROVED_CORE_SURFACE` here.

### Declared-vs-Default Presence Check (extraction correctness)
**Source:** `/Users/brandon/GDTFComparer/src/gdtf_comparer/core/extract.py` lines 25-41 (module docstring), 279-290 (loop), 200-226 (`_weight_declared`)
**Apply to:** every new attribute extracted for the new category(ies)
```python
if gdtf_name not in element.attrib:
    value: AttributeValue = None
else:
    raw_value = getattr(node, field_name, None)
    value = float(raw_value) if raw_value is not None else None
```
pygdtf silently backfills GDTF-spec defaults (`Properties.weight=0`, `BeamType._default="Wash"`, etc.) — never trust `getattr(node, field, None)` alone; always gate on the raw XML attribute's presence first. This is the single most load-bearing pattern in the whole phase per RESEARCH.md Pitfall 3.

### `ComparisonRow.differs` / `any_differs` as the single diff source of truth
**Source:** `/Users/brandon/GDTFComparer/src/gdtf_comparer/core/models.py` lines 94-108
**Apply to:** `table_model.py`'s new `BackgroundRole` branch and the new differences-only proxy's `filterAcceptsRow`
No new diff-computation logic should be written anywhere in this phase — both DIFF-01 features are pure consumers of `row.differs[i]` / `row.any_differs`, already computed by `compare()` and already unit-tested in `tests/core/test_models.py`.

### Qt Proxy-Model Layering (view-only behavior, source model untouched)
**Source:** `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/table_model.py` lines 215-246 (`UppercaseHeaderProxyModel`); wired in `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/main_window.py` lines 140-144
**Apply to:** the new `AttributeSelectionProxy` and `DifferencesOnlyProxy` classes
```python
self.table_model = ComparisonTableModel(central)
self.header_proxy = UppercaseHeaderProxyModel(central)
self.header_proxy.setSourceModel(self.table_model)
self.table_view.setModel(self.header_proxy)
```
Insert new proxies into this exact chain (`table_model → new proxy → new proxy → header_proxy → table_view`) rather than modifying `ComparisonTableModel`'s row set directly — matches the codebase's one-class-one-purpose proxy convention and its stated "never touch the source model" philosophy.

### Theme-Aware Color, Never Hardcoded (D-05 styling constraint)
**Source:** `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/theme.py` lines 26-32, 51-66, 69-109
**Apply to:** the highlight `QColor` computation in `table_model.py`
```python
THEME_PROPERTY = "gdtf_comparer_theme"
...
if app.property(THEME_PROPERTY) == theme:
    return False
```
Read the live theme via `QApplication.instance().property(theme.THEME_PROPERTY)`, then `qt_material.get_theme(name, invert_secondary=name.startswith("light_"))` — **compute and cache the resulting `QColor` once**, never inside `data()` (RESEARCH.md Pitfall: `get_theme()` re-parses an XML file and mutates `os.environ` per call; `data()` is invoked per visible cell per repaint). Recompute only when `OsThemeFollower.on_color_scheme_changed` fires (theme.py line 79's existing `colorSchemeChanged` connection) — `MainWindow` needs its own connection to the same signal to refresh the cached color and trigger a repaint.

### Google-style Docstrings with Decision-ID Cross-References
**Source:** pervasive — e.g. `/Users/brandon/GDTFComparer/src/gdtf_comparer/core/models.py` lines 1-8, 23-43; `/Users/brandon/GDTFComparer/src/gdtf_comparer/gui/table_model.py` lines 46-54
**Apply to:** every new module/class/function this phase adds
Every module opens with a one-paragraph summary docstring naming the relevant decision IDs (D-01..D-06, ATTR-01/02, DIFF-01) it satisfies; every public function/class uses `Parameters:`/`Returns:`/`Raises:` sections. Match this exactly in `attribute_picker.py` and the new proxy classes — it is the dominant, unbroken convention across the entire `core/` and `gui/` packages.

## No Analog Found

None. Every file in this phase's scope has at least a role-match (event-driven GUI widgets against `QListWidget` usage in `main_window.py`) or an exact self-analog (files extended in place). The one open architectural risk — where the new "available (category, attribute) catalog" function should live — is not a missing-analog problem but a constraint documented above (Shared Patterns: Core/GUI Import Boundary) and in RESEARCH.md Pitfall 1.

## Metadata

**Analog search scope:** `src/gdtf_comparer/core/`, `src/gdtf_comparer/gui/`, `tests/core/`, `tests/gui/`, `tests/` (root), plus `.venv/lib/python3.12/site-packages/{pygdtf,qt_material}` referenced only for third-party API shape (not as pattern analogs — no first-party code copies from vendored packages)
**Files scanned:** 8 first-party source files read in full (`core/models.py`, `core/comparator.py`, `core/extract.py`, `core/errors.py`, `gui/table_model.py`, `gui/main_window.py`, `gui/theme.py`, `tests/conftest.py`), plus 5 test files read in full or in relevant part (`tests/test_architecture.py`, `tests/core/test_extract.py`, `tests/core/test_comparator.py`, `tests/core/test_models.py` (grep), `tests/gui/test_namespaced_rows.py`, `tests/gui/test_theme.py`)
**Pattern extraction date:** 2026-09-29
