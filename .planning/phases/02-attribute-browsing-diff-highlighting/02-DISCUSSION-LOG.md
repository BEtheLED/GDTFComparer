# Phase 2: Attribute Browsing & Diff Highlighting - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-29
**Phase:** 2-Attribute Browsing & Diff Highlighting
**Areas discussed:** Attribute grouping, Selection mechanism, Diff highlighting style, Differences-only toggle, Picker location, Default selection

---

## Attribute Grouping

| Option | Description | Selected |
|--------|-------------|----------|
| Keep it as more categories in the same table | Same table, just with every GDTF category instead of only 2 | |
| Group into collapsible sections | Attributes grouped by category with expand/collapse per section | ✓ |

**User's choice:** "Group into collapsible sections and let the use choose what they want to compair" (free text, combining grouping + selection)
**Notes:** User's answer folded in the selection-mechanism decision too — collapsible sections double as the picker structure.

---

## Selection Mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Search box IS the filter/selection | Whatever matches the search is what's included | |
| Separate checkbox list, search just helps find items | Explicit check/uncheck; search only narrows the view | ✓ |

**User's choice:** Separate checkbox list, search just helps find items
**Notes:** Selection state persists independent of the last search term.

---

## Diff Highlighting Style

| Option | Description | Selected |
|--------|-------------|----------|
| Color-highlight just the differing cells | Only the specific value cell(s) get highlighted | ✓ |
| Highlight the whole row when any value differs | Entire row highlighted if any comparison differs | |

**User's choice:** Color-highlight just the differing cells

---

## Differences-Only Toggle

| Option | Description | Selected |
|--------|-------------|----------|
| Add a "show differences only" toggle | Quick way to see just what changed | ✓ |
| No toggle — just highlight, keep full list visible | Simpler; diff-only view deferred | |

**User's choice:** Add a "show differences only" toggle

---

## Picker Location

| Option | Description | Selected |
|--------|-------------|----------|
| Side panel next to the results table | Always visible, no extra clicks | ✓ |
| Separate dialog/window opened by a button | Opens on demand, keeps main window uncluttered | |

**User's choice:** Side panel next to the results table

---

## Default Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Just Beam + Physical Properties (today's set) | Matches current behavior on first use | ✓ |
| Everything checked | Full attribute set shown right away | |

**User's choice:** Just Beam + Physical Properties (today's set)

---

## Claude's Discretion

- Exact grouping/labeling of non-Beam/Physical categories from pygdtf's object model
- Exact highlight color/styling for differing cells (follow qt-material theme, light/dark)
- Exact picker widget choice and panel width/layout details
- Exact widget type for the "show differences only" toggle

## Deferred Ideas

None — discussion stayed within Phase 2 scope.
