# Phase 2: Attribute Browsing & Diff Highlighting - Research

**Researched:** 2026-09-29
**Domain:** PySide6/Qt model-view UI over an existing typed Python core (pygdtf object-model traversal, Qt proxy models, qt-material theming)
**Confidence:** MEDIUM-HIGH (architecture: HIGH, verified by reading the actual source; exact "60+" attribute source mapping: MEDIUM, flagged as assumption)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The full attribute set is organized into collapsible sections by category (not a flat list, not just adding more rows to today's Category/Element/Attribute table) — the user picks attributes from this grouped structure rather than scanning one long list.
- **D-02:** The attribute picker lives in an always-visible side panel next to the results table (not a separate dialog/window opened on demand) — no extra click to see or change the current selection.
- **D-03:** Selection is explicit checkboxes per attribute; the search box only narrows what's *visible* in the picker, it does not itself determine what's included in the comparison. The checked set is the source of truth for what gets compared. — **Reversibility:** costly — Phase 3's ATTR-03 ("save/name a subset of selected attributes as a reusable compare profile") will persist this checked-set as the thing a profile saves; switching to filter-as-selection later would change what a saved profile actually represents.
- **D-04:** On first use (no prior selection), the picker defaults to today's two categories checked (Beam, Physical Properties) — everything else starts unchecked. Matches current behavior until the user opts into more.
- **D-05:** Differing values are marked with a color highlight on just the differing cell(s) — not the whole row.
- **D-06:** Add a "show differences only" toggle on the results table that hides rows where nothing differs, on top of the cell highlighting (not a replacement for it).

### Claude's Discretion

- Exact grouping/labeling of the non-Beam/Physical categories pulled from pygdtf's object model (e.g. how DMX channels, geometries, wheels, properties get bucketed and named as picker sections).
- Exact highlight color/styling for differing cells — should follow the qt-material theme (light/dark) established in Phase 1 (D-05/D-06 of Phase 1 context), not a hardcoded color that only works in one theme.
- Exact picker widget choice and panel width/layout details.
- Whether the "show differences only" toggle is a checkbox, switch, or button — functional behavior is locked, exact widget is not.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within Phase 2 scope. Saving/reloading attribute selections as named "compare profiles" (ATTR-03) and CSV export (EXPORT-01/EXPORT-02) were correctly kept out of scope — those are Phase 3.

### Phase Boundary (from CONTEXT.md)

Replace the hardcoded two-category attribute display (Beam, Physical Properties) with the full GDTF attribute set (60+ properties), organized into a browsable/searchable picker the user checks attributes in, and visually highlight which values differ between the target and each comparison file in the results table. Compare-profile save/reload (ATTR-03) and CSV export (EXPORT-01/EXPORT-02) are explicitly out of this phase's scope — Phase 3's job.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ATTR-01 | User can browse/search the full set of GDTF attributes (60+ properties) for a fixture, not just the two hardcoded categories (Beam, Physical Properties) | Architecture Patterns (Pattern 1: generalized extraction), Architecture Responsibility Map, Common Pitfalls 1/3/4, Open Question 1 (which pygdtf collection satisfies "60+") |
| ATTR-02 | User can select which attributes to include in a comparison via search/filter | Architecture Patterns (Pattern 2: selection key is (category, attribute), not AttributeKey), Don't Hand-Roll (QTreeWidget checkable items, QSortFilterProxyModel), Open Question 2 (default-selection semantics) |
| DIFF-01 | The comparison table visually highlights which attribute values differ between the target and each comparison file | Architecture Patterns (Pattern 3: reuse ComparisonRow.differs, Pattern 4: theme-aware color), Common Pitfalls (get_theme() caching), Assumption A2/A4 |
</phase_requirements>

## Summary

This phase has almost no *external* research surface — no new libraries, no new frameworks, no network calls. Everything needed already exists in the repo: `pygdtf` 1.4.5 (pinned, `[VERIFIED: tests/test_fixture_builder.py:12-18]`, quote below) exposes a much larger object model than the two categories Phase 1 chose to surface, PySide6 already ships every widget needed (checkable `QTreeWidget`, `QSortFilterProxyModel`), and `qt-material` already exposes a small, parseable theme-color API that Phase 1's `theme.py` already uses. The work is almost entirely **internal architecture**: (1) generalize `core/extract.py`'s per-category, hand-rolled "declared vs. default" extraction loops into a reusable pattern that can cover several new categories without duplicating the same 20-line loop four more times, (2) relax `core/comparator.py`'s hard `DISPLAY_CATEGORIES` filter and introduce a clear, new selection concept — **(category, attribute-name) pairs**, not full `AttributeKey`s — as the thing the picker checks and the thing that filters rows, (3) add a `BackgroundRole` to `ComparisonTableModel` driven by the already-computed `ComparisonRow.differs` tuple (zero new diff logic needed — it's already computed and already unit-tested, just unused per Phase 1's own docstring), and (4) add two `QSortFilterProxyModel`-style filters (attribute selection, differences-only) that slot into the existing proxy chain next to `UppercaseHeaderProxyModel`.

The one real open question is *scope*: pygdtf's full object model (Wheels, Emitters, Filters, DMX Modes → DMX Channels → Logical Channels → Channel Functions → Channel Sets, Connectors, Protocols, Revisions...) is enormous — DMX Channels alone is a 4-level-deep nested structure with per-DMX-mode variability that would be its own multi-plan effort. The phase's "60+ properties" success criterion is very plausibly satisfied by a single new category — the fixture's own `<AttributeDefinitions><Attributes>` collection (`fixture_type.attributes`, a flat list of GDTF's standardized DMX-function attributes: Pan, Tilt, Dimmer, Shutter1, Gobo1, Zoom, Frost1, Color1, CTO, etc.) — because real-world moving-light GDTF files routinely declare 60–150 of these. This document recommends that as the primary new category, plus two small, low-risk additions (expanded Physical Properties: LegHeight/OperatingTemperature; Wheels), and explicitly recommends **deferring** DMX Channels/Connectors/Protocols/Revisions to a later phase. This scope call is `[ASSUMED]` and belongs in front of the user/planner as a confirmable decision, not silently baked into a plan.

