# Phase 02 — UI Review

**Audited:** 2026-10-11  
**Baseline:** Abstract 6-pillar standards (no UI-SPEC.md)  
**Screenshots:** Not captured (PySide6 desktop application — code-only audit)  
**Interaction captures:** off (desktop application, not web-based)  

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | Clear, action-oriented labels; some messages are verbose (80+ chars). |
| 2. Visuals | 3/4 | Strong layout hierarchy; Attributes panel always visible; lacks visual progress feedback during comparison. |
| 3. Color | 3/4 | Diff highlighting follows theme properly; match indicators use hard-coded colors, breaking theme consistency. |
| 4. Typography | 3/4 | Typography delegated to qt-material theme; good hierarchy; could benefit from consistent heading styles. |
| 5. Spacing | 3/4 | Hard-coded key measurements justified; panel width well-reasoned per G-03-1 fix; some layouts use platform defaults. |
| 6. Experience Design | 3/4 | Good state coverage (empty, loading, error, ready); lacks confirmation for destructive actions; no intermediate profile-load state. |

**Overall: 18/24**

---

## Top 3 Priority Fixes

1. **Match indicator colors break theme consistency** — User sees hardcoded green/red/gray dots instead of theme-derived colors. Impact: Visual inconsistency across light/dark themes. Fix: Derive match indicator colors from primary/warning/neutral theme colors while ensuring readability in both themes, or document the intentional exception as a design trade-off.

2. **Verbose empty-state message degrades scannability** — "No attributes selected. Check attributes in the Attributes panel to show them." is 80+ characters and competes for status bar space. Impact: Long message reduces scan speed and clarity. Fix: Shorten to "No attributes selected — check the panel at left" (48 chars).

3. **Missing visual progress feedback during comparison** — Run button disables but no spinner, progress bar, or animated indication shows work is underway. Impact: User cannot tell if the app froze or is processing. Fix: Add an indeterminate progress bar or animated spinner to the status bar during `is_comparison_running()`.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

#### Strengths
- **Clear action labels:** "Browse…", "Add Files…", "Remove Selected", "Run Comparison" are all specific and unambiguous.
- **Contextual status messages:** "No attributes selected. Check attributes in the Attributes panel to show them." (NO_ATTRIBUTES_SELECTED_MESSAGE) correctly guides users where to act.
- **Search hint is intuitive:** "Search attributes…" (SEARCH_PLACEHOLDER) clearly indicates the field's purpose.
- **Toggle label is explicit:** "Show differences only" (DIFFERENCES_ONLY_LABEL) leaves no ambiguity about what the checkbox does.

#### Issues
- **Message length exceeds optimal scan time:** NO_ATTRIBUTES_SELECTED_MESSAGE (80 chars) and NO_DIFFERENCES_MESSAGE (103 chars with formatting) are verbose for a status bar, which is typically scanned in <2 seconds. Users may miss the guidance.
- **Search placeholder could be more specific:** "Search attributes…" doesn't clarify that search only narrows picker visibility, not the comparison itself. Could be "Filter by name…" or "Search (picker only)…".
- **Profile messages are context-heavy:** PROFILE_LOADED_NO_RESULT_TEMPLATE and PROFILE_ITEMS_NOT_FOUND_TEMPLATE are technically accurate but assume user context (Phase 3 features). For Phase 02 audit, these are acceptable but noted.

**File references:**
- `src/gdtf_comparer/gui/main_window.py:64-77` (constants)
- `src/gdtf_comparer/gui/attribute_picker.py:30` (SEARCH_PLACEHOLDER)

---

### Pillar 2: Visuals (3/4)

#### Strengths
- **Clear component hierarchy:** Files group at top, Run button center-right, Attributes panel left-always-visible, results table right-main-area creates intuitive layout.
- **Non-collapsible Attributes panel enforces discoverability:** `content_splitter.setChildrenCollapsible(False)` (line 416, main_window.py) ensures the picker is never accidentally hidden — critical for D-02.
- **Splitter proportions are well-chosen:** 260px left (23%) / 1020px right (77%) split keeps the panel readable while maximizing table space. Minimum width of 240px per G-03-1 fix prevents squeezing profile controls.
- **Visual focal point is clear:** Results table dominates the window; Run button draws attention via button styling and layout position (top-right of run row).
- **Grid/layout structure is legible:** Three columns for file selection (Label / Input / Button) clearly map the interaction flow.

