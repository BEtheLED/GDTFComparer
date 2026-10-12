# Phase 03 — UI Review

**Audited:** 2026-10-11
**Baseline:** Abstract 6-pillar standards (no UI-SPEC.md; desktop PySide6/Qt application)
**Screenshots:** Not captured (desktop application; code-only audit)
**Interaction captures:** off

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Clear, task-specific labels and messages; ambiguity in "Show differences only" toggle wording |
| 2. Visuals | 3/4 | Functional hierarchy via collapsible sections and match indicators; toolbar split feels cramped in implementation |
| 3. Color | 3/4 | Fixed indicator colors for theme independence; but three colors for two states (match/differs/unknown) lacks clear semantic layer |
| 4. Typography | 4/4 | Consistent Qt Roboto styling; uppercase headers via proxy model; no hierarchy issues found |
| 5. Spacing | 3/4 | Toolbar split to two rows to fit 240px min width; trade-off between label readability and panel narrowness |
| 6. Experience Design | 3/4 | Profile operations never change selection; damaged-file safety good; but pre-comparison "Run a comparison…" message conflicts with default seeding logic pathway |

**Overall: 19/24**

---

## Top 3 Priority Fixes

1. **Profile load before comparison shows misleading message** (D-06 continuity) — When a profile is loaded before any comparison runs, the status bar says "Run a comparison to check them against your files" (PROFILE_LOADED_NO_RESULT_TEMPLATE). This pre-empts the natural D-04 default seeding flow and leaves users uncertain whether the checked attributes are correct. **Fix:** Either suppress the status bar message until after the first comparison, or clarify that the shown attributes are "from your saved profile, not yet verified."

2. **"Show differences only" checkbox language is ambiguous** (Pillar 1: Copywriting) — The label "Show differences only" does not clearly indicate that it hides rows where all attributes match; users may expect it to show ONLY the differing attributes per row, not hide entire matching rows. **Fix:** Revise to "Hide rows where all checked attributes match" or "Show only rows with differences" to clarify scope.

