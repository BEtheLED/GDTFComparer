# Phase 2: Attribute Browsing & Diff Highlighting - Context

**Gathered:** 2026-09-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the hardcoded two-category attribute display (Beam, Physical Properties) with the full GDTF attribute set (60+ properties), organized into a browsable/searchable picker the user checks attributes in, and visually highlight which values differ between the target and each comparison file in the results table. Compare-profile save/reload (ATTR-03) and CSV export (EXPORT-01/EXPORT-02) are explicitly out of this phase's scope — Phase 3's job.

</domain>

<decisions>
## Implementation Decisions

### Attribute Grouping & Picker UI
- **D-01:** The full attribute set is organized into collapsible sections by category (not a flat list, not just adding more rows to today's Category/Element/Attribute table) — the user picks attributes from this grouped structure rather than scanning one long list.
- **D-02:** The attribute picker lives in an always-visible side panel next to the results table (not a separate dialog/window opened on demand) — no extra click to see or change the current selection.

### Selection Mechanism
- **D-03:** Selection is explicit checkboxes per attribute; the search box only narrows what's *visible* in the picker, it does not itself determine what's included in the comparison. The checked set is the source of truth for what gets compared. — **Reversibility:** costly — Phase 3's ATTR-03 ("save/name a subset of selected attributes as a reusable compare profile") will persist this checked-set as the thing a profile saves; switching to filter-as-selection later would change what a saved profile actually represents.
- **D-04:** On first use (no prior selection), the picker defaults to today's two categories checked (Beam, Physical Properties) — everything else starts unchecked. Matches current behavior until the user opts into more.

### Diff Highlighting
- **D-05:** Differing values are marked with a color highlight on just the differing cell(s) — not the whole row.
- **D-06:** Add a "show differences only" toggle on the results table that hides rows where nothing differs, on top of the cell highlighting (not a replacement for it).

### Claude's Discretion
- Exact grouping/labeling of the non-Beam/Physical categories pulled from pygdtf's object model (e.g. how DMX channels, geometries, wheels, properties get bucketed and named as picker sections).
- Exact highlight color/styling for differing cells — should follow the qt-material theme (light/dark) established in Phase 1 (D-05/D-06 of Phase 1 context), not a hardcoded color that only works in one theme.
- Exact picker widget choice and panel width/layout details.
- Whether the "show differences only" toggle is a checkbox, switch, or button — functional behavior is locked, exact widget is not.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/PROJECT.md` — core value, constraints (milestone-level)
- `.planning/REQUIREMENTS.md` — Phase 2 covers ATTR-01, ATTR-02, DIFF-01
- `.planning/ROADMAP.md` — Phase 2 goal and success criteria

### Prior Phase Decisions (Phase 1)
- `.planning/phases/01-foundation-rebuild/01-CONTEXT.md` — D-09 (pygdtf's full object model is wrapped directly, not flattened — this phase's full attribute set comes from that model), D-10 (Phase 1 deliberately kept only 2 categories displayed; full browsing was explicitly deferred to this phase), D-13 (ComparisonResult/ComparisonRow contract this phase builds on)

### Existing Code
- `src/gdtf_comparer/core/models.py` — `DISPLAY_CATEGORIES` (the 2-category hard filter this phase must relax/replace), `AttributeKey` (already carries `.category`), `ComparisonRow.any_differs` (unused row-level predicate, docstring explicitly earmarks it for this phase's diff highlighting)
- `src/gdtf_comparer/core/comparator.py` — `compare()` (filters to `DISPLAY_CATEGORIES` at the core layer; needs to accept/produce the full set with GUI-side selection instead)
- `src/gdtf_comparer/gui/table_model.py` — `ComparisonTableModel` (only implements `DisplayRole`/`ToolTipRole` today — needs a role for cell background highlighting), `UppercaseHeaderProxyModel` (existing pattern for a thin Qt proxy model — the "differences only" toggle should follow this proxy-model pattern, e.g. a `QSortFilterProxyModel` subclass, rather than modifying `ComparisonTableModel` directly)
- `src/gdtf_comparer/gui/main_window.py` — `MainWindow.create_widgets()` (where the new side panel attaches), `on_comparison_ready()` (where the differences-only toggle and highlighting get wired to a fresh result)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ComparisonRow.any_differs` and the per-comparison `differs` tuple (`core/models.py`) — already computed by `compare()`; reuse directly for both cell-level highlighting and the differences-only filter, no new diff logic needed.
- `AttributeKey.category` — already the namespaced category string pygdtf's model produces; the picker's collapsible sections group by this field directly.

### Established Patterns
- Core/GUI separation (D-16, Phase 1) — the GUI must not import `pygdtf` directly. The full category/attribute list for the picker must be exposed through the `core` layer (e.g. from `FixtureModel`/`FixtureType`), not derived by the GUI reaching into pygdtf objects itself.
- Qt proxy-model layering (`UppercaseHeaderProxyModel`) — the established way to add view-only behavior without touching the source model. The differences-only toggle should follow this same pattern (a filter proxy) rather than adding filtering logic inside `ComparisonTableModel`.

### Integration Points
- `DISPLAY_CATEGORIES` in `core/models.py` is currently a hard filter applied inside `compare()` — this phase needs to relax that at the core layer (produce rows for all categories) and apply the user's checked-attribute selection at the GUI layer instead, so the core `compare()` API stays a pure function unaware of UI selection state.
- The results table (`ComparisonTableModel`) and the new attribute-picker panel both need to talk to whatever holds the "currently selected attributes" state — this is new state that doesn't exist yet in `MainWindow`.

</code_context>

<specifics>
## Specific Ideas

No specific visual reference supplied for the highlight color — follow the qt-material theme direction already established in Phase 1 (Claude's discretion, see above).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within Phase 2 scope. Saving/reloading attribute selections as named "compare profiles" (ATTR-03) and CSV export (EXPORT-01/EXPORT-02) were correctly kept out of scope — those are Phase 3.

</deferred>

---

*Phase: 2-Attribute Browsing & Diff Highlighting*
*Context gathered: 2026-09-29*
