---
phase: "04"
slug: "standalone-packaging"
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 04-01 Task 1 | 01 | 1 | PKG-01/02 | T-04-SC | checkpoint:human-verify — package-legitimacy check for `pyinstaller==6.22.3` before install | manual | n/a — human approval gate | ❌ W0 — PyInstaller not yet a dependency | ⬜ pending |
| 04-01 Task 2 | 01 | 1 | PKG-01/02 | T-04-01 | `packaging/app.spec` builds a standalone macOS `.app`; smoke check proves launch/theme/stay-up | tracer | `PyInstaller --noconfirm --clean packaging/app.spec && python packaging/smoke_check.py --dist dist` | ❌ W0 — spec file doesn't exist yet | ⬜ pending |
| 04-01 Task 3 | 01 | 1 | PKG-01/02 | — | Smoke check correctly fails on a broken app | auto (tdd) | `pytest tests/test_smoke_check.py -q -W error::DeprecationWarning` | ❌ W0 — test file doesn't exist yet | ⬜ pending |
| 04-02 Task 1 | 02 | 2 | PKG-01/02 | T-04-SC | checkpoint:decision — "publish?" decision (repo never pushed to origin; GH token lacks `workflow` scope) | manual | n/a — human approval gate, rated one-way | ❌ N/A — decision, not a file | ⬜ pending |
| 04-02 Task 2 | 02 | 2 | PKG-01/02 | T-04-01 | CI builds + smoke-checks the macOS app on `macos-latest` | tracer | `gh run download ... && python packaging/smoke_check.py --zip ...` | ❌ W0 — `.github/workflows/release.yml` doesn't exist | ⬜ pending |
| 04-02 Task 3 | 02 | 2 | PKG-01/02 | T-04-01 | Same run adds Windows build; a version tag would publish both or neither | auto | `gh run view ... --json jobs` assertion on build-macos/build-windows/release job states | ❌ W0 — workflow doesn't exist | ⬜ pending |
| 04-03 Task 1 | 03 | 1 | PKG-03 | — | README download/bypass section matches current OS UX (corrected Gatekeeper flow) | tracer | `pytest tests/test_release_docs.py -q -W error::DeprecationWarning` | ❌ W0 — doc/test don't exist yet | ⬜ pending |
| 04-03 Task 2 | 03 | 1 | PKG-03 | — | GitHub Release description kept in sync with README by the same test | auto (tdd) | `pytest tests/test_release_docs.py -q -W error::DeprecationWarning` | ❌ W0 | ⬜ pending |
| 04-04 Task 1 | 04 | 3 | PKG-01/02/03 | T-04-01/SC | `packaging/RELEASING.md` recipe followed to publish v0.1.0; uploads verified as github-actions[bot] only | tracer | `gh release view v0.1.0 --json ...` assertions | ❌ W0 — RELEASING.md doesn't exist | ⬜ pending |
| 04-04 Task 2 | 04 | 3 | PKG-01/02/03 | — | Published downloads fetched back and re-checked; human walks both OSes | manual + auto | `gh release download v0.1.0 ... && python packaging/smoke_check.py --zip ...` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.github/workflows/release.yml` — does not exist yet; this phase's primary CI deliverable
- [ ] `packaging/app.spec` — does not exist yet; this phase's primary PyInstaller deliverable
- [ ] `pyinstaller==6.22.3` added as a dev/build dependency in `pyproject.toml` (package-legitimacy checkpoint required before this install per research)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| macOS user can download and run the packaged app with no Python install | PKG-01 | Only manifests on a genuinely downloaded, unsigned, frozen artifact outside a dev machine — pytest cannot exercise PyInstaller's freeze process or a browser-set quarantine xattr | Download the actual release `.app` from GitHub Releases (not a local build) on a real or clean Mac; launch it |
| Windows user can download and run the packaged app with no Python install | PKG-02 | Same reasoning — SmartScreen/unknown-publisher flagging only applies to a real downloaded binary | Download the actual release `.exe`/folder from GitHub Releases on a real or clean Windows machine; launch it |
| Build launches without Gatekeeper "damaged app" block (macOS) / SmartScreen block (Windows) on first run, following the documented bypass steps | PKG-03 | Inherently an OS-level security-dialog interaction; no automated test can click through a native OS prompt | Walk the documented bypass steps exactly as written in the user-facing instructions against the real downloaded artifact on both OSes; confirm the current dialog wording still matches (OS vendors change this without notice — re-verify at UAT time regardless of research age) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
