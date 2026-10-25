---
phase: 04-standalone-packaging
plan: 04
subsystem: infra
tags: [github-actions, ci, release, github-releases, pyinstaller]

# Dependency graph
requires:
  - phase: 04-standalone-packaging (plan 02)
    provides: ".github/workflows/release.yml (build-macos, build-windows, release jobs), proven green on a hand-started run"
  - phase: 04-standalone-packaging (plan 03)
    provides: "README.md and packaging/release-notes.md first-launch instructions; tests/test_release_docs.py"
provides:
  - "packaging/RELEASING.md: the maintainer release recipe (make a release, test without releasing, recovery rule, rules, docs upkeep, future signing)"
  - "Annotated git tag v0.1.0 on origin/main"
  - "Public GitHub Release 'GDTF Comparer v0.1.0' at https://github.com/BEtheLED/GDTFComparer/releases/tag/v0.1.0 with GDTF-Comparer-macos.zip and GDTF-Comparer-windows.zip, both uploaded only by github-actions[bot]"
  - "Both published downloads independently re-verified on this Mac (macOS: smoke_check.py --zip PASS + arm64; Windows: zip layout has GDTF Comparer.exe and _internal/)"
affects: ["Phase 4 end-of-phase UAT (two human checks on real Mac/Windows hardware queued below)"]

# Actuals (#2632)
actuals:
  tokens: 1069
  tasks: 2
  commits: 1
  plan_head_before: 321b3007660291f46d9b3664b5dfcc52ac850f5c
  plan_head_after: df59b22a1197b401832ed91447ad2f28a241c9b9

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Release recipe documented as a standalone maintainer doc (packaging/RELEASING.md) separate from README's end-user instructions, so the two audiences (maintainer vs. downloader) never share one doc"
    - "Tag-triggered publish verified end-to-end on the very first real tag push: build-macos, build-windows, release all green with no recovery-path exercise needed"

key-files:
  created:
    - packaging/RELEASING.md
  modified: []

key-decisions:
  - "Followed the orchestrator's explicit instruction not to re-ask the publish decision: the user had already answered 'publish' in Plan 04-02 Task 1 and, when asked again directly before this plan, explicitly said 'Yes, publish now,' including this release. This plan proceeded straight to writing the recipe and publishing."
  - "Versioning: first release is v0.1.0, matching pyproject.toml's existing unbumped version, per the plan's own discretion note."
  - "macOS architecture check used the known local-machine DEVELOPER_DIR=/Library/Developer/CommandLineTools workaround (documented in STATE.md from Plan 04-01: this Mac's Xcode 16.0 vs macOS 26.6.2 mismatch breaks lipo without it) — an environment-only adjustment, not a repository change, and not expected to recur in CI (confirmed again here: CI's own lipo step in build-macos succeeded without any such workaround)."

patterns-established:
  - "packaging/RELEASING.md's recovery rule (delete+recreate tag only before a release exists; never move/reuse a tag after one exists) was written but not exercised — both the Task 1 precondition checks and the live tag push succeeded on the first attempt, so no recovery path was needed this time."

requirements-completed: [PKG-01, PKG-02, PKG-03]

