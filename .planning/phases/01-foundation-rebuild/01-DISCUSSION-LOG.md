# Phase 1: Foundation Rebuild - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-09-25
**Phase:** 1-Foundation Rebuild
**Areas discussed:** GUI framework swap, Visual style direction, pygdtf data model depth, Service layer & threading

---

## GUI framework swap

| Option | Description | Selected |
|--------|-------------|----------|
| PySide6 (Qt) | Research pick: real table/model views for a diff-highlighted comparison grid with search/filter, LGPL/free to ship, mature PyInstaller hooks. Bigger rewrite than reskinning Tkinter. | ✓ |
| CustomTkinter | Lowest rewrite risk — reuses BEtheLD's widget layout with a modern skin, but much weaker table/grid widget. | |
| You decide | Let Claude pick PySide6 per research. | |

**User's choice:** PySide6 (Qt)

| Option | Description | Selected |
|--------|-------------|----------|
| 3.11+ | Required floor for the full research-recommended stack (PySide6, websockets, zeroconf). | ✓ |
| 3.8+ (current stated floor) | Matches PROJECT.md's stated "3.7+" more closely, but would mean re-deciding later. | |

**User's choice:** 3.11+

| Option | Description | Selected |
|--------|-------------|----------|
| Proper package layout | Split into modules (core/service package, gui package, tests/) — matches decoupled architecture goal (UI-02). | ✓ |
| Keep single-script style | Stay closer to BEtheLD's current single-file shape. | |

**User's choice:** Proper package layout

| Option | Description | Selected |
|--------|-------------|----------|
| Rewrite from scratch | Framework + parser swap means most existing code doesn't carry over directly. | ✓ |
| Port incrementally | Preserve BEtheLD's existing method names/flow while swapping the underlying framework/parser. | |

**User's choice:** Rewrite from scratch

**Notes:** All four questions in this area resolved with the research-recommended option.

---

## Visual style direction

| Option | Description | Selected |
|--------|-------------|----------|
| qt-material | Flat Material-Design-style reskin, ~2 lines to apply. Fastest path to visual refresh. | ✓ |
| PySide6-Fluent-Widgets | Windows-11 Fluent look, heavier/more opinionated widget set. | |
| You decide | Let Claude pick qt-material per research. | |

**User's choice:** qt-material

| Option | Description | Selected |
|--------|-------------|----------|
| Dark | Common preference for lighting/AV pros working in dark show environments. | |
| Light | Higher contrast in normal office/daylight settings. | |
| Follow OS setting | Respect the user's system light/dark preference automatically. | ✓ |

**User's choice:** Follow OS setting

| Option | Description | Selected |
|--------|-------------|----------|
| Claude's judgment | Pick a clean, professional accent/theme variant — no specific reference needed. | ✓ |
| I have a reference in mind | User describes a specific app/color/style. | |

**User's choice:** Claude's judgment

| Option | Description | Selected |
|--------|-------------|----------|
| Functional modern baseline | Apply qt-material theming and clean layout; don't over-invest in custom styling yet. | ✓ |
| Invest more now in a polished look | Spend more Phase 1 effort on custom styling/icons/layout details. | |

**User's choice:** Functional modern baseline

**Notes:** User chose "Follow OS setting" over the flagged-as-simpler dark/light default — accepted the extra qt-material theme-switching setup this implies.

---

## pygdtf data model depth

| Option | Description | Selected |
|--------|-------------|----------|
| Wrap pygdtf's model directly | Build around pygdtf's actual object model rather than flattening to a dict — sets up Phase 2 cleanly. | ✓ |
| Minimal flat bridge for now | Less Phase 1 work, but Phase 2 will need to revisit the data layer. | |

**User's choice:** Wrap pygdtf's model directly

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current 2 categories for now | Phase 1's goal is crash-free comparison + modernized shell; full browsing is Phase 2's job. | ✓ |
| Show everything pygdtf can extract | Risks overlapping with Phase 2 scope, cluttered table before filtering exists. | |

**User's choice:** Keep current 2 categories for now

| Option | Description | Selected |
|--------|-------------|----------|
| Namespace by element path | Key each attribute by its full path/context, matching pygdtf's structured model. | ✓ |
| You decide | Let Claude design the exact keying/namespacing scheme. | |

**User's choice:** Namespace by element path

| Option | Description | Selected |
|--------|-------------|----------|
| Rely on pygdtf's own errors | pygdtf raises on malformed input; catch and show a friendly message. | ✓ |
| Add explicit pre-validation | More Phase 1 work for clearer error messages. | |

**User's choice:** Rely on pygdtf's own errors

**Notes:** All four questions resolved with the research-recommended option.

---

## Service layer & threading

| Option | Description | Selected |
|--------|-------------|----------|
| A ComparisonResult object | Typed dataclass/model instead of raw dicts — gives Phase 2/3 a clean contract. | ✓ |
| Plain dicts | Simpler now, but Phase 2/3 will likely need structure later anyway. | |

**User's choice:** A ComparisonResult object

| Option | Description | Selected |
|--------|-------------|----------|
| Move parsing off the UI thread now | QThread/worker for parse+compare; fixes known UI-freeze issue now rather than later. | ✓ |
| Keep it synchronous for Phase 1 | Simpler to build/test; success criteria only require crash-free, not responsive. | |

**User's choice:** Move parsing off the UI thread now

| Option | Description | Selected |
|--------|-------------|----------|
| Batch API | compare(target, [files]) → one ComparisonResult covering all files at once. | ✓ |
| One-at-a-time | compare_one(target, file) per file, merged by the GUI — works against decoupling goal. | |

**User's choice:** Batch API

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated package (e.g. core/) | Matches the proper-package-layout decision; importable/testable independent of Qt. | ✓ |
| Single service.py file | Less structure now, may need splitting later. | |

**User's choice:** Dedicated package (e.g. `core/`)

**Notes:** All four questions resolved with the research-recommended option.

---

## Claude's Discretion

- Exact qt-material accent color/theme variant (Visual style direction — no specific reference supplied).
- Exact attribute-namespacing/keying scheme, as long as it follows pygdtf's structured model (pygdtf data model depth).

## Deferred Ideas

None — discussion stayed entirely within Phase 1 scope; no scope-creep items were raised.
