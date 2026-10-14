# Phase 4: Standalone Packaging - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-10-14
**Phase:** 4-standalone-packaging
**Areas discussed:** Signing & security warnings, Build automation vs manual, Distribution channel, Platform priority / scope

---

## Signing & Security Warnings

### macOS

| Option | Description | Selected |
|--------|-------------|----------|
| Pay for Apple Developer ($99/yr) | Completely normal double-click launch, no warnings, no workaround needed. Recurring cost. | |
| Ship unsigned + instructions | Free. Gatekeeper "unidentified developer" block on first launch; right-click → Open bypasses it permanently. PKG-03 explicitly allows this path. | ✓ |

**User's choice:** Ship unsigned + instructions
**Notes:** None

### Windows

| Option | Description | Selected |
|--------|-------------|----------|
| Pay for a code-signing cert | Standard (OV) certs ~$75-400/yr still show some warning until download reputation builds; EV certs (~$300-600/yr) avoid SmartScreen immediately but need extra identity verification. Recurring cost either way. | |
| Ship unsigned + instructions | Free. "Windows protected your PC" → More info → Run anyway. One extra click, no cost. | ✓ |

**User's choice:** Ship unsigned + instructions
**Notes:** None

---

## Build Automation vs Manual

| Option | Description | Selected |
|--------|-------------|----------|
| GitHub Actions CI | One macOS runner + one Windows runner, fully repeatable for future releases without needing to personally own both a Mac and a Windows PC. | ✓ |
| Manual builds | Build directly on whatever machine(s) available. Simpler initial setup, but needs access to both OSes and manual work every release. | |

**User's choice:** GitHub Actions CI
**Notes:** None

---

## Distribution Channel

| Option | Description | Selected |
|--------|-------------|----------|
| GitHub Releases | Free, built into the existing repo. Pairs naturally with the CI pipeline. | ✓ |
| Something else | A personal website, shared drive link, or community forum/Discord. | |

**User's choice:** GitHub Releases
**Notes:** None

---

## Platform Priority / Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Ship together | Both builds land in the same release/tag. Matches the roadmap's success criteria treating both as equally required. | ✓ |
| One platform first | Sequence one OS's build before the other within the phase. | |

**User's choice:** Ship together
**Notes:** None

---

## Claude's Discretion

- Exact wording/formatting of the Gatekeeper/SmartScreen bypass instructions (README section, in-app message, or a text file alongside the build).
- GitHub Actions workflow structure (triggers, job naming, artifact upload mechanics, caching strategy).
- PyInstaller spec file details (`--windowed`, `--add-data` for qt-material assets, exact `--name` string).
- Versioning/tagging scheme for releases.

## Deferred Ideas

- **Project license change (GPLv3 → MIT):** The user raised this mid-discussion after noticing the repo's actual `LICENSE` file (GPLv3) contradicts prior decisions that assumed an open/non-GPL license (PySide6-over-PyQt6, MVR-xchange reimplemented from spec rather than ported GPLv3 code). User confirmed they want MIT. This is a repo-wide, project-level change outside Phase 4's packaging scope — flagged for a separate follow-up task (e.g., `/gsd-quick`), not folded into this phase's plan.