#### Issues
- **No progress feedback during comparison:** Run button disables (line 560, main_window.py) but statusBar only shows text "Comparing N file(s)…". No spinner, progress bar, or animated indication. Users cannot visually confirm the app is working during long comparisons.
- **Visual state transitions are subtle:** No visual distinction between "result ready with all rows" and "result ready but filtered to zero rows". Both show empty table; only the status bar message clarifies why.
- **Match indicator dots appear without introduction:** The compare-list match indicators (Phase 3, lines 198-220) use small colored dots without obvious legend on first view. Phase 02 doesn't add this, but the infrastructure is present and lacks a help tip.

**File references:**
- `src/gdtf_comparer/gui/main_window.py:260` (window resize)
- `src/gdtf_comparer/gui/main_window.py:412-420` (splitter setup)
- `src/gdtf_comparer/gui/main_window.py:547-578` (run_comparison, button disable)

---

### Pillar 3: Color (3/4)

#### Strengths
- **Diff highlight follows theme correctly:** `diff_highlight_color(theme_name)` in `src/gdtf_comparer/gui/theme.py:137-157` derives the tint from qt-material's `primaryColor` at 0.35 alpha. This ensures the highlight reads correctly in both light and dark themes.
- **Live theme switching re-tints without recompute:** `_on_color_scheme_changed` (main_window.py:430-446) calls `_apply_highlight_theme`, which updates the model's brush once per theme change, not per cell. Cache is present via `@functools.lru_cache` on `_theme_color_hex` (theme.py:113-134).
- **Only one accent color used for core feature:** Diff highlighting is the only place the primary color is applied as a user-facing tint in Phase 02. Consistent with Phase 1's D-07.
- **BackgroundBrushDelegate required to visible because qt-material suppresses BackgroundRole:** Design notes in table_model.py:368-377 document why the delegate is necessary. This shows the team understood the qt-material quirk and solved it correctly.

#### Issues
- **Match indicator colors are hard-coded instead of theme-derived:** Lines 155-159 in main_window.py define:
  ```python
  _MATCH_INDICATOR_COLORS = {
      MATCH_STATE_MATCH: QColor("#2ecc71"),      # green
      MATCH_STATE_DIFFERS: QColor("#e74c3c"),    # red
      MATCH_STATE_UNKNOWN: QColor("#9e9e9e"),    # gray
  }
  ```
  These do not follow the theme. The comment (lines 148-154) justifies this as "theme-independent colors" so the dot "reads the same way regardless of light/dark mode." However, this breaks the principle that all colors should derive from the active theme. The green/red are readable in both themes, but they are visually alien to the rest of the theme-driven UI.
  
  **Impact:** Inconsistent visual system. A user switching themes will see the entire table, buttons, and panels re-tint, but the tiny match indicators stay the same color. This is a minor but noticeable break in visual cohesion.

**File references:**
- `src/gdtf_comparer/gui/theme.py:40-53` (constants)
- `src/gdtf_comparer/gui/theme.py:137-157` (diff_highlight_color)
- `src/gdtf_comparer/gui/main_window.py:155-159` (_MATCH_INDICATOR_COLORS)
- `src/gdtf_comparer/gui/main_window.py:198-220` (_match_indicator_icon)

---

### Pillar 4: Typography (3/4)

#### Strengths
- **All typography delegated to qt-material theme:** No custom font sizes, weights, or families are hard-coded in the GUI code. This allows the entire app to respect the user's OS accessibility settings (font scaling, etc.) and ensures consistency with other qt-material applications.
- **UppercaseHeaderProxyModel correctly works around a qt-material quirk:** Table headers are uppercased at the model level (table_model.py:388-418) so Qt's column-sizing logic sees the actual display text, preventing clipping. This is a clean, non-stylesheet solution.
- **Section titles are clearly labeled:** "Files", "Attributes" group boxes use standard QGroupBox styling, giving clear visual hierarchy.
- **Status bar messages use monospace font for file names:** Status messages like "Removed 'file.gdtf' from the comparison list" render the file name in a consistently-readable way.