coverage:
  - id: D1
    description: "packaging/RELEASING.md documents the next-release recipe: bump version, commit, push, tag v<version>, push tag; testing a build without releasing via Run workflow; the tag-recovery rule for a failed pre-release run; never moving/reusing a published tag; hand-upload and tag/version-match rules; keeping README.md and release-notes.md in sync via tests/test_release_docs.py; where future code signing would slot in"
    verification:
      - kind: other
        ref: "grep -n 'git push origin v' / 'Run workflow' / 'never move or reuse' / 'tests/test_release_docs.py' / 'Developer ID' packaging/RELEASING.md — all five matched"
        status: pass
    human_judgment: false
  - id: D2
    description: "Following the written recipe, pushing annotated tag v0.1.0 triggered the 'Build and release' workflow (run 40202786583), which built and smoke-checked both the macOS and Windows apps and published GitHub Release 'GDTF Comparer v0.1.0' with exactly the two expected zips, all uploaded by github-actions[bot], description containing the first-launch steps, tag on origin/main with pyproject.toml version 0.1.0 and RELEASING.md present"
    requirement: "PKG-01, PKG-02, PKG-03"
    verification:
      - kind: integration
        ref: "gh release view v0.1.0 --json tagName,name,isDraft,isPrerelease,assets,body (Task 1 verify command 1) — passed, printed 'release ok'"
        status: pass
      - kind: integration
        ref: "git merge-base --is-ancestor; git show v0.1.0:pyproject.toml; git cat-file -e v0.1.0:packaging/RELEASING.md; gh api .../releases/tags/v0.1.0 --jq uploader.login (Task 1 verify command 2, run as separated sub-checks) — all passed"
        status: pass
    human_judgment: false
  - id: D3
    description: "The exact files on the public release page were fetched back (not trusted from CI alone) and independently re-checked on this Mac: macOS zip passes packaging/smoke_check.py --zip (SMOKE PASS) and is arm64; Windows zip contains 'GDTF Comparer/GDTF Comparer.exe' and a 'GDTF Comparer/_internal/' entry"
    requirement: "PKG-01, PKG-02"
    verification:
      - kind: integration
        ref: "gh release download v0.1.0; python packaging/smoke_check.py --zip GDTF-Comparer-macos.zip -> SMOKE PASS; lipo -archs on extracted binary -> arm64; python3 zipfile assertion on GDTF-Comparer-windows.zip -> 'published windows zip ok'"
        status: pass
    human_judgment: false
  - id: D4
    description: "README.md and packaging/release-notes.md name exactly the two files the published release carries, and tests/test_release_docs.py passes"
    verification:
      - kind: integration
        ref: "grep -qF GDTF-Comparer-macos.zip / GDTF-Comparer-windows.zip in both README.md and packaging/release-notes.md -> both matched; python -m pytest tests/test_release_docs.py -q -> 19 passed"
        status: pass
    human_judgment: false
  - id: D5
    description: "A person follows README.md's 'On a Mac' steps exactly, on a copy downloaded via a web browser, through Gatekeeper's first-launch bypass, and runs a real comparison; second launch has no warning (PKG-01, PKG-03 real-user backstop)"
    requirement: "PKG-01, PKG-03"
    verification: []
    human_judgment: true
    rationale: "Gatekeeper only blocks a copy a browser marked as downloaded from the internet; its dialogs and System Settings screens cannot be driven by a script, and Apple's exact wording can change between macOS versions without notice. This plan explicitly queues this check for end-of-phase UAT rather than performing it — see 'Pending Human Checks' below."
  - id: D6
    description: "A person follows README.md's 'On Windows' steps exactly, on a copy downloaded via a web browser, through SmartScreen's first-launch bypass, and runs a real comparison; second launch has no warning; Defender does not remove the file (PKG-02, PKG-03 real-user backstop)"
    requirement: "PKG-02, PKG-03"
    verification: []
    human_judgment: true
    rationale: "SmartScreen only checks a file a browser downloaded on a real Windows PC; GitHub's build machines never show these screens and this Mac cannot run Windows. This plan explicitly queues this check for end-of-phase UAT rather than performing it — see 'Pending Human Checks' below."

duration: ~14min
completed: 2026-10-25
status: complete
---

# Phase 04 Plan 04: Publish GitHub Release v0.1.0 Summary

**Wrote the release recipe (packaging/RELEASING.md), then followed it to tag and publish GDTF Comparer's first public GitHub Release, v0.1.0 — both the macOS and Windows downloads built and smoke-checked by CI, re-verified here after fetching them back from the live release page.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-10-25T14:25:00Z (approx.)
- **Completed:** 2026-10-25T14:39:00Z
- **Tasks:** 2 of 2
- **Files modified:** 1 (`packaging/RELEASING.md`, created)

## Accomplishments

