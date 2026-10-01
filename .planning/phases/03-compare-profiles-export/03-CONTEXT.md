# Phase 3: Compare Profiles & Export - Context

**Gathered:** 2026-09-30
**Status:** Ready for planning — WITH AN OPEN SCOPE FLAG (see Decisions, Scope Flag section)

<domain>
## Phase Boundary

Originally: users can save a named subset of selected attributes as a reusable "compare profile" and reload it for future comparisons (ATTR-03), and export comparison results to CSV, both full and diff-only (EXPORT-01, EXPORT-02).

**Scope flag raised during this discussion:** the user does not see a clear need for CSV export and asked to flag EXPORT-01/EXPORT-02 for removal from requirements. This has NOT been applied to REQUIREMENTS.md or ROADMAP.md yet — see the Scope Flag subsection under Decisions. Until that's resolved, treat this phase's confirmed scope as **compare profiles only (ATTR-03)**.

</domain>

<decisions>
## Implementation Decisions

### Profile Concept & Real Workflow
- **D-01:** A "compare profile" is a reusable *spec sheet* of required properties (e.g. color mixing, zoom, max weight, power draw) — not tied to one fixture type. The user's real use case: they know they need certain properties out of a fixture (e.g. starting from a reference like a "MAC Aura XB"), and they reuse that same spec-sheet checklist against completely unrelated candidate fixtures from other manufacturers (e.g. an "R2X Wash") to see at a glance whether a substitute measures up — replacing back-and-forth email with a vendor. This is the primary use case, not a rare edge case — profiles will routinely be loaded against fixtures with a very different attribute catalog than whatever fixture the profile was originally saved from.

### Profile Storage & Reload
- **D-02:** Saved profiles are picked for reload via a dropdown directly in the Attributes side panel (not a separate "Open Profile" dialog).
- **D-03:** Loading a profile **replaces** the currently checked attributes entirely — it does not merge/add onto whatever was already checked. Matches the "pick a spec sheet and run from scratch" workflow.
- **D-04:** Saving a profile under a name that's already in use asks for confirmation before overwriting (not silent overwrite, not a hard block).
- **D-05:** Rename and delete of saved profiles are **in scope for this phase** (not deferred) — the user wants to clean up/update spec sheets over time (e.g. "Moving Head Spec" changing as requirements evolve).

### Profile Portability Across Fixtures
- **D-06:** When a loaded profile's saved properties don't exist on either file in the *current* comparison (i.e., neither the target nor any comparison file has that attribute at all, so no row appears), the app must tell the user explicitly — e.g. a status-bar message like "2 of 6 spec items weren't found in these files." Silently dropping unmatched spec items without telling the user was explicitly rejected: since the user is making go/no-go sourcing decisions from this, they need to know when part of their checklist wasn't actually evaluated, not just see a shorter list and assume everything checked out fine.

### Button Placement
- **D-07:** Save and Manage (rename/delete) controls for profiles sit in the same compact toolbar row at the top of the Attributes side panel, alongside the load dropdown — one consolidated location for all profile actions, consistent with D-02's placement for loading.