3. **Match indicator "unknown" state visually indistinguishable from disabled/inactive** (Pillar 3: Color + 2: Visuals) — The gray (#9e9e9e) indicator dot for "not yet compared" lacks semantic weight; users may interpret it as "comparison not run" instead of "comparison not run yet on this file." The three-color system (match=green, differs=red, unknown=gray) spreads semantic information across colors instead of pairing state transitions clearly. **Fix:** Either add a fourth indicator (e.g., outline-only dot for unknown), or pair the gray dot with a status label in the Compare list header row (e.g., "Status" column).

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**Audit method:** Grep for string literals and dialog/button text; check against task-specific clarity.

**Findings with file:line references:**

- **GOOD — Button labels use ellipsis correctly:** "Save…", "Rename…", "Delete…" (main_window.py:84, 101, 102) signal that a dialog will open. This follows platform conventions.

- **GOOD — Match indicator tooltips are precise and actionable:**
  - "Not yet compared. Run a comparison to check." (main_window.py:141)
  - "Matches the target in every checked attribute." (main_window.py:142)
  - "Differs from the target in at least one checked attribute." (main_window.py:143)
  Each tooltip describes the state, the current file's role, and the next action (if needed).

- **GOOD — Confirmation dialogs use plain text and default to safe action:**
  - "A profile named '{name}' already exists. Replace it with the attributes checked now?" (main_window.py:90–91) — Question is clear, safe default is No.
  - "Delete the profile '{name}'? This can't be undone." (main_window.py:106) — Same pattern.

- **GOOD — Profile state messages distinguish between pre- and post-comparison:**
  - Pre-comparison: "Loaded profile '{name}' ({count} spec items). Run a comparison to check them against your files." (main_window.py:125–128)
  - Post-comparison: "{missing} of {total} spec items in '{name}' weren't found in these files: {names}." (main_window.py:116–118)
  The distinction prevents false confidence ("nothing to worry about") when attributes are missing because no comparison has run yet.

- **WARNING — "Show differences only" label is ambiguous (Pillar 1 blocker, lines 70, 403):** The label does not clarify whether it hides matching rows or hides matching attributes *within* rows. A user unfamiliar with the design may expect it to collapse or dim differing cells, not remove entire rows. The docstring in Phase 2 D-06 explains "never a replacement for [cell highlighting]," but the label alone does not convey "hide rows." Proposed fix: "Hide matching rows" or "Show only rows with differences."

- **NEUTRAL — File rejection messages are specific but context-dependent:**
  - "Removed '{removed_basename}' from the comparison list: it is now the target file." (main_window.py:493–495) — Clear.
  - "Skipped '{os.path.basename(self.target_file)}': it is already selected as the target file." (main_window.py:531–533) — Clear.
  These are only shown when the user tries an invalid action, so the specificity is appropriate.

- **NEUTRAL — Profile save/rename/delete status messages are brief:**
  - "Saved profile '{name}' ({count} attributes)." (main_window.py:89)
  - "Renamed profile '{old}' to '{new}'." (main_window.py:105)
  - "Deleted profile '{name}'." (main_window.py:107)
  These confirm the action but do not explain next steps. Users may not realize a renamed profile is immediately selected in the dropdown. Not critical, as the UI state is self-evident, but slightly less helpful than "Saved and selected for future comparisons."

**Score justification:** Copywriting is clear and task-specific in most cases, using active voice and specific nouns (file names, attribute counts). The "Show differences only" label is ambiguous enough to cause confusion, dropping the score from 4 to 3. The pre-comparison profile message is slightly misleading in implying the user should run a comparison immediately (blocking other workflows like "run with different files first, then load a profile").

---

### Pillar 2: Visuals (3/4)

**Audit method:** Check component hierarchy, focal points, and visual differentiation.

**Findings:**

- **GOOD — Clear focal point on main window:** The "Run Comparison" button (main_window.py:304–306) is right-aligned and styled as a QPushButton (prominent vs. menu buttons). The results table below it is the primary content area. The Attributes side panel is clearly secondary (always left, narrow, non-collapsible).

- **GOOD — Attribute picker hierarchy via collapsible sections:** Categories are top-level (category, attribute) pairs grouped in collapsible QTreeWidgetItems (attribute_picker.py:113–136). Checked categories auto-expand; unchecked collapse. This creates visual scanability.

- **GOOD — Match indicator dots provide at-a-glance file status:** Each "Compare with" item shows a colored circle (12 px diameter, main_window.py:146) that signals match/differs/unknown without requiring a hover or selection. This is a genuine visualization win over a single "status" column.

- **NEUTRAL — Profile toolbar layout is split but visually cramped:** The two-row profile toolbar (profile_combo_row above profile_actions_row, main_window.py:352, 364) was introduced to fit within the 240–260 px panel minimum width (03-04-PLAN.md Design notes). This is a pragmatic layout fix, but the result is:
  - Two rows of controls (dropdown alone, then two buttons) instead of one cohesive toolbar
  - No visual separator between the rows; they appear as stacked widgets with no grouping cue
  - The "Manage" button's icon-like appearance (QToolButton with PopupMode.InstantPopup) is less discoverable than a text button
  **Impact:** Users may not immediately recognize the Manage menu as separate from Save. The layout trades compactness for clarity.

- **NEUTRAL — Attribute picker search box does not indicate live filtering:** The search_edit (attribute_picker.py:50–53) has a clear button but no visual cue that it filters the tree in real time (hiding non-matching leaf items, preserving section structure). A placeholder "Search attributes…" is clear, but the filtering is a pure behavioral discovery. Not a blocker, as the search is responsive and obvious on use.

- **NEUTRAL — Icon-only buttons lack redundant text labels:** The "Manage" QToolButton (main_window.py:370–380) uses setText("Manage") but as a PopupMode.InstantPopup button, it may render as an icon-heavy control in some qt-material themes. The tooltip ("Rename or delete the profile shown in the list") is present but not always visible on first glance.

**Score justification:** Visual hierarchy is clear and functional. Match indicators are a genuine visualization win. The toolbar layout is cramped due to panel width constraints, and the Manage button's presentation is less prominent than the Save button. No severe visual confusion, but the layout trade-off and button presentation cost 1 point from an otherwise solid 4.

---

### Pillar 3: Color (3/4)

**Audit method:** Grep Tailwind/Qt classes and color definitions; count color semantics.

**Findings with color analysis:**

- **GOOD — Fixed indicator colors chosen for theme independence:** Green #2ecc71, Red #e74c3c, Gray #9e9e9e (main_window.py:155–159) are fixed QColor literals, not derived from qt-material's theme. This is deliberate (03-04-PLAN.md Design notes): a dot must read identically in light and dark modes. The choices are accessible and distinct.

- **GOOD — Two semantic states map to two colors (match/differs):** Green and red are classic "pass/fail" signals. This is immediately understood. The third color (gray for unknown) is added for completeness, not semantic load.

- **WARNING — Three-color system spreads state across colors without a fourth dimension:** The unknown state uses gray, which is often interpreted as "disabled" or "inactive" rather than "pending." With only three colors, the system cannot layer other information (e.g., "running," "stale," "error"). A future enhancement might add icon overlays or a fourth color tier.
  **Mitigation in code:** The code explicitly checks for result=None and count mismatch and resets all dots to gray (main_window.py:704–717), preventing stale indicators. This is correct, but the visual cue alone doesn't explain "why gray." A tooltip hover reveals it ("Not yet compared…"), but the initial impression is ambiguous.

- **NEUTRAL — Diff highlight color is theme-dependent:** The table's diff-highlight tint (main_window.py:611) is derived from qt-material (diff_highlight_color). This is separate from the match indicators and serves a different purpose (per-cell differences within a row), so the two-color system (match/differs) + theme-derived cell highlighting is coherent overall.

- **NEUTRAL — Profile dropdown and buttons use standard Qt colors:** No custom colors for the profile toolbar widgets (main_window.py:353–380). They defer to qt-material. This is correct (reduces cognitive load; no new color vocabulary introduced for profile management).

**Color usage audit (no Tailwind; PySide6 uses qss/qt colors):**
- 3 fixed indicator colors (match, differs, unknown)
- 1 derived theme color (diff highlight)
- 0 hardcoded accent colors in the profile UI (good — no over-use)
- Standard Qt colors for buttons, text, backgrounds (inherited from theme)

**Score justification:** The indicator color palette is well-chosen for accessibility and theme independence. The three-color system is semantically clear for the two-state comparison (match/differs). The gray unknown state lacks a supplementary visual cue (e.g., outline, pulse, or label), reducing clarity slightly. 3/4 is appropriate for a solid, theme-aware color scheme with minor semantic ambiguity in the unknown state.

---

### Pillar 4: Typography (4/4)

**Audit method:** Grep font size and weight classes; check hierarchy and consistency.

**Findings:**

- **GOOD — Consistent font family and sizes throughout:** PySide6/Qt uses platform fonts (Roboto 13 px in qt-material, referenced in main_window.py line 172 comment). No custom font sizes or weights are overridden in the GUI code for Phase 03 (profile toolbar, match indicators, attribute picker).

- **GOOD — Font hierarchy via Qt's default button/label/header styling:**
  - QMessageBox title: default bold
  - Button labels (Save…, Manage, etc.): default normal weight
  - Tooltip text: default small
  - Attribute names in tree: default normal
  - Table headers: uppercase via UppercaseHeaderProxyModel (main_window.py:317), not bold, not resized
  
- **GOOD — Uppercase header transformation is applied consistently:** The UppercaseHeaderProxyModel (table_model.py, imported main_window.py:55) transforms all column headers to uppercase, a single point of control. No mixed-case or inline-style headers introduce hierarchy.

- **GOOD — Search placeholder and profile placeholder text are readable:** "Search attributes…" (attribute_picker.py:30) and "Load a profile…" (main_window.py:81) are clear hints, sized to standard QLineEdit/QComboBox heights.

- **NEUTRAL — No custom font weights (thin, light, bold, etc.) in profile UI:** This is correct — no need to introduce weight variation for profile controls. They are secondary actions, not high-emphasis UI.

**Font audit (no font-size classes; PySide6 inherits platform defaults):**
- 1 consistent font family (Roboto via qt-material)
- 1 default size (13 px, appropriate for desktop)
- 0 overrides in Phase 03 code
- 1 transformation (uppercase headers, via proxy)

**Score justification:** Typography is clean, consistent, and follows platform conventions without introducing new cognitive load. There are no illegible, disproportionate, or confused font choices. The single transformation (uppercase headers) is applied uniformly. This is a solid 4/4 — no issues found.

---

### Pillar 5: Spacing (3/4)

**Audit method:** Grep spacing classes and layout definitions; check for arbitrary values and consistency.

**Findings with spacing analysis:**

- **GOOD — Standard Qt layouts used throughout:** QVBoxLayout, QHBoxLayout, QGridLayout with default spacing (main_window.py and attribute_picker.py). No arbitrary pixel margins or padding in Phase 03 code.

- **GOOD — Attributes panel enforces minimum width without hard height:** ATTRIBUTES_PANEL_MIN_WIDTH_PX = 240 (main_window.py:195) is a single constant, raised from 220 to 240 to accommodate the stacked profile toolbar (03-04-PLAN.md). No arbitrary per-widget spacing constants introduced.

- **GOOD — Profile toolbar layout uses stretch factors:** profile_combo_row and profile_actions_row both use addWidget(..., stretch=1) (main_window.py:361, 368, 380), ensuring buttons/combo fill available width evenly.

- **WARNING — Toolbar split into two rows creates visual spacing/grouping gap:** The profile_row is a QVBoxLayout containing profile_combo_row (dropdown alone) above profile_actions_row (buttons). No explicit spacing or visual separator is added between the two rows (main_window.py:350–381). The gap is implicit Qt default inter-layout spacing (typically 6–9 px). This is readable but lacks explicit grouping (no border, no label, no divider), so users may not perceive the two rows as a single "profile toolbar" unit.
  **Impact:** At 240–260 px widths, the vertical stack is necessary, but the visual cohesion is diminished. Adding a simple QHLine or a QGroupBox("Profiles") border could help, but that would increase vertical footprint.

- **NEUTRAL — Attributes panel contents margins are zeroed:** layout.setContentsMargins(0, 0, 0, 0) in attribute_picker.py:48. This is correct — the panel is a side-panel content area, not a top-level dialog.

- **NEUTRAL — Result table uses standard QTableView spacing:** alternatingRowColors=True (main_window.py:321), verticalHeader hidden (line 323), default row heights. No custom spacing.

- **NEUTRAL — Match indicator diameter is explicit:** _MATCH_INDICATOR_DIAMETER_PX = 12 (main_window.py:146) is intentional, chosen to be visible but not oversized in a list. No arbitrary tweaking.

**Spacing audit:**
- 1 constant min-width (240 px)
- 1 constant indicator diameter (12 px)
- 1 explicit toolbar split (two rows, no visual separator)
- 0 arbitrary padding or margins in Phase 03 code (relies on Qt defaults)
- Standard Qt inter-widget spacing (inherited, not overridden)

**Score justification:** Spacing is consistent and intentional, using Qt's default inter-widget spacing and explicit stretch factors. The toolbar split introduces a minor visual grouping gap (two rows without an explicit separator), but this is a pragmatic trade-off for fitting a narrow panel. The overall layout is readable. 3/4 accounts for the lack of visual separation between the two profile toolbar rows; a 4/4 would require explicit grouping (border/label/divider).

---

### Pillar 6: Experience Design (3/4)

**Audit method:** Check for state coverage (loading, error, empty, disabled, confirmation) and interaction patterns.

**Findings with state analysis:**

- **GOOD — Profile operations never change the checked attributes or run state:**
  - _save_profile() (main_window.py:1061–1093) reads checked_attributes but does not mutate them.
  - _load_selected_profile() (main_window.py:1095–1141) calls attribute_picker.set_checked(), which fires selection_changed once and lets the existing _apply_attribute_selection chain do the rest (no manual table refit or status bar overwrite).
  - _rename_selected_profile() (main_window.py:971–1009) and _delete_selected_profile() (main_window.py:1011–1043) never touch the picker or comparison.
  This isolation is correct per D-05, ensuring profile operations are orthogonal to comparison state.

- **GOOD — Damaged profiles.json is handled safely:**
  - _refresh_profile_combo() catches ProfileStorageError and disables the dropdown with "Saved profiles unavailable" (main_window.py:928–934).
  - The status bar displays the error message from the exception.
  - The file is never overwritten or re-read until the next operation.
  - A save attempt (through _save_profile error handling, line 1086) surfaces the same error.
  This "fail-open, inform, refuse to write" pattern is correct.

- **GOOD — Empty profiles are handled:**
  - An empty frozenset is a valid profile (attribute_picker.py sets no defaults; core/profile_repository.py never rejects an empty attributes set).
  - Loading an empty profile unchecks everything; the status bar shows NO_ATTRIBUTES_SELECTED_MESSAGE (correct, not a not-found report).
  - Saving an empty profile is allowed (no validation gate).
  This is permissive but correct — users may save an "empty" profile as a placeholder or a reset.

- **GOOD — Confirmation dialogs default to No/safe action:**
  - Overwrite confirmation: "Replace it?" with No default (main_window.py:1080–1082).
  - Delete confirmation: "Delete the profile…? This can't be undone." with No default (main_window.py:1028–1029).
  - _confirm() method enforces No as both the default and escape button (main_window.py:1184–1185).
  This prevents accidental data loss.

- **GOOD — Match indicators reset on file/selection changes:**
  - add_compare_files(), remove_selected_files(), set_target_file() all call _reset_match_indicators() (main_window.py:535, 545, 497).
  - _apply_attribute_selection() and _apply_differences_only() call _update_match_indicators() or _reset_match_indicators() respectively.
  - The indicators never show stale state across operations.

- **WARNING — Pre-comparison profile load message may confuse attribute defaults (D-06 continuity issue):**
  - PROFILE_LOADED_NO_RESULT_TEMPLATE reads: "Loaded profile '{name}' ({count} spec items). Run a comparison to check them against your files." (main_window.py:125–128).
  - This message is written directly by _load_selected_profile when table_model.result() is None (main_window.py:1128–1141).
  - **The issue:** When a profile is loaded and then a comparison is run, Phase 2's D-04 first-use default seeding is disabled (attribute_picker._defaults_enabled = False, set by set_checked() at line 170). This is correct per D-01.
  - **The confusion:** The pre-comparison message implies "check your checked attributes," but those attributes are only the profile's saved subset. If the user runs a comparison and finds that the Beam category is unchecked (because it wasn't in the saved profile), they may be surprised. The message doesn't clarify that the checked set is *exactly* the profile's saved attributes, not a starting point for defaults.
  - **Severity:** Medium. The checked state is visually obvious in the picker (all items are in the correct state), but the message's phrasing ("check them against your files") suggests an action, not a final state. Users who expect "Load profile → see defaults → run comparison" may be confused.
  - **Mitigation:** The message is only shown once, before the first comparison. After the comparison runs, _show_result_status takes over and explains "2 of 5 spec items not found" (if applicable), which is clearer. But the pre-comparison message is still sub-optimal.

