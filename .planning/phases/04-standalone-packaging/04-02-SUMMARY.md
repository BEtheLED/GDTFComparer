---
phase: 04-standalone-packaging
plan: 02
subsystem: infra
tags: [github-actions, ci, release, pyinstaller]

# Dependency graph
requires:
  - phase: 04-standalone-packaging (plan 01)
    provides: packaging/app.spec, packaging/smoke_check.py, local macOS build proof
provides:
  - "Public GitHub repository (github.com/BEtheLED/GDTFComparer), published with the user's explicit go-ahead"
  - ".github/workflows/release.yml: three-job CI pipeline (build-macos, build-windows, release), proven green on a hand-started run"
  - "A hand-started run whose macos-build and windows-build downloads both passed the smoke check; release correctly skipped (no tag pushed)"
affects: [04-04 (release/publish plan — now unblocked: CI pipeline exists and is proven green)]

# Actuals (#2632)
actuals:
  tokens: 1244
  tasks: 3
  commits: 2
  plan_head_before: 63d0fa7a9efecb5cdb9b67c1109a2a7de8ffc488
  plan_head_after: af09300b2523d30a1279f646b94fefb30f2834d1

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Explicit named jobs (build-macos, build-windows, release) instead of a matrix, each with its own OS-native zip step and a smoke-check gate before upload"
    - "release job gated on both build jobs succeeding (needs:) and on the ref being a v* tag (if:), so a half-built or half-checked release can never publish"
    - "Tag-vs-version guard reads the tag only through a TAG_NAME environment variable, never by expanding the GitHub Actions expression inside a shell/Python script"

key-files:
  created:
    - .github/workflows/release.yml
  modified: []

key-decisions:
  - "Task 1 publish decision, first answer (2026-10-14): 'hold' — nothing was sent to GitHub; this plan's Tasks 2-3 did no work and 04-02-SUMMARY.md recorded only the halt."
  - "Task 1 publish decision, final answer (2026-10-25): 'publish' — the user was asked again directly and explicitly answered 'Yes, publish now,' superseding the earlier hold. This resumed execution proceeded on that basis without re-asking the Task 1 checkpoint."
  - "git push failed twice with 'RPC failed; HTTP 400 ... unexpected disconnect while reading sideband packet' on the first-ever push of ~230 commits of history over HTTPS. Root cause: git's default http.postBuffer (1 MiB) was too small for this push. Fixed by running `git config http.postBuffer 524288000` (500 MB) in this worktree, after which the push succeeded immediately. This is a local git-client setting, not a GitHub-side limit — the repository itself is small (full .git is ~7.9 MB; no object over ~81 KB)."
  - "softprops/action-gh-release pinned to v3.0.3's commit SHA (efb35369e0ad2afab669f228072c1b0d510eae64) — same SHA the plan's Assumptions Log had already pre-verified at planning time (2026-10-14); re-verified identical at execution time (2026-10-25) via `gh api repos/softprops/action-gh-release/releases/latest` and `.../commits/v3.0.3`."
  - "actions/checkout, actions/setup-python and actions/upload-artifact pinned to @v7 (not @v4/@v5 as in the original 2026-10-14 RESEARCH.md draft) per the plan's own flagged-assumption update; actions/download-artifact pinned to @v8. All current majors re-confirmed live via `gh api .../releases/latest` immediately before writing the workflow."
  - "No Windows-only fixes were needed to packaging/app.spec or packaging/smoke_check.py — the Windows build, zip structure, and smoke check (including the Windows main-window-title and PyInstaller-error-dialog EnumWindows checks wired in by Plan 04-01) all passed on the very first CI run."

patterns-established:
  - "Tag reaches a release-gating script only through an environment variable (TAG_NAME), never through direct expression interpolation into a shell/Python heredoc — mitigates script injection via a maliciously named tag (T-04-09)."

requirements-completed: [PKG-01, PKG-02]