**Primary recommendation:** Add one new core category sourced from `fixture_type.attributes` (the GDTF-standardized DMX Attribute Definitions) as the main lever for "60+ properties," reuse the existing `ComparisonRow.differs` field for cell highlighting (no new diff logic), and use `(category, attribute)` pairs — not full `AttributeKey`s — as the picker's selection unit.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Full attribute catalog extraction (pygdtf → typed dict) | Core (`core/extract.py`) | — | Only `core` may import `pygdtf` (D-16, enforced by `tests/test_architecture.py::test_gui_does_not_import_parsing_libraries`) |
| Category relaxation / row production | Core (`core/comparator.py`) | — | `compare()` must stay a pure, selection-unaware function (Integration Points, 02-CONTEXT.md) |
| "Available (category, attribute) catalog" for the picker | Core (new function, `core/comparator.py` or `core/models.py`) | — | GUI must not inspect `pygdtf`/`FixtureType` directly to build picker sections; must go through the core service surface |
| Attribute picker UI (checkable tree, search box) | GUI (`gui/main_window.py`, new widget) | — | Always-visible side panel (D-02); pure presentation + selection state |
| Selection state (checked attributes) | GUI (`MainWindow`, new instance state) | — | New state that doesn't exist yet per 02-CONTEXT.md Integration Points |
| Row filtering by selection / differences-only | GUI (`gui/table_model.py`, new proxy model(s)) | — | Follows the existing `UppercaseHeaderProxyModel` proxy pattern (D-established in Phase 1) |
| Cell-level diff highlighting (color) | GUI (`gui/table_model.py` `data()` + `gui/theme.py`) | — | Needs Qt (`QColor`) and the live qt-material theme; `ComparisonRow.differs` (core) is only the boolean input |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pygdtf | 1.4.5 (pinned) | GDTF object model | Already the project's parser (PARSE-01, Phase 1). `[VERIFIED: tests/test_fixture_builder.py:12-18]` — `assert importlib.metadata.version("pygdtf") == "1.4.5"` |
| PySide6 | 6.11.2 (pinned) | Qt bindings — `QSortFilterProxyModel`, `QTreeWidget`, `QColor` | Already the project's GUI toolkit (UI-01/UI-02, Phase 1). `[VERIFIED: tests/test_fixture_builder.py:13]` — `assert importlib.metadata.version("PySide6") == "6.11.2"` |
| qt-material | 2.17 (pinned) | Theme-aware colors for diff highlighting | Already the project's theming layer (D-05..D-08, Phase 1). `[VERIFIED: tests/test_fixture_builder.py:16]` — `assert importlib.metadata.version("qt-material") == "2.17"` |

**No new packages are required for this phase.** Every capability needed (checkable tree widget, row filtering, background-color cell painting, theme color lookup) is already available in the pinned stack.