- **packaging/RELEASING.md written:** the maintainer recipe for every future release — bump `pyproject.toml`'s version, commit, push, tag `v<version>`, push the tag; testing a build without releasing via "Run workflow"; the recovery rule for a failed pre-release tag run (fix, recreate the tag — never after a release exists); rules against hand uploads and for the tag/version match; keeping README.md and `packaging/release-notes.md` in sync via `tests/test_release_docs.py`; and where future code signing (D-01, reversible) would slot into the existing pipeline (D-02) without changing its shape.
- **Pre-publish checks all passed before tagging:** `pyproject.toml` version was exactly `0.1.0`; no `v0.1.0` tag existed on origin; no `v0.1.0` release existed; the working tree had no uncommitted changes to tracked files.
- **First-ever public release published, end to end, on the first attempt:** `packaging/RELEASING.md` committed (`df59b22`), pushed to `origin/main`, tagged `v0.1.0` (annotated: `git cat-file -t v0.1.0` reports `tag`), tag pushed. CI run `40202786583` (triggered by the tag push) ran `build-macos` (1m27s, success), `build-windows` (2m22s, success), and `release` (23s, success) — no recovery path was needed.
- **GitHub Release "GDTF Comparer v0.1.0" is public** at https://github.com/BEtheLED/GDTFComparer/releases/tag/v0.1.0 — not a draft, not a prerelease, carrying exactly `GDTF-Comparer-macos.zip` and `GDTF-Comparer-windows.zip`, both uploaded only by `github-actions[bot]` (independently confirmed via `gh api .../releases/tags/v0.1.0`), with a description containing the documented first-launch steps ("Open Anyway", "Run anyway").
- **The published tag/commit were independently checked, not just trusted from the workflow's own success:** the tag is an ancestor of `origin/main`; the tagged commit's `pyproject.toml` reads `version = "0.1.0"`; `packaging/RELEASING.md` exists in the tagged commit.
- **Both published downloads fetched back from the live release (not a local build) and re-checked here:** the macOS zip passes `packaging/smoke_check.py --zip` (`SMOKE PASS`) and is `arm64` (confirmed via `lipo -archs`, using this Mac's known `DEVELOPER_DIR=/Library/Developer/CommandLineTools` local workaround); the Windows zip's layout holds `GDTF Comparer/GDTF Comparer.exe` and a `GDTF Comparer/_internal/` entry.
- **Docs confirmed to name the right files:** both `README.md` and `packaging/release-notes.md` name both `GDTF-Comparer-macos.zip` and `GDTF-Comparer-windows.zip`; `tests/test_release_docs.py` passes (19 tests).
- **Two human checks explicitly queued, not performed, for end-of-phase UAT** — see "Pending Human Checks" below.

## Task Commits

1. **Task 1: End-to-end "write down the release recipe, follow it, and GitHub Release v0.1.0 appears with the Mac and Windows downloads and the first-launch steps"** — `df59b22` (docs) — writes `packaging/RELEASING.md`; publishing the tag/release itself is a git/CI action, not a repository file change, so it has no separate commit.
2. **Task 2: The files people actually download open: fetched back and checked here, then walked through by a person on a real Mac and a real Windows PC** — no commit (verification-only task; plan's own `<files>` states "No repository file changes").

**Plan metadata:** This SUMMARY's commit (pending).

## Files Created/Modified

- `packaging/RELEASING.md` — New: the maintainer release recipe (make a new release, test without releasing, recovery rule, rules, docs upkeep, future signing).

## Decisions Made

- The publish decision was not re-asked. The orchestrator's objective explicitly recorded that the user had already answered "publish" in Plan 04-02 Task 1, and, when asked again directly immediately before this plan, explicitly said "Yes, publish now," including this release. This plan proceeded straight to writing the recipe and publishing.
- First release version is `v0.1.0`, matching `pyproject.toml`'s existing unbumped `version = "0.1.0"`, per the plan's own "Claude's discretion" note on versioning.
- The macOS architecture check (`lipo -archs`) used this Mac's known local-only workaround, `DEVELOPER_DIR=/Library/Developer/CommandLineTools`, first documented in STATE.md during Plan 04-01 (this machine's Xcode 16.0 vs. macOS 26.6.2 mismatch breaks `lipo` without it). This is an environment variable set for one command, not a repository change, and did not recur in CI — the workflow's own `lipo -archs` step in `build-macos` succeeded with no such workaround needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `lipo -archs` failed on this Mac without a `DEVELOPER_DIR` override**
- **Found during:** Task 2, step 1 (verifying the downloaded macOS zip's architecture)
- **Issue:** Running `lipo -archs` on the extracted macOS binary failed with exit code 72 and an Xcode/`xcodebuild` loader error (`Error loading required libraries ... Symbol not found: _XPCTypeBool`), because this Mac's default `xcode-select` path resolves to a mismatched Xcode/macOS combination (documented previously in STATE.md from Plan 04-01).
- **Fix:** Re-ran the identical command with `DEVELOPER_DIR=/Library/Developer/CommandLineTools` set for that one invocation, which succeeded and reported `arm64`.
- **Files modified:** None — environment variable only, no repository file touched.
- **Verification:** `DEVELOPER_DIR=/Library/Developer/CommandLineTools lipo -archs ".../GDTF Comparer.app/Contents/MacOS/GDTF Comparer"` printed `arm64`.
- **Committed in:** n/a (no file change; local shell environment adjustment only, matching the precedent already recorded from Plan 04-01).

---

**Total deviations:** 1 auto-fixed (1 blocking, environment-only, with direct precedent already documented in STATE.md)
**Impact on plan:** No repository file was touched beyond the plan's own `packaging/RELEASING.md`; no scope creep. This exact workaround was already anticipated as a known local-machine quirk, not expected to recur in CI (and indeed did not — CI's own `lipo -archs` step succeeded unassisted).

## Issues Encountered

None beyond the `lipo`/`DEVELOPER_DIR` deviation documented above. The tag push, CI run, and release publish all succeeded on the first attempt — `packaging/RELEASING.md`'s "If something goes wrong" recovery rule was written but never exercised.

## User Setup Required

None required during this execution. `gh auth status` already had the scopes needed from the prior plan's setup.

## Pending Human Checks (queued for end-of-phase UAT — NOT performed by this execution)

Per the plan's explicit instruction, the two `<human-check>` blocks in Task 2's verify section were deliberately left un-performed. They require a non-technical human on real Mac and Windows hardware, not an automated agent. Both are recorded here as open items for the end-of-phase review:

1. **Mac human check (PKG-01, PKG-03):** Download `GDTF-Comparer-macos.zip` with a web browser from https://github.com/BEtheLED/GDTFComparer/releases/latest, follow README.md's "On a Mac" steps exactly (unzip, move to Applications, first launch, System Settings → Privacy & Security → Open Anyway), run a real comparison between two fixture files, then confirm the second launch shows no warning. Record exactly what each screen said, especially any wording that differs from README.md.
2. **Windows human check (PKG-02, PKG-03):** Download `GDTF-Comparer-windows.zip` with a web browser on a real Windows 10/11 PC, follow README.md's "On Windows" steps exactly (keep if warned, Extract All, first launch, "Windows protected your PC" → More info → Run anyway), run a real comparison, then confirm the second launch shows no warning and Microsoft Defender does not remove the file.

**Release URL for both checks:** https://github.com/BEtheLED/GDTFComparer/releases/tag/v0.1.0

If either check finds wording that differs from the documented steps, the fix belongs in README.md and `packaging/release-notes.md` plus a new patch release (via `packaging/RELEASING.md`) — the published v0.1.0 release itself must never be edited in place.

## Next Phase Readiness

- **Public release live:** Anyone can now download and run GDTF Comparer for macOS or Windows from https://github.com/BEtheLED/GDTFComparer/releases/latest with no Python install, satisfying the automated/CI-provable portions of PKG-01, PKG-02, and PKG-03.
- **Phase 4 is not yet fully verified end-to-end:** per the plan's own `<verification>` section, "The phase is verified only when both [human checks] pass, or the user decides otherwise in UAT." Both human checks above remain open.
- **Repeatable release recipe in place:** `packaging/RELEASING.md` means the next release (a bug-fix patch, a new feature) follows a documented, already-proven-working path — bump version, commit, push, tag, push tag, watch CI, confirm the Releases page.
- **No blockers for UAT:** The release, both downloads, and the docs are all in a verified-correct state; the only remaining work is the two queued human checks.

## Self-Check: PASSED

- FOUND: `packaging/RELEASING.md`
- FOUND: `.planning/phases/04-standalone-packaging/04-04-SUMMARY.md` (this file)
- FOUND (commit ancestor of HEAD): `df59b22a1197b401832ed91447ad2f28a241c9b9` (Task 1)
- OK: `gh release view v0.1.0` reports a published, non-draft, non-prerelease release with exactly the two expected assets, all uploaded by `github-actions[bot]`
- OK: tag `v0.1.0` is an annotated tag (`git cat-file -t v0.1.0` → `tag`) and an ancestor of `origin/main`
- OK: downloaded macOS zip passes `smoke_check.py --zip` (`SMOKE PASS`) and is `arm64`; downloaded Windows zip contains `GDTF Comparer/GDTF Comparer.exe` and a `GDTF Comparer/_internal/` entry
- OK: `tests/test_release_docs.py` passes (19 passed)

---
*Phase: 04-standalone-packaging*
*Completed: 2026-10-25*
