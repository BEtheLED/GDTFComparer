---
phase: 04-standalone-packaging
plan: 01
subsystem: infra
tags: [pyinstaller, packaging, macos, qt-material, pyside6, codesign]

# Dependency graph
requires: []
provides:
  - "pyinstaller==6.22.3 pinned in pyproject.toml's dev extra"
  - "packaging/app.spec: one cross-platform PyInstaller spec (onedir, windowed, macOS BUNDLE)"
  - "packaging/smoke_check.py: reusable, non-vacuous frozen-app smoke check (dist/zip/exe sources)"
  - "tests/test_smoke_check.py: proof the smoke check catches every covered failure mode"
  - "Build command contract: python -m PyInstaller --noconfirm --clean packaging/app.spec"
  - "Smoke CLI contract: python packaging/smoke_check.py [--dist|--zip|--exe] [--startup-timeout] [--settle]"
affects: [04-02-ci-release, 04-03-first-launch-docs, 04-04-public-release]

# Actuals (#2632)
actuals:
  tokens: 6900
  tasks: 3
  commits: 2

# Tech tracking
tech-stack:
  added: [pyinstaller==6.22.3, pyinstaller-hooks-contrib==2026.8, altgraph==0.17.5, macholib==1.16.4]
  patterns:
    - "One PyInstaller spec branches on sys.platform (darwin-only BUNDLE) instead of per-OS spec files"
    - "Smoke check launches the real frozen artifact with a stripped environment and fresh fake HOME, using qt-material's own theme-icon output as startup evidence instead of polling internal app state"
    - "CLI scripts print exactly one final summary line to stdout; diagnostic detail (log tails, codesign output) goes to stderr"

key-files:
  created:
    - packaging/app.spec
    - packaging/smoke_check.py
    - tests/test_smoke_check.py
  modified:
    - pyproject.toml

key-decisions:
  - "PyInstaller 6.22.3 and its helper packages (pyinstaller-hooks-contrib, altgraph, macholib) approved by the user at the Task 1 blocking-human legitimacy checkpoint before any install ran"
  - "Local build/smoke commands on this Mac need DEVELOPER_DIR=/Library/Developer/CommandLineTools: the machine's Xcode.app is version 16.0 while the OS is macOS 26.6.2, and Xcode 16's xcodebuild crashes (dlopen symbol mismatch in CoreDevice/Mercury frameworks) when asked to resolve `lipo`, which PyInstaller's macOS build needs to thin its universal2 bootloader to arm64. Pointing DEVELOPER_DIR at the separately-installed, OS-matched Command Line Tools package resolves `lipo` (and `codesign`/`lipo` acceptance checks) without touching system-wide xcode-select. This is a local-machine-only workaround; GitHub Actions' macos-latest runners (Plan 04-02) are not expected to hit this, since their Xcode/OS pairing is Apple-maintained and kept in sync."
  - "qt-material's PyInstaller hook supplies all theme/icon/font data automatically; packaging/app.spec's datas stays empty, matching RESEARCH Pattern 2"

patterns-established:
  - "Smoke check CLI contract: exactly one final stdout line starting with 'SMOKE PASS:' or 'SMOKE FAIL:'; any multi-line diagnostic (app log tail, codesign output) goes to stderr instead of being embedded in that line"

requirements-completed: [PKG-01, PKG-02]

coverage:
  - id: D1
    description: "pyinstaller==6.22.3 pinned in the dev extra only after a human approved the Task 1 package-legitimacy checkpoint"
    requirement: "PKG-01"
    verification:
      - kind: unit
        ref: "pip show pyinstaller reports 6.22.3; git diff pyproject.toml shows exactly one added line"
        status: pass
    human_judgment: false
  - id: D2
    description: "One shared PyInstaller spec (packaging/app.spec) builds a standalone macOS GDTF Comparer.app from the existing entry point, with qt-material's data bundled automatically via its own hook (no hand-written datas list)"
    requirement: "PKG-01"
    verification:
      - kind: integration
        ref: "python -m PyInstaller --noconfirm --clean packaging/app.spec (local build, this session) -> dist/GDTF Comparer.app"
        status: pass
    human_judgment: false
  - id: D3
    description: "packaging/smoke_check.py launches the frozen app with a stripped environment and fresh fake HOME, confirms qt-material theming occurred, requires a 10s settle, and verifies the macOS code signature"
    requirement: "PKG-01"
    verification:
      - kind: integration
        ref: "python packaging/smoke_check.py --dist dist -> SMOKE PASS (this session); codesign --verify --deep --strict dist/GDTF Comparer.app exits 0; lipo -archs reports arm64"
        status: pass
    human_judgment: false
  - id: D4
    description: "The smoke check is proven not vacuous: it fails loudly (with cleanup) for a crash-at-startup, a never-themed app, a death-during-settle, a missing executable, and an unsigned macOS bundle, and passes for a healthy app"
    requirement: "PKG-01"
    verification:
      - kind: unit
        ref: "tests/test_smoke_check.py (7 tests)"
        status: pass
    human_judgment: false
  - id: D5
    description: "Shared spec and smoke check are cross-platform-ready for PKG-02 (Windows): find_executable/extract_zip branch on sys.platform, and windows_window_titles()/EnumWindows-based main-window detection is wired into run_smoke's settle loop for win32"
    requirement: "PKG-02"
    verification:
      - kind: other
        ref: "grep -n 'def windows_window_titles' / 'EnumWindows' packaging/smoke_check.py; actual Windows execution deferred to Plan 04-02's CI job per plan scope"
        status: pass
    human_judgment: true
    rationale: "No Windows machine or CI runner available in this session to execute the Windows branch end-to-end; code presence and the plan's stated division of labor (04-02 runs it on windows-latest) are the only evidence available here."

