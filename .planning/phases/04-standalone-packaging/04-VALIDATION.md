---
phase: "04"
slug: "standalone-packaging"
status: validated
nyquist_compliant: true
wave_0_complete: true
created: "2026-10-14"
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.1.1 + pytest-qt 4.5.0 (existing, per `pyproject.toml`) |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` (existing) |
| **Quick run command** | `pytest tests/ -x` |
| **Full suite command** | `pytest tests/` |
| **Estimated runtime** | ~30 seconds (existing suite; this phase adds no new application code) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x` only if the task touched `pyproject.toml` (packaging-only tasks — CI YAML, `.spec` files, docs — add no app code and have nothing for pytest to exercise)
- **After every plan wave:** Run `pytest tests/` to confirm packaging-phase edits to `pyproject.toml` haven't broken the existing suite
- **Before `/gsd-verify-work`:** Full suite must be green AND the manual cross-machine UAT below must be walked
- **Max feedback latency:** 30 seconds (existing suite)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01 Task 1 | 01 | 1 | PKG-01/02 | T-04-SC | checkpoint:human-verify — package-legitimacy check for `pyinstaller==6.22.3` before install | manual | n/a — human approval gate | ✅ pyinstaller==6.22.3 pinned in pyproject.toml | ✅ green |
| 04-01 Task 2 | 01 | 1 | PKG-01/02 | T-04-01 | `packaging/app.spec` builds a standalone macOS `.app`; smoke check proves launch/theme/stay-up | tracer | `PyInstaller --noconfirm --clean packaging/app.spec && python packaging/smoke_check.py --dist dist` | ✅ packaging/app.spec exists | ✅ green |
| 04-01 Task 3 | 01 | 1 | PKG-01/02 | — | Smoke check correctly fails on a broken app | auto (tdd) | `pytest tests/test_smoke_check.py -q -W error::DeprecationWarning` | ✅ tests/test_smoke_check.py exists | ✅ green |
| 04-02 Task 1 | 02 | 2 | PKG-01/02 | T-04-SC | checkpoint:decision — "publish?" decision (repo never pushed to origin; GH token lacks `workflow` scope) | manual | n/a — human approval gate, rated one-way | ✅ decision recorded in 04-02-SUMMARY.md (hold, then publish) | ✅ green |
| 04-02 Task 2 | 02 | 2 | PKG-01/02 | T-04-01 | CI builds + smoke-checks the macOS app on `macos-latest` | tracer | `gh run download ... && python packaging/smoke_check.py --zip ...` | ✅ .github/workflows/release.yml exists | ✅ green |
| 04-02 Task 3 | 02 | 2 | PKG-01/02 | T-04-01 | Same run adds Windows build; a version tag would publish both or neither | auto | `gh run view ... --json jobs` assertion on build-macos/build-windows/release job states | ✅ workflow has build-windows + release jobs | ✅ green |
| 04-03 Task 1 | 03 | 1 | PKG-03 | — | README download/bypass section matches current OS UX (corrected Gatekeeper flow) | tracer | `pytest tests/test_release_docs.py -q -W error::DeprecationWarning` | ✅ README.md + packaging/release-notes.md exist | ✅ green |
| 04-03 Task 2 | 03 | 1 | PKG-03 | — | GitHub Release description kept in sync with README by the same test | auto (tdd) | `pytest tests/test_release_docs.py -q -W error::DeprecationWarning` | ✅ tests/test_release_docs.py exists | ✅ green |
| 04-04 Task 1 | 04 | 3 | PKG-01/02/03 | T-04-01/SC | `packaging/RELEASING.md` recipe followed to publish v0.1.0; uploads verified as github-actions[bot] only | tracer | `gh release view v0.1.0 --json ...` assertions | ✅ packaging/RELEASING.md exists; release v0.1.0 published | ✅ green |
| 04-04 Task 2 | 04 | 3 | PKG-01/02/03 | — | Published downloads fetched back and re-checked; human walks both OSes | manual + auto | `gh release download v0.1.0 ... && python packaging/smoke_check.py --zip ...` | ✅ automated half ran against the live v0.1.0 release | ⚠️ partial — automated checks green; the two human cross-machine checks are queued for end-of-phase UAT (see Manual-Only Verifications) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `.github/workflows/release.yml` — exists, with green `build-macos`/`build-windows`/`release` jobs proven by hand-started and tag-triggered runs
- [x] `packaging/app.spec` — exists; builds a working standalone macOS app proven by `smoke_check.py`
- [x] `pyinstaller==6.22.3` added as a dev/build dependency in `pyproject.toml` (package-legitimacy checkpoint approved in 04-01 Task 1)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| macOS user can download and run the packaged app with no Python install | PKG-01 | Only manifests on a genuinely downloaded, unsigned, frozen artifact outside a dev machine — pytest cannot exercise PyInstaller's freeze process or a browser-set quarantine xattr | Download the actual release `.app` from GitHub Releases (not a local build) on a real or clean Mac; launch it |
| Windows user can download and run the packaged app with no Python install | PKG-02 | Same reasoning — SmartScreen/unknown-publisher flagging only applies to a real downloaded binary | Download the actual release `.exe`/folder from GitHub Releases on a real or clean Windows machine; launch it |
| Build launches without Gatekeeper "damaged app" block (macOS) / SmartScreen block (Windows) on first run, following the documented bypass steps | PKG-03 | Inherently an OS-level security-dialog interaction; no automated test can click through a native OS prompt | Walk the documented bypass steps exactly as written in the user-facing instructions against the real downloaded artifact on both OSes; confirm the current dialog wording still matches (OS vendors change this without notice — re-verify at UAT time regardless of research age) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** validated 2026-10-25. All automated coverage is green (462/462 pytest suite, plus each plan's own CI/`gh`-based tracer and auto verify commands, run live and confirmed passing by their executors). The two genuinely manual checks (real-Mac Gatekeeper walkthrough, real-Windows SmartScreen walkthrough, both in 04-04 Task 2's Manual-Only row) remain queued for end-of-phase UAT — that is the correct, documented Nyquist disposition for OS-security-dialog behavior, not a gap.

## Validation Audit 2026-10-25

| Metric | Count |
|---|---|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