### Supporting
None — no new dependency is needed.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `QTreeWidget` with checkable items for the picker | `QTreeView` + custom `QAbstractItemModel` | `QTreeWidget` is far less code for a static, non-huge (hundreds of leaves, not thousands) checkable tree; a custom model only pays off if the picker later needs to bind live to a changing catalog across many fixtures per frame — not the case here (Claude's discretion per 02-CONTEXT.md) |
| Two `QSortFilterProxyModel` subclasses (selection filter, diff-only filter) chained | One custom `QSortFilterProxyModel` with two independent predicates in a single `filterAcceptsRow` | Chaining is more idiomatic Qt (each filter is independently testable, mirrors `UppercaseHeaderProxyModel`'s existing single-purpose-proxy pattern) but adds one extra indirection layer; a combined proxy is fewer moving parts. Either is reasonable — planner's call, not user-locked. |

## Package Legitimacy Audit

**Not applicable.** This phase adds no new external packages (npm/PyPI/crates or otherwise). All work is against the already-pinned `pygdtf`, `PySide6`, and `qt-material`.

## Architecture Patterns

### System Architecture Diagram

```
                     ┌─────────────────────────────────────────────┐
                     │              MainWindow (GUI)                │
                     │                                               │
  target .gdtf   ──▶ │  ComparisonWorker (QThread) ──▶ compare_files │
  compare .gdtf(s)   │         (core, unchanged D-14/D-15)           │
                     │                    │                          │
                     │                    ▼                          │
                     │           ComparisonResult (ALL categories,   │
                     │           unfiltered — core stays selection-  │
                     │           unaware, per Integration Points)    │
                     │                    │                          │
                     │      ┌─────────────┴──────────────┐           │
                     │      ▼                             ▼           │
                     │  available_attributes()      ComparisonTableModel
                     │  (new core fn: distinct       (adds BackgroundRole
                     │   (category, attribute)        from row.differs)
                     │   pairs, for picker)                 │           │
                     │      │                                │           │
                     │      ▼                                ▼           │
                     │  Attribute Picker Panel      AttributeSelectionProxy
                     │  (QTreeWidget, checkboxes,    (filters rows by
                     │   search box narrows          checked (category,
                     │   *visible*, not *checked*)    attribute) set)
                     │      │                                │           │
                     │      │ checked-set changed            ▼           │
                     │      └───────────────────────▶ DifferencesOnlyProxy
                     │                                (hides rows where
                     │                                 row.any_differs
                     │                                 is False, if toggled)
                     │                                       │           │
                     │                                       ▼           │
                     │                            UppercaseHeaderProxyModel
                     │                                       │           │
                     │                                       ▼           │
                     │                                 QTableView         │
                     └─────────────────────────────────────────────┘
```

A reader can trace: pick files → worker → `compare_files` (unfiltered, core) → table model (all rows + diff flags) → two stacked view-only proxies (attribute selection, differences-only) → header proxy → view. The picker panel reads the *catalog* (all distinct category/attribute pairs seen in the current result) independently of the *filtered display*.

### Recommended Project Structure
```
src/gdtf_comparer/
├── core/
│   ├── extract.py       # add new attribute-spec-driven extraction for
│   │                     #   DMX Attributes (+ optionally Wheels, extended
│   │                     #   Physical Properties) using a shared helper
│   ├── models.py         # DISPLAY_CATEGORIES relaxed/renamed; AttributeKey
│   │                     #   unchanged (category/element_path/attribute
│   │                     #   already generic enough for new categories)
│   └── comparator.py     # compare() drops the DISPLAY_CATEGORIES filter;
│                          #   new available_attributes()-style function
├── gui/
│   ├── attribute_picker.py   # NEW: checkable QTreeWidget + search QLineEdit
│   ├── table_model.py         # add BackgroundRole; add the 1-2 new proxy
│   │                           #   model classes next to UppercaseHeaderProxyModel
│   └── main_window.py         # wire picker panel into layout; own the
│                                #   checked-set state; own the diff-only toggle
└── ...
tests/
├── core/test_extract.py       # new tests for the new category's presence-vs-
│                                #   default behavior (mirrors existing Beam/Model tests)
├── core/test_comparator.py    # update: DISPLAY_CATEGORIES-based assertions
│                                #   need to change since the filter is relaxed
└── gui/                        # new tests for picker, proxies, highlight role
```

### Pattern 1: Generalize the "declared vs. default" extraction loop

**What:** `core/extract.py` currently has two near-identical loops: one for `BEAM_ATTRIBUTES` over `GeometryBeam` nodes, one for `MODEL_ATTRIBUTES` over `Model` entries. Each does: for every `(gdtf_xml_name, python_field_name)` pair, check `gdtf_name in element.attrib` (presence), else `None`; else read `getattr(node, field_name)`, with a special case for enum-valued fields (`BeamType`) needing `.value`.

**When to use:** Every new category this phase adds (DMX Attributes from `fixture_type.attributes`, optionally Wheels, optionally extended Physical Properties) needs exactly this same presence-check-then-read shape, because pygdtf backfills GDTF-spec defaults everywhere, not just Beam/Model (verified in `pygdtf/properties.py:33-65` for `Properties.weight/leg_height/operating_temperature_low/operating_temperature_high`, and in `pygdtf/value.py:164-166` for `BeamType`'s own default-value enum pattern, which the existing code already special-cases).

**Example (real signature to generalize from, verbatim from the file read this session):**
```python
# Source: src/gdtf_comparer/core/extract.py:279-290 (existing BEAM_ATTRIBUTES loop)
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

**Recommendation:** Extract this into one shared helper (e.g. `_extract_scalar_attributes(node, element, specs, category, element_path, attributes)`) parameterized by a spec tuple that also carries a value-transform callable (default `float`, override to `lambda v: v.value` for enum fields, override to `str` for plain strings) — replacing 2 duplicated ~15-line loops today and preventing 2-4 more near-duplicates as new categories are added. This is the single highest-leverage refactor for this phase's "Don't Hand-Roll" concern.

### Pattern 2: Selection key is `(category, attribute)`, not full `AttributeKey`

**What:** `AttributeKey(category, element_path, attribute)` is per-*instance* (e.g. `("Beam", "Body/Head1/Beam", "BeamAngle")` and `("Beam", "Body/Head2/Beam", "BeamAngle")` are two different rows for the same logical attribute on two different geometry instances). The picker (D-01) shows checkboxes for *attribute names within a category*, not per-instance rows — a fixture with 6 beam geometries should show one "BeamAngle" checkbox, not six.

**When to use:** Any code that reads or writes "the user's selection" (default-selection on first use per D-04, the checked-set the picker mutates, the predicate the attribute-selection proxy filters rows by) must operate on `(row.key.category, row.key.attribute)`, never on the full `AttributeKey`.

**Why this matters:** Getting this wrong means either (a) the picker has to show one checkbox per geometry-instance-and-attribute combination (unusable UX at 60+ properties × N geometries), or (b) a fixture with more geometry instances than the target silently shows unchecked rows the user thought they'd already selected. This distinction is not called out explicitly in 02-CONTEXT.md's decisions and is worth flagging to the planner/user as a locked-in interpretation of D-01/D-03, not an open style choice.

### Pattern 3: Reuse `ComparisonRow.differs` for both highlighting and the diff-only toggle

**What:** `ComparisonRow.differs: tuple` (one bool per comparison file) and `ComparisonRow.any_differs` (property, `any(self.differs)`) are already computed by `compare()` and already unit-tested. `[VERIFIED: src/gdtf_comparer/core/models.py:99-108]`:
```python
@property
def any_differs(self) -> bool:
    """Return True if any comparison value differs from the target.

    Row-level predicate kept as intended future surface for Phase 2 diff
    highlighting (DIFF-01) and Phase 3 diff-only export (EXPORT-02).
    Review IN-01 decided to keep it unused in Phase 1; exercised by
    tests/core/test_models.py (Plan 01-07).
    """
    return any(self.differs)
```

**When to use:** Cell highlighting (D-05): `ComparisonTableModel.data()` should return a `QColor` for `Qt.ItemDataRole.BackgroundRole` when `column >= COL_TARGET + 1` (a comparison-value column, not the Target column itself) and `row.differs[comparison_index]` is `True`. The differences-only toggle (D-06) filters using `row.any_differs` directly in a proxy's `filterAcceptsRow`. **No new diff-computation logic is needed anywhere in this phase** — both features are pure consumers of an already-correct, already-tested field.

**Example:**
```python
# gui/table_model.py — data(), new branch
if role == Qt.ItemDataRole.BackgroundRole:
    if column > self.COL_TARGET:
        comparison_index = column - self.COL_TARGET - 1
        if 0 <= comparison_index < len(row.differs) and row.differs[comparison_index]:
            return self._highlight_color  # cached QColor, see Pitfall below
    return None
```

### Pattern 4: Theme-aware highlight color via `qt_material.get_theme()`

**What:** `qt_material.get_theme(theme_name, invert_secondary=...)` parses the same theme XML `theme.py` already references (`dark_blue.xml` / `light_blue.xml`) and returns a plain `dict[str, str]` of hex colors. `[VERIFIED: .venv/lib/python3.12/site-packages/qt_material/__init__.py:162-230]` — the function signature and return shape (confirmed by reading the source this session):
```python
def get_theme(theme_name, invert_secondary=False):
    ...
    document = parse(theme)
    theme = {
        child.getAttribute("name"): child.firstChild.nodeValue
        for child in document.getElementsByTagName("color")
    }
    ...
    return theme
```
The actual theme files ship these exact keys `[VERIFIED: .venv/lib/python3.12/site-packages/qt_material/themes/dark_blue.xml, light_blue.xml]`:
```xml
<!-- dark_blue.xml -->
<color name="primaryColor">#448aff</color>
<color name="primaryLightColor">#83b9ff</color>
<color name="secondaryColor">#232629</color>
<color name="secondaryLightColor">#4f5b62</color>
<color name="secondaryDarkColor">#31363b</color>
<color name="primaryTextColor">#ffffff</color>
<color name="secondaryTextColor">#ffffff</color>
<!-- light_blue.xml -->
<color name="primaryColor">#2979ff</color>
<color name="primaryLightColor">#75a7ff</color>
<color name="secondaryColor">#f5f5f5</color>
<color name="secondaryLightColor">#ffffff</color>
<color name="secondaryDarkColor">#e6e6e6</color>
<color name="primaryTextColor">#3c3c3c</color>
<color name="secondaryTextColor">#555555</color>
```
`theme.py` already tracks the currently-applied theme file name on the `QApplication` itself: `[VERIFIED: src/gdtf_comparer/gui/theme.py:29-32,62-66]`:
```python
#: Dynamic Qt property stashed on the QApplication recording the theme name
#: currently applied, so re-applying the same theme is a no-op ...
THEME_PROPERTY = "gdtf_comparer_theme"
...
if app.property(THEME_PROPERTY) == theme:
    return False
apply_stylesheet(app, theme=theme, invert_secondary=theme.startswith("light_"))
app.setProperty(THEME_PROPERTY, theme)
```

**When to use:** Read `QApplication.instance().property(theme.THEME_PROPERTY)` to get the current theme file name, call `qt_material.get_theme(name, invert_secondary=name.startswith("light_"))`, and build a `QColor` from e.g. `theme["primaryLightColor"]` (with reduced alpha, so it reads as a tint/wash over the row's existing alternating-row background rather than a solid block) as the differing-cell highlight. This satisfies D-05/D-06's "follow the qt-material theme, not a hardcoded color" requirement using only already-pinned, already-used code paths.

**Pitfall — do not call `get_theme()` per cell.** `get_theme()` re-parses an XML file from disk and writes to `os.environ` on every call `[VERIFIED: .venv/.../qt_material/__init__.py:198-228]` (`document = parse(theme)`; `os.environ[str(k)] = theme[k]` in a loop). `QAbstractTableModel.data()` is called by Qt extremely frequently (every visible cell, on every scroll/repaint). Compute the highlight `QColor` **once**, cache it on `ComparisonTableModel` (or `MainWindow`), and only recompute it when the theme actually changes — hook into the same live-theme-change path Phase 1 already built (`QApplication.instance().styleHints().colorSchemeChanged`, currently only consumed by `theme.OsThemeFollower` — `[VERIFIED: src/gdtf_comparer/gui/theme.py:79]`, `app.styleHints().colorSchemeChanged.connect(self.on_color_scheme_changed)`). `MainWindow` needs its own connection to this same signal (or a new signal from `OsThemeFollower`) so it can refresh the cached highlight color and repaint (`table_model.dataChanged` emit, or simplest: `beginResetModel()/endResetModel()`) when the OS theme flips live.

### Anti-Patterns to Avoid
- **Filtering in `compare()` by the user's checked attributes:** Keeps `core` a pure, UI-unaware function (already explicitly called out as the required design in 02-CONTEXT.md's Integration Points) — do the filtering in a GUI-layer proxy model instead.
- **One bespoke extraction function per new category, copy-pasted from `BEAM_ATTRIBUTES`'s loop:** This is exactly the "Don't Hand-Roll" trap for this phase — see Pattern 1.
- **Checkbox-per-`AttributeKey` (per geometry instance) in the picker:** See Pattern 2 — breaks down completely at 60+ properties × multiple geometries.
- **Calling `qt_material.get_theme()` inside `data()`:** See Pattern 4 pitfall — a real, measurable performance bug (file I/O + env mutation per cell paint).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Checkable, searchable attribute list grouped by category | A custom tree/list widget with manual checkbox state tracking | `QTreeWidget` with `Qt.ItemFlag.ItemIsUserCheckable` per top-level (category) and child (attribute) item, plus `QTreeWidgetItem.setCheckState` | Built-in tri-state checkbox propagation (checking a category checks all its attributes) comes for free with `QTreeWidget`'s native check-state handling; hand-rolling this with a plain list loses that |
| "Hide rows where nothing differs" / "show only checked attributes" | Manually removing/re-inserting rows in `ComparisonTableModel`, or filtering the `ComparisonResult.rows` tuple before handing it to the model | `QSortFilterProxyModel` subclass overriding `filterAcceptsRow` | This is the exact pattern the codebase already established for `UppercaseHeaderProxyModel` (a different proxy purpose, same "don't touch the source model" philosophy) — `[VERIFIED: src/gdtf_comparer/gui/main_window.py:140-144]`, the view already sits on top of a proxy chain (`table_model` → `header_proxy` → `table_view`), so inserting one or two more proxies before the header proxy is additive, not a redesign |
| Detecting whether a GDTF attribute was "declared" vs. pygdtf's spec-default backfill | Re-implementing pygdtf's default-substitution table per attribute | The existing lockstep tree-walk pattern already built in `core/extract.py` (`iter_geometry_paths`, `_weight_declared`, and the generic `gdtf_name not in element.attrib` presence check) | This is genuinely tricky (T-01-23's `DescriptionMismatchError` fail-closed design exists specifically because pygdtf silently backfills spec defaults with no presence signal of its own) — the existing pattern in this codebase already solves it once; generalize it (Pattern 1), don't reinvent it |

**Key insight:** Every hand-roll risk in this phase already has a working, tested precedent somewhere in this exact codebase (Beam extraction, Model extraction, `UppercaseHeaderProxyModel`, `OsThemeFollower`). The work is *generalizing existing patterns to new categories*, not inventing new mechanisms.

## Common Pitfalls

### Pitfall 1: `test_gui_uses_only_core_service_surface` will fail if the picker's catalog function lives in a new core module
**What goes wrong:** `tests/test_architecture.py` enforces an *allow-list* of core modules the GUI may import from: `[VERIFIED: tests/test_architecture.py:20-24]`
```python
APPROVED_CORE_SURFACE = {
    "gdtf_comparer.core.comparator",
    "gdtf_comparer.core.models",
    "gdtf_comparer.core.errors",
}
```
If the new "available (category, attribute) pairs for the picker" function is added in a brand-new module (e.g. `core/catalog.py`), the GUI importing it will fail this test with a real, correct violation — not a false positive.
**Why it happens:** The allow-list is intentionally an allow-list, not an auto-discovered set.
**How to avoid:** Either put the new catalog function in `core/comparator.py` or `core/models.py` (both already approved), or add the new module to `APPROVED_CORE_SURFACE` in the same plan/wave that introduces it.
**Warning signs:** `test_gui_uses_only_core_service_surface` failing in CI/local test run right after adding the picker.

### Pitfall 2: `DISPLAY_CATEGORIES` is imported directly by existing tests — relaxing it is a breaking change to test code, not just app code
**What goes wrong:** `tests/core/test_comparator.py` imports `DISPLAY_CATEGORIES` directly: `[VERIFIED: tests/core/test_comparator.py:1-9]`
```python
from gdtf_comparer.core.models import (
    CATEGORY_BEAM,
    CATEGORY_PHYSICAL,
    DISPLAY_CATEGORIES,
    format_value,
)
```
If `compare()`'s filter on `DISPLAY_CATEGORIES` (`core/comparator.py:36`, `if key.category not in DISPLAY_CATEGORIES: continue`) is simply removed and the constant deleted, this import breaks the test suite immediately (`ImportError`), not just silently changes behavior.
**Why it happens:** `DISPLAY_CATEGORIES` currently serves two roles at once — "categories `compare()` filters to" and "the two categories that exist today" — and tests reference the constant directly rather than through `compare()`'s behavior.
**How to avoid:** Decide explicitly whether `DISPLAY_CATEGORIES` is deleted (update the test import) or repurposed (e.g., renamed to something like `LEGACY_DEFAULT_CATEGORIES` and reused only for D-04's "first-use default selection", not as a `compare()` filter). Either way this must be an explicit task, not an incidental side effect.
**Warning signs:** `pytest tests/core/test_comparator.py` failing on collection (import error) after the core change lands.

### Pitfall 3: pygdtf backfills spec defaults far beyond Beam/Weight — every new field needs its own presence check
**What goes wrong:** Assuming a new field (e.g., `Attribute.physical_unit`, `Properties.leg_height`) is `None`/absent just because the fixture's own XML didn't set a value is wrong — pygdtf substitutes GDTF-spec defaults silently. `[VERIFIED: .venv/.../pygdtf/properties.py:33-46]`:
```python
class Properties(BaseNode):
    def __init__(
        self,
        weight: float = 0,
        operating_temperature_low: float = 0,
        operating_temperature_high: float = 40,
        leg_height: float = 0,
        *args,
        **kwargs,
    ):
```
and `[VERIFIED: .venv/.../pygdtf/value.py:164-166]`:
```python
class BeamType(Enum):
    permitted = ["Wash", "Spot", "None", "Rectangle", "PC", "Fresnel", "Glow"]
    _default = "Wash"
```
This is precisely the bug class Phase 1 already fixed once for Beam/Weight (Plan 01-06, `DescriptionMismatchError`'s whole reason for existing, per T-01-23) — it will recur for every new field this phase adds unless the same presence-check-against-raw-XML pattern is applied uniformly.
**Why it happens:** pygdtf's job is to give callers a complete, always-populated object model for rendering a fixture; it has no concept of "the comparer needs to know if this was declared."
**How to avoid:** Apply Pattern 1's generalized presence-check helper to every new field, never `getattr(node, field, None)` alone.
**Warning signs:** A comparison shows identical values for two fixtures that actually differ in whether they declared the field at all (silently "N/A-masking" a real difference, or worse, showing a false non-difference).

### Pitfall 4: DMX Channels is a 4-level nested structure with per-DMX-mode variability — do not attempt full coverage in this phase without scoping it explicitly
**What goes wrong:** `pygdtf/__init__.py` shows `DmxMode → DmxChannel → LogicalChannel → ChannelFunction → ChannelSet` as a real, deeply nested chain `[VERIFIED: .venv/.../pygdtf/__init__.py — class declarations at lines 1369, 1571, 1816, 1896, 2171]` (`class DmxMode`, `class DmxChannel`, `class LogicalChannel`, `class ChannelFunction`, `class ChannelSet`). Each fixture can declare multiple DMX modes with different channel counts and different channel functions per mode. Treating this the same way as Beam/Model (a flat per-instance loop) does not work — the "element path" concept would need to include the DMX mode name, channel offset, logical channel, and channel function, and two fixtures being compared may not even share DMX mode names.
**Why it happens:** It looks like "just another category" from the outside, but it's structurally the most complex part of the GDTF spec.
**How to avoid:** Treat DMX Channels as explicitly out of scope for this phase (recommend deferring to a later phase or a dedicated follow-up), and confirm that with the user/planner rather than discovering the scope blowout mid-plan.
**Warning signs:** A task estimate for "add DMX Channels category" that doesn't mention DMX-mode-scoping at all is under-scoped.

## Code Examples

### Extending `make_gdtf` test fixture for new categories (Wave 0 gap)
```python
# Source: tests/conftest.py:15-75 (existing pattern to extend)
# build_description_xml() currently only accepts models_xml / geometries_xml
# as raw-XML injection points, and hardcodes an always-empty <Attributes/>
# and <Wheels/> — [VERIFIED: tests/conftest.py:56-61]:
#     "    <AttributeDefinitions>\n"
#     "      <ActivationGroups/>\n"
#     "      <FeatureGroups/>\n"
#     "      <Attributes/>\n"
#     "    </AttributeDefinitions>\n"
#     "    <Wheels/>\n"
# New tests for the DMX Attributes / Wheels categories need build_description_xml
# (and the make_gdtf fixture that wraps it) extended with attributes_xml=/
# wheels_xml= injection points, following the exact same optional-raw-XML-
# string parameter pattern models_xml/geometries_xml already use.
```

### Generalized presence-check extraction helper (sketch, not verbatim from repo — new code)
```python
# New in core/extract.py — generalizes the existing BEAM_ATTRIBUTES/
# MODEL_ATTRIBUTES loops (core/extract.py:279-290, :305-311)
def _extract_scalar_attributes(
    node: Any,
    element: Element,
    specs: Sequence[Tuple[str, str, Callable[[Any], AttributeValue]]],
    category: str,
    element_path: str,
    attributes: Dict[AttributeKey, AttributeValue],
) -> None:
    """Apply the declared-vs-default presence check uniformly.

    specs: (gdtf_xml_name, python_field_name, value_transform) triples.
    value_transform receives the raw pygdtf attribute value and returns the
    AttributeValue to store (e.g. float, str, or `lambda v: v.value` for an
    enum-like pygdtf value type).
    """
    for gdtf_name, field_name, transform in specs:
        if gdtf_name not in element.attrib:
            value: AttributeValue = None
        else:
            raw_value = getattr(node, field_name, None)
            value = transform(raw_value) if raw_value is not None else None
        attributes[AttributeKey(category, element_path, gdtf_name)] = value
```

## State of the Art

Not applicable — this is an internal-architecture phase over an already-current, already-pinned stack (pygdtf 1.4.5, PySide6 6.11.2, qt-material 2.17 were all selected and verified during Phase 1's research; no newer major version or deprecation affects this phase).

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The phase's "60+ properties" success criterion is most tractably (and most plausibly, in domain terms) satisfied primarily by adding `fixture_type.attributes` (the `<AttributeDefinitions><Attributes>` collection) as a new category, rather than by exhaustively covering every pygdtf category | Summary, Architecture Patterns | If wrong, the planner may under- or over-scope the new-category work; no real GDTF sample file was available in this repo to directly count a real fixture's declared `<Attribute>` entries and confirm the "60+" figure empirically — this was reasoned from GDTF domain knowledge (training data), not measured this session |
| A2 | Only Beam-column comparison cells (not the Target column itself) should receive the diff-highlight background | Pattern 3 | D-05 says "the differing cell(s)" without specifying whether Target is included; if the intended UX is to highlight Target too when any comparison differs, this needs a one-line change to the `data()` branch |
| A3 | Wheels and extended Physical Properties (LegHeight, OperatingTemperature) are worth adding in this phase as secondary categories alongside DMX Attributes | Architecture Patterns, Recommended Project Structure | These are small/low-risk if added, but not required to hit "60+"; if the planner wants a tighter MVP, these could be deferred without threatening the phase's success criteria |
| A4 | A single combined highlight color (`primaryLightColor` at reduced alpha) reads clearly as "differs" in both `dark_blue.xml` and `light_blue.xml` without user testing | Pattern 4 | Purely a visual-design call within Claude's discretion per 02-CONTEXT.md; if it reads poorly against `qt-material`'s alternating-row-color background (`table_view.setAlternatingRowColors(True)`, existing), a different theme key (e.g. a mix with `secondaryLightColor`) may be needed — recommend a quick visual check during execution, not a blocking research item |

## Open Questions

1. **Is `fixture_type.attributes` (DMX Attribute Definitions) actually the intended "full attribute set (60+ properties)," or does the user mean something closer to "every field pygdtf exposes across the whole object model"?**
   - What we know: `fixture_type.attributes` is a flat, single-level list (no DMX-mode nesting) whose count on real fixtures commonly reaches 60-150, making it the single most direct match for the stated success criterion's number.
   - What's unclear: 02-CONTEXT.md's Claude's-discretion note explicitly lists "DMX channels, geometries, wheels, properties" as example bucket names, which could imply DMX Channels (the deeply-nested structure, not the flat Attribute Definitions) was intended.
   - Recommendation: Confirm with the user during planning/discuss that "DMX channels" in that note refers to the flat `<AttributeDefinitions>` vocabulary (Pan/Tilt/Dimmer/etc., i.e. what this document calls "DMX Attributes") and not the nested per-mode `DmxChannel` structure, given Pitfall 4's scope risk if it's the latter.

2. **Should the picker's default-checked state (D-04: "today's two categories checked") pre-check the *categories* (Beam, Physical Properties) as whole units, or every individual attribute currently inside them?**
   - What we know: Functionally identical today (Beam has 6 attributes, Physical Properties has 4: Weight/Width/Height/Length) — but diverges the moment Physical Properties gains LegHeight/OperatingTemperature (Assumption A3): should those newly-added Physical-Properties attributes also start pre-checked, or only the original four?
   - What's unclear: 02-CONTEXT.md doesn't address this because it predates the physical-properties-expansion idea.
   - Recommendation: Default-check by category membership at time of picker construction (so newly-added attributes within an already-"on" category are checked too) — matches D-04's literal wording ("today's two categories checked") more directly than a hardcoded list of the exact four legacy attribute names.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | ✓ | 3.12.13 | — |
| pytest | Test suite | ✓ | 9.1.1 | — |
| pygdtf, PySide6, qt-material | Core/GUI | ✓ (pinned in venv) | 1.4.5 / 6.11.2 / 2.17 | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-qt 4.5.0 `[VERIFIED: tests/test_fixture_builder.py:12-18]` |
| Config file | none found at repo root — pytest auto-discovers `tests/` (both `tests/core/` and `tests/gui/` are scanned) |
| Quick run command | `pytest tests/core -x -q` (core, no Qt event loop needed) or `pytest tests/gui -x -q` (GUI, needs `QT_QPA_PLATFORM=offscreen`, already set in `tests/conftest.py:5`) |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ATTR-01 | New category(ies) extracted with correct declared-vs-default presence semantics | unit | `pytest tests/core/test_extract.py -x -q` | ✅ (extend existing file, mirrors `test_omitted_weight_is_none_not_zero` etc.) |
| ATTR-01 | `compare()` no longer drops non-Beam/Physical rows | unit | `pytest tests/core/test_comparator.py -x -q` | ✅ (existing file; needs the `DISPLAY_CATEGORIES` import fixed per Pitfall 2) |
| ATTR-01 | Picker shows a section per category with checkable attribute rows, search narrows visibility only | gui | `pytest tests/gui/test_attribute_picker.py -x -q` | ❌ Wave 0 — new file |
| ATTR-02 | Only checked attributes appear in the results table | gui | `pytest tests/gui/test_attribute_selection.py -x -q` | ❌ Wave 0 — new file |
| ATTR-02 | First-use default selection = today's two categories (D-04) | gui | same file as above | ❌ Wave 0 |
| DIFF-01 | Differing cells get a `BackgroundRole` color; non-differing cells and the Target column do not | gui | `pytest tests/gui/test_diff_highlighting.py -x -q` | ❌ Wave 0 — new file |
| DIFF-01 | "Show differences only" toggle hides `any_differs is False` rows without removing the highlight logic | gui | same file as above, or `tests/gui/test_differences_only_toggle.py` | ❌ Wave 0 — new file |

### Sampling Rate
- **Per task commit:** `pytest tests/core -x -q` (fast, no Qt) for core-layer tasks; `pytest tests/gui/<new_or_touched_file>.py -x -q` for GUI-layer tasks
- **Per wave merge:** `pytest -q` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — `build_description_xml`/`make_gdtf` need `attributes_xml=` and (if Wheels/extended Properties are in scope) `wheels_xml=`/richer `properties` injection points, following the existing `models_xml=`/`geometries_xml=` pattern (`[VERIFIED: tests/conftest.py:15-146]`)
- [ ] `tests/gui/test_attribute_picker.py` — new
- [ ] `tests/gui/test_attribute_selection.py` — new
- [ ] `tests/gui/test_diff_highlighting.py` — new
- [ ] `tests/core/test_comparator.py` — existing file needs its `DISPLAY_CATEGORIES` import/assertions updated for the relaxed filter (Pitfall 2), not a net-new file but a required edit before other tests in this file can be trusted

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface in this app |
| V3 Session Management | no | No sessions |
| V4 Access Control | no | Single-user desktop app |
| V5 Input Validation | no (no *new* input path) | This phase reads additional fields off the **same already-validated** `description_root`/`fixture_type` object Phase 1's `hardening.prevalidate_gdtf_document()` already produced (`[VERIFIED: src/gdtf_comparer/core/repository.py:51-59]` — `validated = prevalidate_gdtf_document(path)` then `pygdtf.FixtureType(io.BytesIO(validated.archive_bytes))`). No new file is opened, no new zip/XML parse path is introduced; extraction only reads more properties off the same trusted, already-hardened tree. |
| V6 Cryptography | no | N/A |

### Known Threat Patterns for this stack
No new threat surface is introduced by this phase — it adds read-only traversal of an already-validated in-memory object model (`fixture_type`) and an already-validated XML tree (`description_root`), both already covered by Phase 1's `GDTFUnsafeFileError`/size-limit/`defusedxml` hardening (`[VERIFIED: src/gdtf_comparer/core/hardening.py:1-40]`). The one thing to verify during code review: any new extraction code must keep reading from the `description_root` parameter it's handed (never re-open the file, never call `zipfile`/`ElementTree.parse` directly) — consistent with the existing `core/extract.py` module docstring's stated contract ("Extraction never parses XML itself -- it only reads this tree").

## Sources

### Primary (HIGH confidence — read directly this session)
- `src/gdtf_comparer/core/models.py`, `core/comparator.py`, `core/extract.py`, `core/repository.py`, `core/errors.py`, `core/hardening.py` (partial)
- `src/gdtf_comparer/gui/table_model.py`, `gui/main_window.py`, `gui/theme.py`, `gui/worker.py`, `src/gdtf_comparer/app.py`
- `tests/test_architecture.py`, `tests/conftest.py`, `tests/core/test_extract.py`, `tests/core/test_comparator.py`, `tests/test_fixture_builder.py`
- `.venv/lib/python3.12/site-packages/pygdtf/__init__.py`, `pygdtf/geometries.py`, `pygdtf/properties.py`, `pygdtf/value.py` (class declarations and field assignments)
- `.venv/lib/python3.12/site-packages/qt_material/__init__.py` (`get_theme` source), `qt_material/themes/dark_blue.xml`, `light_blue.xml`
- `.planning/phases/02-attribute-browsing-diff-highlighting/02-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/config.json`

### Secondary (MEDIUM confidence)
- General GDTF-spec domain knowledge about typical real-world fixture files declaring 60-150 `<Attribute>` entries in `<AttributeDefinitions>` — not verified against an actual third-party `.gdtf` file in this session (none present in this repo)

### Tertiary (LOW confidence)
- None used as a basis for a recommendation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, all versions verified by reading pinned-version assertions in the repo's own test suite
- Architecture: HIGH — every pattern recommended is either already implemented elsewhere in this exact codebase (verified by reading the source) or a direct, verified Qt/qt-material API
- "60+ properties" scope mapping: MEDIUM — reasoned from GDTF domain knowledge and pygdtf's object model shape, not verified against a real third-party GDTF file; flagged as Assumption A1 and Open Question 1

**Research date:** 2026-09-29
**Valid until:** 60 days (no external/fast-moving dependency; only risk is if the user's mental model of "60+ properties" diverges from Assumption A1 during planning discussion)