duration: 47min (includes waiting for the Task 1 human approval)
completed: 2026-10-14
status: complete
---

# Phase 4 Plan 01: Standalone macOS Packaging (PyInstaller) Summary

**One shared PyInstaller 6.22.3 spec turns `gdtf_comparer.app:main` into a standalone, ad-hoc-signed `GDTF Comparer.app` that launches with no Python installed, verified by a reusable, non-vacuous smoke check.**

## Performance

- **Duration:** 47 min (includes the pause for the Task 1 human legitimacy approval)
- **Started:** 2026-10-14T22:23:50Z (checkpoint reached)
- **Completed:** 2026-10-14T23:13:23Z
- **Tasks:** 3 (Task 1 checkpoint approved, Task 2 build, Task 3 hardening tests)
- **Files modified:** 4 (`pyproject.toml`, `packaging/app.spec`, `packaging/smoke_check.py`, `tests/test_smoke_check.py`)

## Accomplishments

- Package-legitimacy checkpoint for PyInstaller 6.22.3 (and its helper packages) explicitly approved by the user before any install ran
- `packaging/app.spec`: one PyInstaller 6 spec, repo-root-relative via `SPECPATH`, builds a windowed `onedir` app with `datas=[]` (qt-material's own hook supplies its theme/icon data), and a macOS-only `BUNDLE` with bundle id `io.github.betheled.gdtfcomparer`
- `packaging/smoke_check.py`: standard-library-only CLI that launches the frozen app in a stripped environment with a fresh fake `HOME`, waits for qt-material's theme icons as startup evidence, requires a settle period, verifies the macOS code signature, and now also supports Windows main-window/error-dialog detection via `EnumWindows` for Plan 04-02's CI job
- Local, end-to-end proof on this Mac: `dist/GDTF Comparer.app` builds, launches, themes, stays up, passes `codesign --verify --deep --strict`, and is a genuine `arm64` binary
- `tests/test_smoke_check.py`: 7 tests proving the smoke check actually catches a startup crash, a never-themed app, a settle-period death, a missing executable, and an unsigned bundle -- not just that it can report success
- Full existing suite (283 tests) still green with PyInstaller installed in the shared venv and no `src/` changes

## Task Commits

1. **Task 1: Package legitimacy review before installing PyInstaller** - checkpoint approved by user (no commit; nothing installed until approval)
2. **Task 2: End-to-end macOS standalone build from one shared spec** - `4d89b20` (feat)
3. **Task 3: Smoke check hardening + non-vacuous test proof** - `adb8ede` (test)

**Plan metadata:** pending (this SUMMARY's commit)

## Files Created/Modified

- `pyproject.toml` - Added `"pyinstaller==6.22.3",` to `[project.optional-dependencies] dev`, after `pytest-qt`; runtime `dependencies` unchanged
- `packaging/app.spec` - New: single cross-platform PyInstaller spec (`Analysis`, `PYZ`, `EXE`, `COLLECT`, macOS-only `BUNDLE`)
- `packaging/smoke_check.py` - New: `find_executable`, `verify_app_signature`, `extract_zip`, `smoke_environment`, `run_smoke`, `windows_window_titles`, `main`
- `tests/test_smoke_check.py` - New: 7 tests driving fake POSIX executables through every covered failure mode plus a healthy pass

## Decisions Made

- PyInstaller 6.22.3 and its helper packages (pyinstaller-hooks-contrib 2026.8, altgraph 0.17.5, macholib 1.16.4; packaging 26.3 and setuptools 84.0.0 were already present) approved by the user at the Task 1 checkpoint exactly as listed, with no substitutions.
- This Mac's local build/smoke commands require `DEVELOPER_DIR=/Library/Developer/CommandLineTools` as an environment-variable prefix (not a repo change, not a system-wide `xcode-select --switch`) because the installed Xcode.app (16.0) predates this machine's macOS (26.6.2); its `xcodebuild` crashes with a `dlopen` symbol mismatch when PyInstaller's build asks it to locate `lipo`, which is needed to thin the universal2 bootloader to `arm64`. The separately-installed Command Line Tools package (26.6.0, OS-matched) resolves `lipo` correctly when selected via this env var alone. This is recorded here for whoever next builds locally on this machine; GitHub Actions' `macos-latest` runners (Plan 04-02) keep Xcode and the OS in sync, so this is not expected to recur in CI.
- qt-material's bundled PyInstaller hook is relied on entirely for theme/font/icon data; `packaging/app.spec`'s `datas` stays `[]`, confirmed present in the built bundle (`light_blue.xml`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking, environment-only] Local PyInstaller build needs `DEVELOPER_DIR` override for a broken `lipo` resolution**
- **Found during:** Task 2, first local build attempt
- **Issue:** `python -m PyInstaller --noconfirm --clean packaging/app.spec` failed at the `EXE` step: `lipo -thin arm64 ...` crashed because this Mac's active `xcode-select` developer directory (`/Applications/Xcode.app`, version 16.0) is incompatible with the installed OS (macOS 26.6.2) -- its `xcodebuild` aborts with a `dlopen` symbol error when resolving `lipo`.
- **Fix:** Ran the build and smoke-check commands with `DEVELOPER_DIR=/Library/Developer/CommandLineTools` (the separately-installed, OS-matched Command Line Tools package) set as an environment variable for those commands only. No repo file was changed; no system-wide `xcode-select --switch` was run.
- **Files modified:** none (environment variable only, scoped to this session's build/verify commands)
- **Verification:** Build completed; `dist/GDTF Comparer.app` built, `codesign --verify --deep --strict` passed, `lipo -archs` (also run with the same `DEVELOPER_DIR` override) reported `arm64`
- **Committed in:** n/a (no file change)

**2. [Rule 1 - Bug] Smoke check launched a relative `--dist` executable path after changing the child's cwd, causing a `FileNotFoundError`**
- **Found during:** Task 2, first local smoke-check run after a successful build
- **Issue:** `run_smoke` set the child process's `cwd` to the fresh fake-home folder but launched `exe` using its original (relative, e.g. `dist/GDTF Comparer.app/...`) path, so the OS looked for it relative to the new cwd instead of the real working directory.
- **Fix:** `run_smoke` now resolves `exe` to an absolute path (`exe = exe.resolve()`) before launching.
- **Files modified:** `packaging/smoke_check.py`
- **Verification:** Re-ran `python packaging/smoke_check.py --dist dist` -> `SMOKE PASS`
- **Committed in:** `4d89b20` (Task 2 commit)

**3. [Rule 1 - Bug] Failure messages embedded a multi-line log/codesign tail inside the text that becomes the final "SMOKE FAIL" line, violating the plan's "exactly one final line" CLI contract**
- **Found during:** Task 3, while writing tests that check `captured.out.strip().splitlines()[-1]` starts with `SMOKE FAIL`/`SMOKE PASS`
- **Issue:** `run_smoke`'s failure returns and `main()`'s signature-check failure both appended a multi-line diagnostic (log tail or codesign output) directly after the short reason in the same string that got printed to stdout, so the truly last printed line was often a fragment of that diagnostic, not the summary line.
- **Fix:** Added `_print_diagnostic()`, which writes any multi-line detail to stderr; `run_smoke` and `main()` now print that detail separately (to stderr) and keep the reason string embedded in the single `SMOKE PASS:`/`SMOKE FAIL:` line short and single-line.
- **Files modified:** `packaging/smoke_check.py`
- **Verification:** All 7 `tests/test_smoke_check.py` tests pass, each asserting on the final stdout line; full build + smoke re-verified end to end after this change (`SMOKE PASS`)
- **Committed in:** `adb8ede` (Task 3 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking/environment-only, 2 bugs)
**Impact on plan:** All three were necessary to get a working local build/verify loop and to meet the plan's own CLI-output contract. No scope creep -- no `src/` files touched, no new dependencies beyond the approved PyInstaller install.

## Issues Encountered

- This Mac's Xcode/OS version mismatch (see Decisions Made and Deviation 1) blocks any local PyInstaller macOS build unless `DEVELOPER_DIR` is overridden. This is a local development-environment quirk, not a project defect, and does not affect the CI builds planned for 04-02.

## User Setup Required

None - no external service configuration required. (Note for local rebuilds on this machine only: prefix `PY -m PyInstaller ...` and any `lipo`/build commands with `DEVELOPER_DIR=/Library/Developer/CommandLineTools` until this machine's Xcode.app is updated to match the OS.)

## Next Phase Readiness

- Build command (`python -m PyInstaller --noconfirm --clean packaging/app.spec`) and smoke CLI (`python packaging/smoke_check.py [--dist|--zip|--exe] ...`) contracts are fixed and proven locally on macOS -- Plan 04-02 can reuse both unchanged in its `macos-latest` and `windows-latest` CI jobs.
- `windows_window_titles()`/`EnumWindows` wiring exists in `run_smoke` for the win32 settle loop, but has not been exercised on a real Windows machine or CI runner in this session (see coverage D5) -- Plan 04-02's `windows-latest` job is the first real test of that path.
- No blockers for 04-02, 04-03 or 04-04.

---
*Phase: 04-standalone-packaging*
*Completed: 2026-10-14*

## Self-Check: PASSED

All created files found on disk (`pyproject.toml`, `packaging/app.spec`, `packaging/smoke_check.py`, `tests/test_smoke_check.py`, this SUMMARY). Both task commits (`4d89b20`, `adb8ede`) confirmed as ancestors of HEAD.
