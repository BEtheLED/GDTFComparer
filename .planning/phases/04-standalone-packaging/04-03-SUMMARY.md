---
phase: 04-standalone-packaging
plan: 03
subsystem: docs
tags: [pyinstaller, gatekeeper, smartscreen, release-notes, pytest]

# Dependency graph
requires:
  - phase: 04-standalone-packaging (plan 01)
    provides: PyInstaller build producing GDTF-Comparer-macos.zip / GDTF-Comparer-windows.zip naming used by these docs
provides:
  - README.md "Download and run (no Python needed)" section with corrected macOS System Settings Gatekeeper flow and Windows SmartScreen/Smart App Control steps
  - packaging/release-notes.md as the GitHub Release description body (consumed by Plan 04-02's body_path)
  - tests/test_release_docs.py keeping both documents aligned on every safety-critical step
affects: [04-04 (release/UAT plan that walks these exact steps on a real machine), ship]

# Actuals (#2632)
actuals:
  tokens: 3900
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns: ["Shared doc-consistency test (section() heading-range helper) parametrized over both README.md and packaging/release-notes.md so first-launch instructions can't silently drift apart"]

key-files:
  created:
    - packaging/release-notes.md
    - tests/test_release_docs.py
  modified:
    - README.md

key-decisions:
  - "Corrected D-01's bypass wording per RESEARCH Pitfall P1: replaced the removed right-click->Open macOS shortcut with the current System Settings -> Privacy & Security -> Open Anyway flow, plus an xattr -cr fallback scoped to /Applications/GDTF Comparer.app only"
  - "packaging/release-notes.md still links https://github.com/BEtheLED/GDTFComparer/releases/latest (as a low-key 'looking for the newest build?' line) even though the reader is already on the release page — kept so the shared test suite (which runs every document test, including the latest-release-link check, against both files) has one honest source of truth rather than a doc-specific test exemption"

requirements-completed: [PKG-03]

coverage:
  - id: D1
    description: "README's 'Download and run (no Python needed)' section tells a Mac or Windows user which file to download and walks them through first launch using the current (post-Sequoia) Gatekeeper flow and current SmartScreen/Smart App Control flow, scoped to this app only"
    requirement: "PKG-03"
    verification:
      - kind: unit
        ref: "tests/test_release_docs.py::test_mac_steps_use_current_gatekeeper_flow[README.md]"
        status: pass
      - kind: unit
        ref: "tests/test_release_docs.py::test_windows_steps[README.md]"
        status: pass
      - kind: unit
        ref: "tests/test_release_docs.py::test_no_system_wide_security_off_switch[README.md]"
        status: pass
    human_judgment: false
  - id: D2
    description: "packaging/release-notes.md (the GitHub Release description) carries the same download names, first-launch steps and safety scope as the README, using only absolute links, with no developer setup instructions"
    requirement: "PKG-03"
    verification:
      - kind: unit
        ref: "tests/test_release_docs.py::test_windows_steps[release-notes.md]"
        status: pass
      - kind: unit
        ref: "tests/test_release_docs.py::test_release_notes_links_are_absolute"
        status: pass
      - kind: unit
        ref: "tests/test_release_docs.py::test_release_notes_have_no_developer_setup"
        status: pass
      - kind: unit
        ref: "tests/test_release_docs.py::test_docs_agree_on_download_names"
        status: pass
    human_judgment: false
  - id: D3
    description: "The exact current-OS dialog wording and click path (System Settings labels, SmartScreen/Smart App Control screens) actually matches what a real current macOS and Windows machine shows, since OS vendors change these flows without notice (RESEARCH Open Question 1)"
    requirement: "PKG-03"
    verification: []
    human_judgment: true
    rationale: "No automated test can click through a native OS security dialog or confirm current OS wording; RESEARCH.md explicitly flags this as needing a live-machine check. Plan 04-04's human-verify checkpoint walks these exact steps on a real current macOS and Windows machine."

duration: 5min
completed: 2026-10-14
status: complete
---

# Phase 4 Plan 3: First-launch bypass instructions Summary

**Corrected (post-Sequoia) macOS Gatekeeper and Windows SmartScreen first-launch instructions in README.md and a new packaging/release-notes.md, kept in sync by a 19-test pytest suite that forbids any system-wide security-off wording.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-10-14T23:17:00Z
- **Completed:** 2026-10-14T23:22:19Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- README.md now opens with a "Download and run (no Python needed)" section: a two-row download table (Apple silicon vs. Windows 10/11), numbered macOS steps using the current System Settings -> Privacy & Security -> Open Anyway flow (never the removed right-click shortcut), a scoped `xattr -cr` fallback for the "is damaged" dialog, numbered Windows steps covering Extract All, the `_internal` folder, Edge's "isn't commonly downloaded" warning, and "Windows protected your PC" -> More info -> Run anyway, plus an honest "Why do I see a warning?" explanation scoped to this project's Releases page.
- README's existing run-from-source sections (Requirements, Setup, Run, Test, Project Layout, Safety, Blender Addon) are preserved, now flagged as developer-only; the stale "Phase 1" intro sentence was replaced with a description of the app's current capabilities (browse/search attributes, diff highlighting, compare profiles).
- New `packaging/release-notes.md` carries the same steps and safety scope for the GitHub Release description (consumed by Plan 04-02's `body_path`), using only absolute links and no developer setup instructions.
- New `tests/test_release_docs.py` (19 tests) enforces: both downloads named correctly, no removed macOS right-click/Control-click wording, the `xattr` command is always scoped to `/Applications/GDTF Comparer.app`, Windows steps are complete, the "why a warning" explanation names the unsigned-build reason and scopes the bypass to this project's Releases page, and — critically — neither document ever tells a user to disable Gatekeeper/SmartScreen/Smart App Control/Defender/antivirus system-wide.

## Task Commits

1. **Task 1: README "Download and run" section plus its test** - `f666ff5` (docs)
2. **Task 2: packaging/release-notes.md kept in sync with the README via the same test file** - `88f4673` (test)

**Plan metadata:** (this commit)

_Note: Task 2 followed the TDD red/green flow — the test file was extended first (RED, confirmed failing because `packaging/release-notes.md` didn't exist), then the file was created (GREEN, 19/19 passing)._

## Files Created/Modified
- `README.md` - New "Download and run (no Python needed)" section; refreshed intro; Requirements section marked developer-only
- `packaging/release-notes.md` - New GitHub Release description with the same first-launch steps and safety scope
- `tests/test_release_docs.py` - New doc-consistency and safety test suite (19 tests) parametrized over both documents

## Decisions Made
- Corrected D-01's locked wording per RESEARCH.md Pitfall P1: the macOS right-click -> Open shortcut was removed in macOS Sequoia (15, Sept 2024), so the shipped instructions use System Settings -> Privacy & Security -> Open Anyway instead, with a Terminal `xattr -cr` alternative for the "is damaged" dialog that has no Open Anyway button.
- `packaging/release-notes.md` keeps a low-key "Looking for the newest build?" link to `/releases/latest` even though the reader is already on the release page — the plan's prose suggested omitting this pointer, but the plan's own test spec requires every Task 1 document test (including the latest-release-link check) to pass against both documents, so the automated contract took precedence over the softer wording guidance (Claude's discretion over wording, per D-01).

## Deviations from Plan

None requiring a rule — one wording tension noted above (Decisions Made) was resolved in favor of the plan's explicit, measurable test requirements over its looser prose guidance, which the plan itself frames as Claude's discretion.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- README and release-notes.md are ready for Plan 04-02's release workflow to consume as the `body_path`.
- Plan 04-04's human-verify checkpoint still needs to walk these exact steps on a real current macOS and Windows machine (RESEARCH Open Question 1, flagged in coverage item D3 above) before PKG-03 can be considered fully verified end-to-end.
- No blockers for proceeding to the remaining Phase 4 plan(s).

---
*Phase: 04-standalone-packaging*
*Completed: 2026-10-14*

## Self-Check: PASSED

All created files confirmed present on disk (README.md, packaging/release-notes.md, tests/test_release_docs.py, this SUMMARY.md); both task commits (f666ff5, 88f4673) confirmed as ancestors of HEAD.
