# Phase 5 — UI Review

**Audited:** 2026-10-24
**Baseline:** Abstract 6-pillar standards (no UI-SPEC.md exists for this phase)
**Screenshots:** Not captured (no dev server — PySide6 desktop application, code-only audit)
**Interaction captures:** off

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | All CTAs action-oriented; no generic labels; error messages are friendly and domain-specific |
| 2. Visuals | 4/4 | Clear two-tab structure; left/right pane layout; table hierarchy with color + text (not color-only); legend above results |
| 3. Color | 3/4 | Fixed traffic-light RGB values chosen for both themes; no evidence in code of actual visual testing on both light/dark rendered screens |
| 4. Typography | 3/4 | Relies on defaults (appropriate for desktop); tab/window titles clear; no explicit hierarchy through font; column header "Result" could be more specific |
| 5. Spacing | 4/4 | Standard PySide6 layouts; no arbitrary pixel spacing; user-resizable splitter panes; consistent margins |
| 6. Experience Design | 4/4 | Loading/error/empty states all handled; state preserved across fixture switches; atomic file operations; thread-safe concurrency; non-blocking UI |

**Overall: 22/24**

---

## Top 3 Priority Fixes

1. **Column header "Result" lacks clarity** — Users scanning the table may not immediately understand that the Result column summarizes green/yellow/red counts rather than being a single pass/fail. — Change header from "Result" to "Summary" or "Score" to better signal it's an aggregate, or expand it to "Score (Green/Yellow/Red)" as a tooltip.