coverage:
  - id: D1
    description: "Task 1 blocking-human publish decision answered 'publish' (after an earlier 'hold'); the project's ~230 commits of history (app code, planning notes, this phase's build files) are now public at github.com/BEtheLED/GDTFComparer"
    requirement: "PKG-01"
    verification:
      - kind: other
        ref: "git ls-remote origin main reports af09300b2523d30a1279f646b94fefb30f2834d1, identical to local HEAD; git rev-list --count origin/main..HEAD reports 0"
        status: pass
    human_judgment: true
    rationale: "The publish/hold decision and its consequence (making prior private work permanently public) is inherently a judgment call only the project owner can make; this entry records that the decision was made and the technical state matches it, not that automation decided to publish."
  - id: D2
    description: ".github/workflows/release.yml builds the macOS app on a macos-latest GitHub Actions runner from the pushed code, smoke-checks the zipped download in CI, and the same zip re-verified SMOKE PASS and arm64 on this Mac after download"
    requirement: "PKG-01"
    verification:
      - kind: integration
        ref: "gh run view 40202021705 --json jobs reports build-macos conclusion success; local re-run of packaging/smoke_check.py --zip against the downloaded macos-build artifact printed 'SMOKE PASS: ... started, applied its theme and stayed up 10.0 s'; lipo -archs on the extracted binary reported arm64"
        status: pass
    human_judgment: false
  - id: D3
    description: ".github/workflows/release.yml builds the Windows app on a windows-latest runner, zips it with Compress-Archive into a 'GDTF Comparer' top-level folder containing GDTF Comparer.exe and _internal/, smoke-checks it in CI (including the Windows main-window-title and PyInstaller-error-dialog checks), and the downloaded zip's structure was independently re-verified"
    requirement: "PKG-02"
    verification:
      - kind: integration
        ref: "gh run view 40202021705 --json jobs reports build-windows conclusion success; downloaded windows-build artifact's zip contains 'GDTF Comparer/GDTF Comparer.exe' and an entry starting with 'GDTF Comparer/_internal/' (325 total entries)"
        status: pass
    human_judgment: false
  - id: D4
    description: "A hand-started run (workflow_dispatch) builds and checks both downloads without publishing: release job is correctly 'skipped' because the ref is not a v* tag, and only release gets contents: write"
    requirement: "PKG-01"
    verification:
      - kind: integration
        ref: "gh run view 40202021705 --json jobs --jq '[.jobs[]|{name,conclusion}]' reported build-macos: success, build-windows: success, release: skipped"
        status: pass
    human_judgment: false
  - id: D5
    description: "The release job is version-guarded (tag must equal 'v' + pyproject.toml version) and tag text reaches the guard script only via the TAG_NAME environment variable; only the release job has contents: write; every checkout uses persist-credentials: false; no repository secret is referenced; softprops/action-gh-release is pinned to a full 40-character commit SHA"
    requirement: "PKG-01"
    verification:
      - kind: other
        ref: "grep -c 'contents: write' .github/workflows/release.yml -> 1; grep -c 'persist-credentials: false' .github/workflows/release.yml -> 3; grep -nF 'secrets.' .github/workflows/release.yml -> no match; grep -nE 'softprops/action-gh-release@[0-9a-f]{40}' .github/workflows/release.yml -> match; grep -n TAG_NAME .github/workflows/release.yml -> match"
        status: pass
    human_judgment: false