#### Issues
- **No explicit heading hierarchy in status messages:** Status messages are all plain text with no bold/italic emphasis. "Comparing 2 file(s)…" and error messages have equal visual weight, making errors less scannable.
- **Profile messages lack visual emphasis:** PROFILE_SAVED_TEMPLATE and PROFILE_RENAMED_TEMPLATE include profile names but no bold/color to highlight the important part. Especially on a light theme, these can be hard to spot.
- **Search results have no visual distinction:** The AttributePicker search hides non-matching items with `setHidden()` but doesn't highlight matching text or use a different font style for visible items vs. hidden ones. A user typing "angle" sees both BeamAngle and FieldAngle equally; there's no visual feedback that both matched the query.

**File references:**
- `src/gdtf_comparer/gui/table_model.py:388-418` (UppercaseHeaderProxyModel)
- `src/gdtf_comparer/gui/main_window.py:64-128` (message constants)
- `src/gdtf_comparer/gui/attribute_picker.py:210-250` (_apply_search)

---

### Pillar 5: Spacing (3/4)

#### Strengths
- **Critical measurements are justified and documented:** 
  - 1280x720 window (line 260, main_window.py) keeps the table area ~980px wide (measured per Phase 1's no-scrollbar tests).
  - 260px Attributes panel default (line 419) is explicitly chosen to match the sizeHint of the profile toolbar after the G-03-1 fix.
  - 240px panel minimum width (line 195) replaced 220px for the same reason.
  - MAX_COLUMN_WIDTH_PX = 280 and MIN_VALUE_COLUMN_WIDTH_PX = 120 (lines 180, 186) are capped to keep multiple comparison files visible without horizontal scrollbar.
- **Splitter sizes are consistent:** Default split [260, 1020] (line 419) matches the window width and panel sizes, no surprises.
- **Layout margins are explicit where needed:** AttributePicker (attribute_picker.py:47-48) sets `setContentsMargins(0, 0, 0, 0)` to remove padding from the tree. Results panel (main_window.py:398) does the same for a compact toggle row.
- **Qt's default spacing is used elsewhere:** Run button row (main_window.py:302-307) and file picker grid (lines 269-300) rely on Qt's default layout spacing, which is theme-aware and platform-aware.

#### Issues
- **Hard-coded pixel values don't scale with DPI:** 260px, 280px, 120px are absolute pixel values. On a 4K display (200% scale), the panel becomes proportionally narrower relative to the window, potentially squeezing the profile controls or search box. Qt's native scaling (via `QScreen.devicePixelRatio()`) is not applied to these values.
- **Table column sizing logic is complex:** `_fit_columns_to_contents()` (lines 826-870) calculates adaptive caps based on viewport width and number of comparison files. While well-reasoned for supporting "any number of comparison files," the formula `(available_width // num_value_columns)` produces uneven sizing when available_width is not evenly divisible by the column count.
- **Search box has no explicit height:** The QLineEdit in AttributePicker (line 50) uses Qt's default height. In qt-material with uppercase buttons above it, the relative visual balance could be tighter.

**File references:**
- `src/gdtf_comparer/gui/main_window.py:180-195` (layout constants)
- `src/gdtf_comparer/gui/main_window.py:260, 260, 393, 419` (window and panel sizes)
- `src/gdtf_comparer/gui/main_window.py:826-870` (_fit_columns_to_contents)
- `src/gdtf_comparer/gui/attribute_picker.py:44-60` (__init__)

---

### Pillar 6: Experience Design (3/4)

#### State Coverage

**Present and well-handled:**
1. **Empty result with all attributes unchecked (D-03):** `NO_ATTRIBUTES_SELECTED_MESSAGE` shown in status bar (main_window.py:812-814). ✓
2. **Differences-only toggle with no differing rows:** `NO_DIFFERENCES_MESSAGE` shown (line 820). ✓
3. **Comparison in progress:** Run button disabled, status shows "Comparing N file(s)…" (line 561). ✓
4. **Comparison failed:** Error dialog shown via `on_comparison_failed()` (line 872). ✓
5. **Ready state:** "Ready" shown initially (line 427). ✓
6. **Profile loaded before any comparison:** `PROFILE_LOADED_NO_RESULT_TEMPLATE` shown (line 1137-1141). ✓
7. **Selected profile items absent from current files:** `PROFILE_ITEMS_NOT_FOUND_TEMPLATE` shown (line 772-777). ✓

**Missing or weak:**
- **Live diff-highlight is present but undocumented:** The table updates its cell background when the OS theme switches, but there's no status bar message or indicator saying "theme switched." A user may not notice the re-tint immediately.
- **Long-running comparison has no progress bar:** Only status text changes. Comparison on a 100+ file fixture might take seconds with no visual feedback beyond a static "Comparing…" message.

#### Interaction Patterns

**Excellent:**
- **Search visibility-only (D-03):** Search box in AttributePicker never modifies the checked set, only calls `setHidden()` on tree items (attribute_picker.py:236-248). The implementation is correct and well-tested.
- **Toggle state persistence (D-06):** `differences_only_checkbox` is never touched by `run_comparison()` or `on_comparison_ready()` (main_window.py:547-600), so user's toggle choice survives a re-run. ✓
- **Attribute selection coalescing:** AttributePicker uses a single-shot QTimer (lines 73-76) to emit `selection_changed` once per event-loop turn, preventing the table from refiltering 30 times when a section checkbox clicks. ✓
- **Match indicators update on attribute change:** `_update_match_indicators()` is called from `_apply_attribute_selection()` (line 630), so the dots always reflect the currently-checked attributes. ✓

**Issues:**
- **No confirmation before removing comparison files:** `remove_selected_files()` (line 537) removes items immediately with no dialog. A user can accidentally delete all comparison files with a double-click. Compare with file picker UI conventions where removing a file list item usually asks "Remove?".
- **Profile load has no intermediate state:** When a user selects a profile from the dropdown, `_load_selected_profile()` (line 1095) calls `attribute_picker.set_checked()` directly. If the picker is large (60+ DMX attributes), the tree update can be visually jarring. No progress indication.
- **Error dialogs use modal windows:** `_show_error()` (line 1143) calls `QMessageBox.exec()`, which blocks the GUI. On a long-running comparison, an error arriving partway through could leave the app unresponsive for a moment. Non-blocking notifications would be better.

**File references:**
- `src/gdtf_comparer/gui/main_window.py:779-824` (_show_result_status)
- `src/gdtf_comparer/gui/main_window.py:613-647` (_apply_attribute_selection, _apply_differences_only)
- `src/gdtf_comparer/gui/main_window.py:537-545` (remove_selected_files)
- `src/gdtf_comparer/gui/main_window.py:1143-1159` (_show_error)
- `src/gdtf_comparer/gui/attribute_picker.py:73-76, 285` (coalescing timer)

---

## Files Audited

- `src/gdtf_comparer/gui/attribute_picker.py` — AttributePicker widget: search, checkboxes, section management (D-01, D-02, D-03, D-04)
- `src/gdtf_comparer/gui/table_model.py` — ComparisonTableModel, AttributeSelectionProxyModel, DifferencesOnlyProxyModel, BackgroundBrushDelegate (D-03, D-05, D-06)
- `src/gdtf_comparer/gui/main_window.py` — MainWindow layout, file pickers, results table, status messages, profile toolbar (overall UI orchestration)
- `src/gdtf_comparer/gui/theme.py` — qt-material theme application, diff-highlight color derivation, live OS color scheme switching (D-05)

---

## Summary

Phase 02 UI implementation is **well-structured and functionally correct**. All six pillars score 3/4, indicating solid quality with room for refinement in UX smoothness and visual consistency.

**Key Compliance:**
- ✓ D-01, D-02: Attributes panel is always visible with collapsible sections.
- ✓ D-03: Search narrows picker visibility only; checked set drives row display.
- ✓ D-04: Beam and Physical Properties default-checked on first use.
- ✓ D-05: Diff highlight follows qt-material theme, includes live theme switch.
- ✓ D-06: "Show differences only" toggle hides non-differing rows, preserves state.

**Recommended Fixes (Priority Order):**
1. Shorten NO_ATTRIBUTES_SELECTED_MESSAGE from 80 to ~50 chars.
2. Add visual progress feedback (spinner or progress bar) during comparison.
3. Consider theme-derived colors for match indicators, or add help text explaining the hard-coded choice.

---

*Audited: 2026-10-11 | Phase: 02-attribute-browsing-diff-highlighting | Standard: Abstract 6-pillar | Overall: 18/24 (3/4 average)*