2. **No visible evidence that traffic-light colors were tested on rendered screens** — Phase 5 Plan 05 Task 3 coverage (D7) mentions `test_traffic_lights_paint_in_both_themes` pixel-sampling the colors in both light and dark qt-material themes, but the test file itself is not present in the audited codebase snapshot. — Run the traffic-light rendering test on both light and dark themes before shipping to confirm the fixed RGB values are distinguishable on actual rendered UI (test exists per SUMMARY.md but verify it's in the codebase and passes).

3. **Fixture type list tooltip shows only gdtf_spec, not readable name** — When hovering over a fixture in the left panel of "Set Requirements", the tooltip is `entry.gdtf_spec` (line 283 of substitution_window.py), which may be a cp437-mangled archive member name for accented files. — Display the `entry.fixture.name` in the tooltip as well (e.g., "Lumière@Spot.gdtf — Chauvet Lumierspect"), or use the readable_gdtf_spec from core.mvr_repository so users see the file name they recognize.

---

## Detailed Findings

### Pillar 1: Copywriting (4/4)

**Strengths:**
- All button labels are action-oriented and specific: "Import MVR…", "Save Requirements…", "Check Inventory With These…" (never generic "OK", "Save", "Next")
- Empty state messages are descriptive and task-focused:
  - "No show file imported yet." (lines 60 substitution_window.py)
  - "Nothing marked yet — tick the attributes that matter for this fixture." (line 56, requirements_editor.py)
- Error messages are friendly and actionable:
  - "Open a requirements file first, or send one over from the Set Requirements tab." (line 64, substitution_window.py)
  - "Couldn't read this file" for failure rows (line 21, candidate_results.py)
- Match state colors explained in plain words (line 44-47, candidate_results.py): "Green: meets or is better... Yellow: close, so it might work... Red: way outside the set range"
- STATE_DESCRIPTIONS (core.substitution.py) provide full explanations on requirement cell tooltips: "Meets or beats the requirement", "Close — might work", "Way outside the range — won't work"
- Tab titles are numbered and clear: "1. Set Requirements", "2. Check Inventory"
- Window title is descriptive: "Find Substitutes — GDTF Comparer"
- Plain text format enforced on summary labels to avoid HTML interpretation (setTextFormat(Qt.TextFormat.PlainText) on lines 119 and 180, substitution_window.py — prevents injection via file-supplied fixture names, following T-01-17)

**No issues found.**

### Pillar 2: Visuals (4/4)

**Strengths:**
- Clear visual hierarchy through two-tab structure with numbered, task-focused titles
  - Tab 1: "1. Set Requirements" — left panel (fixture list) + right panel (requirements editor) with Save/Use buttons below
  - Tab 2: "2. Check Inventory" — horizontal flow: Open Requirements → Choose Folder → Check Inventory → results table
- Left/right splitter pane layout in Set Requirements tab provides intuitive left-list / right-detail pattern (line 123, substitution_window.py)
- Results table has clear column order: Rank (#), Fixture, File, Result (aggregate score), then requirement columns — facilitates left-to-right scanning
- Failure rows (lines 113-155, candidate_results.py) are visually distinct:
  - Gray foreground text (QColor(128,128,128)) for unreadable files
  - "—" in rank column and "Couldn't read this file" in fixture column clearly mark them as non-ranked
  - Failure rows appear below ranked candidates, never mixed in (line 85-90, rowCount method)
- Color + text approach for match indicators:
  - Legend label above results table (line 178, substitution_window.py) explicitly states colors in words: "Green: meets or is better... Yellow: close, so it might work... Red: way outside the set range"
  - Requirement cell tooltips (line 175-197, candidate_results.py) include full explanation: "Candidate: {value} · Your fixture: {target} · {direction} → {color meaning}"
  - Color is never the only signal — every cell has display text or tooltip (D-10 on screen)
- Button states clearly indicate operation status:
  - Import MVR… button disabled during import, status bar shows "Importing '{filename}'…" (line 244, 286)
  - Check Inventory button disabled during scan, status bar shows "Checking '{folder}'…" (line 380, 381)
  - Save/Use buttons disabled until a fixture is selected (lines 136-137, 140-141)
- Search box in requirements editor has visual feedback (setPlaceholderText, line 81, requirements_editor.py) and hides rows on a visibility-only basis (never changes check state)
- Window dimensions (1280x760) provide reasonable working space for both tabs without excessive scrolling

**No issues found.**

### Pillar 3: Color (3/4)

**Strengths:**
- Traffic-light colors use fixed RGB values (not qt-material theme-derived) for consistent visibility in both light and dark modes:
  - GREEN: QColor(46, 204, 113, 140) — sRGB (#2ecc71 equivalent) with alpha 140
  - YELLOW: QColor(241, 196, 15, 160) — sRGB (#f1c40f equivalent) with alpha 160
  - RED: QColor(231, 76, 60, 140) — sRGB (#e74c3c equivalent) with alpha 140
  - (Lines 27-31, candidate_results.py)
- Comment at line 24-26 explicitly documents intent: "Fixed, theme-independent colors (Phase 5, Claude's discretion, matching gui.main_window's own fixed match-indicator color posture): a traffic light needs to read the same way regardless of light/dark mode."
- Gray foreground for failure rows (QColor(128, 128, 128)) is neutral and theme-independent (line 22)
- Alpha values (140-160) indicate consideration for transparency and overlap visibility

**Weakness — WARNING:**
- **No visual evidence in this phase's code that traffic-light colors were actually rendered and tested on both light and dark theme screens.** Phase 5 Plan 05 Task 3 coverage item D7 references `test_traffic_lights_paint_in_both_themes` (SUMMARY.md line 142-144), which allegedly pixel-samples the colors through `view.viewport().grab()`, but:
  - That test file (tests/gui/test_candidate_results.py) is not present in the audited code snapshot
  - No screenshot or visual artifact is included in the phase directory
  - The comment about "qt-material-suppresses-BackgroundRole gap Phase 2's delegate finding first identified" (line 41-43 candidate_results.py) suggests there was a rendering issue in Phase 2, but no evidence that it was verified fixed in Phase 5
- **Recommendation:** Before shipping Phase 5, run the traffic-light test suite on both light and dark qt-material themes and visually confirm the fixed RGB values are distinguishable on actual rendered UI. If the test doesn't exist or is failing, create/fix it.

### Pillar 4: Typography (3/4)

**Strengths:**
- Tab titles are numbered and action-oriented: "1. Set Requirements", "2. Check Inventory" — establishes sequence and role
- Window title is clear and descriptive: "Find Substitutes — GDTF Comparer"
- All text labels use setWordWrap(True) for multi-line readability where needed (lines 115, 159, 168, 179, substitution_window.py)
- Placeholder text provides guidance: "Search attributes…" (line 55, requirements_editor.py)
- Tree columns have descriptive headers: "Attribute", "Your fixture", "Direction", "Tolerance" (line 93, requirements_editor.py)
- Table headers are concise: "#", "Fixture", "File", "Result", then requirement attribute names (lines 208-223, candidate_results.py)
- Direction labels are full words, not abbreviations: "Higher is better", "Lower is better", "Closest to target", "Must match" (core.substitution.py DIRECTION_LABELS)

**Weakness — WARNING:**
- **Column header "Result" is ambiguous.** A user scanning the results table may not immediately understand that "Result" is an aggregate score showing green/yellow/red counts (line 168 of candidate_results.py). The current display is "{green_count} green · {yellow_count} yellow · {red_count} red" which is clear once read, but the column header name doesn't signal this is a summary. **Recommendation:** Change header to "Summary" or "Score (Green/Yellow/Red)" to better indicate it's an aggregate, or add a tooltip to the header explaining what the column shows.

**Other observations:**
- Typography hierarchy is established through widget structure (tabs, panels, buttons) rather than explicit font-size/font-weight changes
- Relies on PySide6's default typography, which is appropriate for a desktop application
- No evidence of custom font selection, which is fine — system fonts work well in PySide6

### Pillar 5: Spacing (4/4)

**Strengths:**
- Uses standard PySide6 layout managers (QVBoxLayout, QHBoxLayout, QGridLayout) throughout — no hardcoded pixel positions
- Consistent margin management:
  - setContentsMargins(0, 0, 0, 0) on RequirementsEditor (line 74, requirements_editor.py) and right_pane (line 130, substitution_window.py) removes unnecessary padding for tightly integrated panels
  - Other layouts use PySide6 defaults for consistent breathing room
- Splitter widget allows user-resizable panes (line 123, substitution_window.py) — users can adjust left-fixture-list vs. right-editor width to suit their workflow
- Window dimensions (1280x760, line 81) are hardcoded but reasonable for a desktop app with a two-tab interface
- No arbitrary spacing values or magic numbers in Phase 05 GUI code
- Row-based layout (QHBoxLayout) for action buttons (line 134, 154, 163, substitution_window.py) provides consistent alignment

**No issues found.**

### Pillar 6: Experience Design (4/4)

**Strengths:**

**Loading states:**
- All long-running operations (MVR import, folder scan) run on background QThread workers (lines 246-261, 383-398, substitution_window.py)
- GUI thread never blocks; button state shows operation in progress:
  - "Importing '{filename}'…" in summary label (line 243)
  - "Checking '{folder}'…" in status bar (line 381)
  - Buttons disabled (import_mvr_button, check_inventory_button) during operation
- is_busy() method (line 227-230) allows main window to detect if substitution window is running a worker, preventing main window close during operation

**Error states:**
- _show_error() method (line 215-225) displays friendly, plain-text modal dialogs — no raw tracebacks, no HTML injection risk
- Error messages are actionable:
  - "Open a requirements file first, or send one over from the Set Requirements tab." (line 373)
  - "Choose the folder that holds your inventory's GDTF files first." (line 376)
  - Exceptions caught as SubstitutionError and displayed as plain strings (lines 326, 352)
- Failed import clears the fixture list and shows placeholder (lines 296-300)
- Failed scan clears results and shows error (lines 412-415)

**Empty states:**
- NO_MVR_PLACEHOLDER, NO_REQUIREMENTS_PLACEHOLDER, NO_FOLDER_PLACEHOLDER provide clear guidance at each step
- "Nothing marked yet — tick the attributes that matter for this fixture." (line 56, requirements_editor.py) shows when a fixture is loaded but no requirements are checked
- Empty fixture list after import shows "Set Requirements" tab with no selection, editor is cleared

**State preservation:**
- RequirementsEditor._remembered (line 103, requirements_editor.py) captures each fixture type's checked state, direction, and tolerance when switching between fixtures
- Switching away from a fixture and back restores exactly what was ticked (D-04)
- clear() empties memory on new MVR import, ensuring fresh start
- Search box text persists across fixture switches, applied fresh at end of show_fixture (line 190)

**Button states and confirmations:**
- Save/Use buttons disabled until a fixture is selected (lines 306-307, 312-313)
- File operations use native QFileDialog prompts (QFileDialog.getOpenFileName, getExistingDirectory, getSaveFileName) — standard OS file selection, no data loss without confirmation
- Import button re-enabled only after worker thread finishes (line 267)
- Check Inventory button re-enabled only after scan finishes (line 404)

**Atomic operations:**
- save_requirements uses proven atomic temp-file-then-replace pattern (core.requirements_repository.py, Phase 5 Plan 04 verified under failure injection)
- Never leaves a half-written file if save fails

**Concurrency guarantees:**
- Only one MVR import at a time: import_mvr() returns early if _import_thread is already running (line 235-236)
- Only one inventory scan at a time: check_inventory() returns early if _scan_thread is already running (line 370-371)
- Results appear complete in one step or not at all (set_scan(None) clears, then set_scan(result) populates atomically)
- New import replaces previous fixture list wholesale (clear() followed by population)

**Accessible output:**
- Legend text above results table explains colors in plain words (not color-only) — matches user's own words from 05-CONTEXT.md
- Requirement cell tooltips on every cell (line 175-197, candidate_results.py) explain: "Candidate: {value} · Your fixture: {target} · {direction} → {color meaning}"
- Status bar messages show operation progress ("Importing...", "Checking...", "Ready")
- Failure rows are labeled and explained (gray text, "Couldn't read this file", reason text in Summary column)

**Clean shutdown:**
- closeEvent waits bounded time (SUBSTITUTION_CLOSE_WAIT_TIMEOUT_MS = 3000 ms) for worker threads to finish (lines 417-428, substitution_window.py)
- Main window's closeEvent closes substitution window first before closing itself (D-05 pattern from Phase 02 proof)
- app.py's post-event-loop os._exit guard (Phase 5 Plan 02) handles stuck workers if they don't finish in time

**No issues found.**

---

## Files Audited

- `src/gdtf_comparer/gui/substitution_window.py` — Main Find Substitutes window: two tabs, import/editor UI, requirements/inventory workflow
- `src/gdtf_comparer/gui/requirements_editor.py` — Per-fixture checklist editor with direction/tolerance controls, per-type memory, search
- `src/gdtf_comparer/gui/candidate_results.py` — Table model for ranked results, failure rows, color painting, tooltips
- `src/gdtf_comparer/gui/main_window.py` (lines 1-299) — Integration point: Find Substitutes button and SubstitutionWindow instance
- `src/gdtf_comparer/core/substitution.py` (lines 1-150) — Direction/MatchState enums, color definitions, scoring logic
- `src/gdtf_comparer/core/requirements_repository.py` — Hardened sidecar file format, atomic saves (verified in Phase 5 Plan 04)
- Phase 5 SUMMARY files (05-01 through 05-05) for context on implementation decisions and test coverage

---

*Phase: 05-mvr-import-fixture-substitution*
*Audited: 2026-10-24*
