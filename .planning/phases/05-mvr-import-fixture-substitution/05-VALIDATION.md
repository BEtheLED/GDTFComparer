---
phase: "05"
slug: "mvr-import-fixture-substitution"
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: validated
nyquist_compliant: true
wave_0_complete: false
created: "2026-10-24"
---

# Phase 05 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (pytest-qt for GUI tests) |
| **Config file** | `pyproject.toml` (`[tool.pytest.ini_options]`) |
| **Quick run command** | `"$(git rev-parse --path-format=absolute --git-common-dir)/../.venv/bin/python" -m pytest tests/core/test_<module>.py tests/gui/test_<module>.py -q -W error::DeprecationWarning` (the plan's own task-scoped `<automated>` command) |
| **Full suite command** | `"$(git rev-parse --path-format=absolute --git-common-dir)/../.venv/bin/python" -m pytest -q -W error::DeprecationWarning` |
| **Estimated runtime** | ~33 seconds (462 tests) |

---

## Sampling Rate

- **After every task commit:** Run the task's scoped `<automated>` command (new/changed test files)
- **After every plan wave:** Run the full suite command
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~33 seconds (full suite), ~1-5 seconds (task-scoped)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | PARSE-02 (package legitimacy) | T-05-SC | Human legitimacy review before any install | checkpoint:human-verify | N/A — human gate, resolved "approved" | N/A | ✅ resolved |
| 05-01-02 | 01 | 1 | SUB-02/SUB-04 (tolerance semantics) | — | One-way decision on tolerance→color rule | checkpoint:decision | N/A — human gate, resolved "option a" | N/A | ✅ resolved |
| 05-01-03 | 01 | 1 | PARSE-02, SUB-01, SUB-02, SUB-03, SUB-04 | T-05-01..T-05-08, T-05-SC | End-to-end MVR import → mark → save → rank, pymvr sandboxed via hardening | e2e (tracer) | `pytest tests/gui/test_substitution_round_trip.py` + full suite | ✅ `tests/gui/test_substitution_round_trip.py` | ✅ green |
| 05-02-01 | 02 | 2 | PARSE-02, SUB-01 | T-05-10 | Nested/accented fixture discovery, dedup, ordering | unit+gui | `pytest tests/core/test_mvr_repository.py tests/gui/test_mvr_import.py` + full suite | ✅ `tests/core/test_mvr_repository.py`, `tests/gui/test_mvr_import.py` | ✅ green |
| 05-02-02 | 02 | 2 | PARSE-02, SUB-01 | T-05-09, T-05-11, T-05-13 | Every damaged/hostile MVR → one friendly error, pymvr never sees unvalidated bytes | unit (hardening matrix) | `pytest tests/core/test_mvr_hardening.py tests/core/test_hardening.py tests/gui/test_mvr_import.py` + full suite | ✅ `tests/core/test_mvr_hardening.py` | ✅ green |
| 05-02-03 | 02 | 2 | PARSE-02, SUB-01 | T-05-12 | Single-flight import, bounded shutdown even with a stuck worker | gui+subprocess | `pytest tests/gui/test_mvr_import.py tests/gui/test_shutdown.py tests/test_fixture_builder.py` + full suite | ✅ (same files) | ✅ green |
| 05-03-01 | 03 | 2 | SUB-02 | T-05-14 | Per-fixture-type independent requirement memory (D-04) | gui | `pytest tests/gui/test_requirements_editor.py` + full suite | ✅ `tests/gui/test_requirements_editor.py` | ✅ green |
| 05-03-02 | 03 | 2 | SUB-02 | — | Table-driven default direction/tolerance with units, Must-match-only text handling (D-05, D-06) | unit+gui | `pytest tests/core/test_requirement_defaults.py tests/gui/test_requirements_editor.py` + full suite | ✅ `tests/core/test_requirement_defaults.py` | ✅ green |
| 05-03-03 | 03 | 2 | SUB-02 | T-05-14 | Declared-only rows (never a pygdtf spec default), search is visibility-only, nothing-marked is allowed | unit+gui | `pytest tests/core/test_requirement_defaults.py tests/gui/test_requirements_editor.py` + full suite | ✅ (same files) | ✅ green |
| 05-04-01 | 04 | 2 | SUB-03 | — | Requirements file round-trips byte-identically across a separate process (D-07), holds exactly one fixture (D-09) | unit+gui+subprocess | `pytest tests/core/test_requirements_repository.py tests/gui/test_requirements_file.py` + full suite | ✅ `tests/core/test_requirements_repository.py`, `tests/gui/test_requirements_file.py` | ✅ green |
| 05-04-02 | 04 | 2 | SUB-03 | T-05-16, T-05-17, T-05-18 | Strict refusal matrix: damaged/foreign/newer/oversized files refused with one plain sentence, never coerced | unit (refusal matrix)+gui | `pytest tests/core/test_requirements_repository.py tests/gui/test_requirements_file.py` + full suite | ✅ (same files) | ✅ green |
| 05-04-03 | 04 | 2 | SUB-03 | T-05-19 | Atomic save: a failed write/replace never leaves a half-written file | unit (failure injection) | `pytest tests/core/test_requirements_repository.py` + full suite | ✅ (same file) | ✅ green |
| 05-05-01 | 05 | 3 | SUB-04 | T-05-22, T-05-25, T-05-26 | Single-folder, case-insensitive `.gdtf` scan; read-only; unreadable files listed as failure rows | unit+gui | `pytest tests/core/test_substitution.py tests/gui/test_candidate_results.py` + full suite | ✅ `tests/core/test_substitution.py`, `tests/gui/test_candidate_results.py` | ✅ green |
| 05-05-02 | 05 | 3 | SUB-04 | T-05-24 | Scoring matches the user's chosen tolerance rule at every edge; ranking is fairness-only (D-11) | unit (scoring/ranking matrix) | `pytest tests/core/test_substitution.py` + full suite | ✅ (same file) | ✅ green |
| 05-05-03 | 05 | 3 | SUB-04 | T-05-23, T-05-27 | Colors visible in both themes, legend + word tooltips, one check at a time | gui (pixel sampling) + `<human-check>` | `pytest tests/gui/test_candidate_results.py` + full suite; **plus one manual visual check** (see Manual-Only) | ✅ `tests/gui/test_candidate_results.py` | ✅ green (automated); manual item below |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

All 15 behavior-bearing tasks have a real `<automated>` command, confirmed passing in the full suite (462/462 green, verified post-merge after each wave). The two checkpoint tasks (05-01-01, 05-01-02) are human decision gates, not testable behavior — both resolved during execution (package approved, tolerance option "a" chosen) and recorded in `05-01-SUMMARY.md`.

---

## Wave 0 Requirements

Existing infrastructure (pytest + pytest-qt, offscreen Qt platform, the `make_gdtf`/`make_mvr` test-data factories carried over from Phases 1-4 and extended in 05-01's `tests/conftest.py`) covers all phase requirements. No Wave 0 bootstrap was needed — every plan wrote its own test files inline with its tracer task.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|--------------------|
| Green/yellow/red traffic-light cells are visually distinguishable from each other in both light and dark theme, on a real screen | SUB-04 (D-10) | Color-distinguishability and overall readability is a subjective, render-time judgment; `test_traffic_lights_paint_in_both_themes` already proves the *channel dominance* (pixel sampling) automatically, but "is this comfortable to read" needs a human looking at the real app | Open GDTF Comparer → "Find Substitutes…" → "2. Check Inventory" tab → check a folder of real GDTF files against a saved requirements file. In both light mode and dark mode, confirm the green/yellow/red cells are easy to tell apart, the text inside is readable, and the legend above the table matches the colors. Report anything hard to read. (Deferred by design: `workflow.human_verify_mode = end-of-phase`; recorded as coverage item D9, `human_judgment: true`, in `05-05-SUMMARY.md`.) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (15/15 behavior tasks; 2 checkpoint tasks are human gates, not test-bearing)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (none were missing — existing infra sufficed)
- [x] No watch-mode flags
- [x] Feedback latency < 60s (full suite: ~33s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-10-24

## Validation Audit 2026-10-24

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