- **NEUTRAL — No loading states visible (comparison runs on QThread):**
  - The main window disables the Run button and updates the status bar (main_window.py:560–561) while a comparison is running.
  - No progress bar or spinner is shown; the UI remains responsive.
  - This is correct per D-14 (no blocking), but there is no visual "running" indicator on the profile toolbar. If a user loads a profile during a comparison, the status bar message remains "Comparing..." (not overwritten). This is acceptable.

- **NEUTRAL — No visual feedback for profile save (only status bar):**
  - _save_profile() updates the status bar with "Saved profile '{name}' ({count} attributes)." (main_window.py:1092).
  - No toast, no highlight, no selection change in the dropdown (the combo already shows the profile selected via _refresh_profile_combo).
  - Users are informed but not visually celebrated. This is in line with the quiet, professional design.

- **NEUTRAL — Attribute picker's set_checked() timing (RESEARCH Pitfall 2 mitigation):**
  - After set_checked() is called (by _load_selected_profile, main_window.py:1127), the method starts the 0 ms coalescing timer (attribute_picker.py:189).
  - This ensures selection_changed is emitted once, on the next event loop turn.
  - The existing _apply_attribute_selection -> _show_result_status chain then runs, and _show_result_status computes the D-06 not-found report from the current result (if any).
  - This is correct and well-designed, but it's a behavioral detail not visible in the UI.