duration: ~10min (this resumed session, Tasks 2-3 only; Task 1's original halt session on 2026-10-14 is recorded separately above and added 0 min of build/push work)
completed: 2026-10-25
status: complete
---

# Phase 04 Plan 02: CI Build and Release Pipeline (Public Push + macOS/Windows CI) Summary

**The project is now public on GitHub, and a three-job CI workflow (build-macos, build-windows, release) builds and smoke-checks both downloads on GitHub's own machines, proven green on a hand-started run that correctly skipped publishing.**

## Performance

- **Duration:** ~10 min for this resumed session (Tasks 2-3); Task 1's original "hold" halt (2026-10-14) added 0 min of build/push work, as designed
- **Started:** 2026-10-25T14:17:13Z (Task 2 commit) — resumed from a prior halt at Task 1, originally reached 2026-10-14
- **Completed:** 2026-10-25T14:27:08Z
- **Tasks:** 3 of 3 (Task 1 resolved via re-ask; Tasks 2 and 3 both executed and verified)
- **Files modified:** 1 (`.github/workflows/release.yml`, created)

## Accomplishments

- **Task 1 (publish decision) resolved:** The user was asked again, directly, after the 2026-10-14 "hold," and answered "Yes, publish now." This resumed execution proceeded on "publish" without re-asking the Task 1 checkpoint, per the orchestrator's explicit instruction.
- **First-ever push to the project's public GitHub repository:** `git push origin HEAD:main` sent ~230 previously-local commits (all of Phases 1-3's app work, the `.planning/` notes, and this phase's packaging files) to `github.com/BEtheLED/GDTFComparer`. `origin/main` is now identical to local `HEAD`.
- **`.github/workflows/release.yml` created and proven, in two commits (Task 2 then Task 3):**
  - `build-macos`: installs the project's dev extras (the pinned PyInstaller), builds `packaging/app.spec`, reports the binary's architecture via `lipo`, zips the `.app` with `ditto`, smoke-checks the zip, uploads it as the `macos-build` artifact.
  - `build-windows`: the same steps on `windows-latest` (pwsh shell), zipping with `Compress-Archive` into a `GDTF Comparer` top-level folder, uploaded as `windows-build`.
  - `release`: tag-only (`refs/tags/v*`), needs both build jobs, runs on `ubuntu-latest`, is the only job with `contents: write`, checks the tag against `pyproject.toml`'s version via a `TAG_NAME` environment variable, downloads both artifacts, and publishes them via a SHA-pinned `softprops/action-gh-release`.
- **Two hand-started CI runs, both green on the first attempt — no Windows-only fixes were needed to `packaging/app.spec` or `packaging/smoke_check.py`:**
  - Run `40201655549` (after Task 2's push): `build-macos` succeeded in 1m32s, including a passing smoke check.
  - Run `40202021705` (after Task 3's push): `build-macos` succeeded in 1m15s, `build-windows` succeeded in 1m54s (including the Windows main-window-title and PyInstaller-error-dialog `EnumWindows` checks Plan 04-01 wired in), and `release` correctly reported `skipped` (the ref was `refs/heads/main`, not a tag).
- **Both downloads independently re-verified on this Mac after download, not just trusted from CI's own exit code:**
  - macOS: `packaging/smoke_check.py --zip` on the downloaded `macos-build` zip printed `SMOKE PASS`; the extracted binary's `lipo -archs` reported `arm64`.
  - Windows: the downloaded `windows-build` zip's 325 entries were confirmed to include `GDTF Comparer/GDTF Comparer.exe` and an entry under `GDTF Comparer/_internal/`.

## Task Commits

1. **Task 1: Publish this project to its public GitHub page now?** — no commit (checkpoint:decision; originally answered "hold" on 2026-10-14 with no file changes; re-asked and answered "publish" on 2026-10-25, which this execution acted on)
2. **Task 2: End-to-end "a push to GitHub builds the Mac app on GitHub's own Mac, and the download it produces opens on this Mac"** — `7f50d56` (feat)
3. **Task 3: The same run now builds and checks the Windows app too, and a version tag would publish both downloads as one release** — `af09300` (feat)

**Plan metadata:** pending (this SUMMARY's commit)

## Files Created/Modified

- `.github/workflows/release.yml` — New: the repository's first CI workflow. "Build and release"; triggers on `v*` tag pushes and manual `workflow_dispatch`; workflow-default `permissions: contents: read`; `concurrency` group `release-${{ github.ref }}` with `cancel-in-progress: false`; jobs `build-macos`, `build-windows`, `release`.

## Decisions Made

- **Task 1, first answer (2026-10-14): "hold."** No files changed, nothing pushed. Recorded word-for-word in the prior version of this SUMMARY.
- **Task 1, final answer (2026-10-25): "publish."** The user was asked again directly and answered "Yes, publish now," explicitly superseding the earlier "hold." This execution treated Task 1 as resolved on that basis and proceeded directly to Tasks 2-3 without re-presenting the checkpoint, per the resuming orchestrator's explicit instruction.
- `git http.postBuffer` raised to 500 MB in this worktree's local git config to fix a push failure (see Deviations below) — a client-side setting change, not a change to any tracked file.
- Current GitHub Actions majors (`actions/checkout@v7`, `actions/setup-python@v7`, `actions/upload-artifact@v7`, `actions/download-artifact@v8`) re-confirmed live via `gh api .../releases/latest` immediately before writing the workflow, matching the plan's own flagged-assumption update from its original 2026-10-14 RESEARCH.md draft (which had cited older `@v4`/`@v5` majors).
- `softprops/action-gh-release` pinned to commit `efb35369e0ad2afab669f228072c1b0d510eae64` (tag `v3.0.3`) — independently re-resolved via `gh api` at execution time and found identical to the plan's pre-verified value.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] First-ever `git push` to origin failed with an HTTP 400 "unexpected disconnect" error; fixed by raising `http.postBuffer`**
- **Found during:** Task 2, first `git push origin HEAD:main` attempt (pushing ~230 previously-unpushed commits for the first time)
- **Issue:** `git push origin HEAD:main` failed twice in a row with `error: RPC failed; HTTP 400 curl 22 The requested URL returned error: 400` / `send-pack: unexpected disconnect while reading sideband packet` / `fatal: the remote end hung up unexpectedly`. `git ls-remote origin main` confirmed the remote ref was unchanged after each failed attempt — nothing partial was pushed. The repository itself is small (full `.git` ~7.9 MB; largest blob in history ~81 KB; 1634 loose objects totaling ~7.8 MB), ruling out a GitHub-side size limit; no proxy was configured in this environment.
- **Fix:** Ran `git config http.postBuffer 524288000` (500 MB, up from git's 1 MB default) in this worktree's local git config, then retried the identical `git push origin HEAD:main` command. It succeeded immediately with no further errors.
- **Files modified:** none (local git client configuration only, not a tracked repository file)
- **Verification:** `git ls-remote origin main` and `git rev-parse origin/main` both reported the pushed commit hash immediately after the successful push; `git rev-list --count origin/main..HEAD` reported `0`.
- **Committed in:** n/a (no file change; this was a local git-client config adjustment, not a commit)

---

**Total deviations:** 1 auto-fixed (1 blocking, environment-only)
**Impact on plan:** Necessary to complete the plan's first-ever push at all; no repository file was touched, no scope creep. The plan itself anticipated exactly this kind of blocking issue needing a fix without re-litigating the Task 1 decision.

## Issues Encountered

None beyond the push-buffer deviation documented above. No Windows-only build or smoke-check failures occurred — both CI runs were green on the first attempt, so no changes to `packaging/app.spec` or `packaging/smoke_check.py` were needed in this plan (unlike the local macOS Xcode/DEVELOPER_DIR workaround documented in Plan 04-01, which remains a local-machine-only concern and did not recur in CI, as that plan predicted).

## User Setup Required

None required during this execution. The `user_setup` step anticipated in this plan's frontmatter (`gh auth refresh -h github.com -s workflow`) was already satisfied before this execution began — `gh auth status` showed the `workflow` scope present (alongside `gist`, `read:org`, `repo`) at the start of this session, so no auth gate was hit.

## Next Phase Readiness

- **Unblocked:** Plan 04-04 (publish GitHub Release `v0.1.0`) can now proceed — the CI pipeline exists, is proven green end-to-end on a hand-started run, and the `release` job's tag-and-version-match gate is in place and verified not to fire on a non-tag ref.
- **Ready for Plan 04-04:** Pushing a tag `v0.1.0` (matching `pyproject.toml`'s current `version = "0.1.0"`) will trigger `build-macos` and `build-windows` again and, if both succeed, the `release` job will publish a GitHub Release named "GDTF Comparer v0.1.0" with `packaging/release-notes.md` as its body and both zips attached.
- **No blockers:** No Windows-only fixes were needed to `packaging/app.spec` or `packaging/smoke_check.py`, so Plan 04-01's local macOS build/smoke-check loop and `tests/test_smoke_check.py` remain unaffected and unexercised by this plan (not required — no changes were made to either file).
- **Public repository note for future plans:** The repository is now public at `github.com/BEtheLED/GDTFComparer`. Future plans/executors should bear this in mind when deciding what, if anything, should NOT be committed (though nothing in this plan introduced any new secret-handling surface — no repository secret is referenced anywhere in `.github/workflows/release.yml`).

## Self-Check: PASSED

- FOUND: `.github/workflows/release.yml`
- FOUND: `.planning/phases/04-standalone-packaging/04-02-SUMMARY.md` (this file)
- FOUND (commit ancestor of HEAD): `7f50d565af9129c813a64e1e6226a067f4bce863` (Task 2)
- FOUND (commit ancestor of HEAD): `af09300b2523d30a1279f646b94fefb30f2834d1` (Task 3)
- OK: `git rev-parse HEAD` equals `git rev-parse origin/main` (`af09300b2523d30a1279f646b94fefb30f2834d1`) — everything pushed, nothing force-pushed
- OK: CI run `40202021705` (`gh run view --json jobs`) reports `build-macos: success`, `build-windows: success`, `release: skipped`
- OK: Locally re-verified macOS smoke check (`SMOKE PASS`, `arm64`) and Windows zip structure (`GDTF Comparer/GDTF Comparer.exe`, `GDTF Comparer/_internal/`) independently of CI's own reported success

---
*Phase: 04-standalone-packaging*
*Completed: 2026-10-25*