### Scope Flag — CSV Export (EXPORT-01, EXPORT-02)
- **D-08:** During discussion the user said "I don't even know why I would need to export" and, when asked directly whether to keep CSV export scoped to this phase or flag it for removal, chose **"Flag it for removal."**
  - **This has not yet been applied to REQUIREMENTS.md or ROADMAP.md.** Before planning or implementing any export work, confirm with the user whether to (a) formally drop EXPORT-01/EXPORT-02 from REQUIREMENTS.md and shrink Phase 3's roadmap goal/success-criteria to profiles only, or (b) proceed with export as originally scoped after all. Do not silently implement or silently skip CSV export — surface this explicitly.
  - **If export does proceed after that confirmation,** conditional answers gathered during this discussion (treat as provisional, not locked, since the feature itself is in question):
    - CSV includes only the attributes currently checked in the side panel (the user's spec sheet), not a full raw dump of every GDTF property.
    - "Differences only" stays binary (matches / doesn't match), same semantics as Phase 2's on-screen highlighting — no stricter pass/fail or tolerance logic (see the deferred Red/Yellow/Green idea below).
    - The CSV includes identifying info (fixture/file names) near the top, since it may be shared with someone outside the app (a vendor, a colleague) rather than kept purely for in-app use.
    - Full export and differences-only export are two separate buttons/actions, not one button with a sub-choice — though the user was not confident in this answer ("I don't know I guess 1"); treat as low-confidence/easily revisited if export proceeds.

### Claude's Discretion
- Exact CSV column layout, file naming convention, and default save location, contingent on the Scope Flag above being resolved in favor of keeping export.
- Visual/layout details of the profile toolbar row (icon vs. text buttons, exact dropdown width, how "N profiles" are listed when many exist).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project & Requirements
- `.planning/PROJECT.md` — core value, constraints (milestone-level)
- `.planning/REQUIREMENTS.md` — Phase 3 covers ATTR-03, EXPORT-01, EXPORT-02 (see Scope Flag — EXPORT-01/02 status is unresolved as of this discussion)
- `.planning/ROADMAP.md` — Phase 3 goal and success criteria (also affected by the Scope Flag)

### Prior Phase Decisions
- `.planning/phases/01-foundation-rebuild/01-CONTEXT.md` — D-13 (ComparisonResult/ComparisonRow typed contract), D-16 (core/GUI separation: core has zero Qt imports)
- `.planning/phases/02-attribute-browsing-diff-highlighting/02-CONTEXT.md` — D-03 (checked (category, attribute) set is the source of truth for what's compared — this is exactly what a profile persists), D-04 (first-use default-selected-categories pattern, analogous to profile defaults)

### Existing Code
- `src/gdtf_comparer/gui/attribute_picker.py` — `AttributePicker.checked_attributes()` (returns the `FrozenSet[(category, attribute)]` a profile must save) and `set_catalog()` (the in-session "pair already known keeps prior choice" logic a profile-load needs to interact with, not duplicate)
- `src/gdtf_comparer/core/comparator.py` — `attribute_catalog(result)` (produces the current run's available (category, attribute) pairs — a loaded profile's saved pairs must be checked against this set to detect D-06's "not found in these files" case)
- `src/gdtf_comparer/core/models.py` — `ComparisonRow.any_differs`, `format_value()` (None → "N/A") — the existing binary differs/matches semantics D-08 keeps for any export, and the same None-handling that already supports "candidate fixture doesn't have this property at all"
- `src/gdtf_comparer/core/repository.py` — `FixtureRepository` (existing pattern for a dedicated, testable loader class — a new profile-persistence component should follow this same shape: a small class with explicit load/save methods, zero Qt imports, typed errors from `core/errors.py` on failure)
- `src/gdtf_comparer/gui/main_window.py` — `create_widgets()` (where the Attributes panel toolbar row attaches, per D-02/D-07), `_apply_attribute_selection()` (existing hook that pushes a checked set into the table — a profile load should drive the same path, not a parallel one)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AttributePicker.checked_attributes()` / the picker's internal `_checked: Set[AttributePair]` — this is exactly the data a "save profile" action persists, and exactly what a "load profile" action needs to push back into the picker (likely via a new `set_checked()`-style method, since today only `set_catalog()` seeds checks and only from `DEFAULT_SELECTED_CATEGORIES`).
- `ComparisonRow.any_differs` and `format_value()`'s `None` → `"N/A"` handling — already gives any future export (if kept) and the D-06 portability warning the exact binary "matches/doesn't match" and "not present" data it needs, with zero new comparison logic required.

### Established Patterns
- `FixtureRepository` (core/repository.py) — small, single-purpose loader class with a typed-error contract (core/errors.py). A new profile-persistence class should mirror this: e.g. `ProfileRepository` or similar, living in `core/`, zero Qt imports (D-16), raising typed errors a GUI layer catches the same way `MainWindow` already catches `GDTFError` subclasses.
- Core/GUI separation (D-16, Phase 1) — profile persistence logic (file I/O, JSON/whatever format) belongs in `core/`, not `gui/`; the GUI only calls into it and renders the result, same as `compare_files()`.

### Integration Points
- `MainWindow.create_widgets()` is where the new profile toolbar row (dropdown + Save + Manage) attaches, inside or just above `self.attributes_group` (per D-02/D-07).
- `AttributePicker.selection_changed` / `_apply_attribute_selection()` is the existing signal chain that pushes a checked set into `AttributeSelectionProxyModel` — loading a profile should set the picker's checked state and let this existing chain do the rest, not bypass it.
- `attribute_catalog(result)` is per-comparison-run (rebuilt each time `on_comparison_ready` fires) — the D-06 "N of M spec items not found" check must compare a loaded profile's saved (category, attribute) pairs against *this* catalog, at the point a profile is loaded (or re-checked after a new comparison runs, since the catalog can change between runs).

</code_context>

<specifics>
## Specific Ideas

The user's concrete example, worth keeping in mind for naming/wording choices in the UI (e.g. empty states, help text): *"I will ask for a type of fixture maybe MAC Aura XB for example, and the company that I am getting the fixture from might not have a MAC Aura but I can say I need these parts like color mixing and zoom and a max weight and as long as I have that I am okay so the company might look and have R2X wash and it fits so they can supply that vs sending me an email."* This is the canonical real-world scenario a saved profile serves — a fixture-replacement/substitution spec check, not a convenience shortcut for repeat work on the same fixture type.

</specifics>

<deferred>
## Deferred Ideas

- **Red/Yellow/Green acceptability rating:** instead of (or alongside) binary "matches/doesn't match," rate each differing property as Red (fails outright, e.g. "color mixing not available"), Yellow (different but acceptable, e.g. "5% over on max weight"), or Green (direct match). Explicitly noted by the user as a future-phase idea, not this one — it requires defining tolerance/acceptability rules per attribute (and per attribute type: numeric tolerance vs. feature presence vs. exact string match), which doesn't exist anywhere in the app today and is a meaningfully bigger feature than this phase's binary diff.

### Reviewed Todos (not folded)
None — no pending todos matched Phase 3 (`todo_count: 0`).

</deferred>

---

*Phase: 3-Compare Profiles & Export*
*Context gathered: 2026-09-30*