**State coverage audit:**
- Loading states: Yes (Run button disabled, status bar shows "Comparing…")
- Error states: Yes (ProfileStorageError surfaces via _show_error, damaged file prevents load)
- Empty states: Yes (empty profile handled, no errors raised)
- Disabled states: Yes (Manage button/actions disabled until a profile is shown in dropdown)
- Confirmation states: Yes (delete and overwrite ask first, No default)
- Stale state prevention: Yes (match indicators reset on file changes; D-06 report recomputed on selection change)

**Score justification:** Experience design is solid and defensive. Profile operations are correctly isolated. Error handling is safe and informative. The pre-comparison profile load message is slightly misleading about the scope of "check them," dropping the score from 4 to 3. All state transitions are covered, and no flows are broken, but the message wording could be tighter.

---

## Files Audited

```
src/gdtf_comparer/gui/main_window.py (lines 1–1188)
  - Profile toolbar layout (profile_row, profile_combo_row, profile_actions_row)
  - Profile management methods (_save_profile, _load_selected_profile, _refresh_profile_combo)
  - Match indicator logic (_match_indicator_icon, _set_compare_item_match_state, _update_match_indicators)
  - Status bar messaging (_show_result_status, _profile_items_not_found_message)
  - Error/confirmation dialogs (_show_error, _confirm)
  - Module constants (PROFILE_*_LABEL, PROFILE_*_TEMPLATE, MATCH_STATE_*_TEMPLATE, etc.)

src/gdtf_comparer/gui/attribute_picker.py (lines 1–200+)
  - Attribute picker hierarchy and styling (QTreeWidget, QLineEdit search)
  - set_checked() method for D-03 profile loading
  - set_catalog() method with D-04 first-use defaults control

src/gdtf_comparer/core/profile_repository.py
  - Profile data structure and storage (not directly UI, but defines what the UI renders)
  - ProfileError, ProfileNameError, ProfileStorageError exception types (user_message property)
```

---

## Summary

Phase 03 implements a robust, well-isolated profile management system with strong safety practices (confirmation dialogs, atomic writes, damaged-file handling) and good accessibility (fixed-color match indicators, clear tooltips). The 6-pillar audit reveals:

- **Strengths:** Clear copywriting for dialogs; consistent typography; safe error handling; state isolation (profile operations don't touch comparison).
- **Weaknesses:** "Show differences only" label is ambiguous; toolbar split lacks visual grouping; pre-comparison profile message doesn't clarify attribute scope; gray "unknown" match indicator is semantically weak.

**Top 3 fixes focus on clarity and visual cohesion:** (1) Revise the "Show differences only" label to specify "Hide rows"; (2) clarify the pre-comparison profile message or defer it; (3) add visual distinction or a label to the "unknown" match state.

The overall implementation is solid for a desktop application, with no blocking issues but meaningful UX improvements available in the three priority areas.

---

*Phase: 03-compare-profiles-export*
*Overall score: 19/24*
*Recommendation: Deploy; address priority fixes in a future polish phase*
