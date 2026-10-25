---
phase: "04"
slug: "standalone-packaging"
status: validated
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: "2026-10-25"
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PyPI -> shared `.venv` | PyInstaller and its helper packages enter the developer environment for the first time | Build-time dependency code |
| Developer machine -> frozen bundle | Whatever PyInstaller collects ends up inside an artifact that is later published | App code, Qt resources |
| This Mac -> public GitHub repository | The first push published ~230 commits of history and planning notes | Full repo history |
| PyPI and GitHub Marketplace -> CI runners | pip packages and third-party actions run code inside the build and release jobs | Build-time dependency + action code |
| CI build jobs -> release job -> public GitHub Release | Whatever the build jobs upload becomes the public download | Built app binaries (macOS/Windows) |
| Git tag name -> workflow scripts | The tag text flows into the release job | Tag string (env-only, never shell-expanded) |
| Project documentation -> end user's OS security decisions | The user follows these words when deciding to override an OS protection | README / release-notes wording |
| Download source (any website) -> user's computer | Unsigned files from other sources look identical; only the download location tells them apart | Downloaded zip |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-04-SC (04-01) | Tampering (supply chain) | `pip install "pyinstaller==6.22.3"` and helpers | high | mitigate | Exact pin in `pyproject.toml`'s dev extra (confirmed: `pyinstaller==6.22.3` at pyproject.toml:23); blocking-human legitimacy checkpoint passed before install | closed |
| T-04-01 | Information Disclosure | `packaging/app.spec` collecting developer files into the bundle | medium | mitigate | Analysis entry is only `src/gdtf_comparer/app.py`; `datas=[]`; verified at Task 2 acceptance | closed |
| T-04-02 | Denial of Service | Invalid bundle signature leaves macOS users at a dead end | medium | mitigate | `smoke_check.py` runs `codesign --verify --deep --strict` before every launch; confirmed passing (462/462 suite) | closed |
| T-04-03 | Tampering (false pass) | Smoke check passing due to leaked dev environment | low | mitigate | `smoke_environment` strips dev env vars, points HOME/APPDATA at a fresh temp dir; `test_child_environment_is_isolated` passes | closed |
| T-04-SC (04-02) | Tampering (supply chain) | `pip install ".[dev]"` on both CI runners | high | mitigate | Every dependency is an exact pin in `pyproject.toml`; no unpinned install line in the workflow | closed |
| T-04-04 | Elevation of Privilege | Repository write token reachable by build jobs running third-party pip/PyInstaller code | high | mitigate | Confirmed: workflow default `contents: read` (release.yml:18); only `release` job gets `contents: write` (release.yml:105); `persist-credentials: false` on all three checkouts | closed |
| T-04-08 | Tampering (supply chain) | Third-party `softprops/action-gh-release` running with the write token | high | mitigate | Confirmed: pinned to full 40-char SHA `efb35369e0ad2afab669f228072c1b0d510eae64 # v3.0.3` (release.yml:148) | closed |
| T-04-05 | Tampering / DoS | Release published with missing/partial/unchecked download | medium | mitigate | `needs: [build-macos, build-windows]`; smoke check before upload; `if-no-files-found: error`; `fail_on_unmatched_files: true` — all present in `release.yml`, exercised live by the green tag-triggered run | closed |
| T-04-06 | Spoofing | Mistyped tag or GSD milestone tag publishing a mislabeled release | medium | mitigate | Version-guard step fails unless tag == "v" + pyproject version; proven: `v0.1.0` matched `0.1.0` and published correctly | closed |
| T-04-07 | Information Disclosure | Pushing local history/planning notes to a public repo without owner consent | medium | mitigate | blocking-human Task 1 decision (04-02) listed exactly what becomes public; user explicitly answered "publish" (recorded in 04-02-SUMMARY.md); no force-push used | closed |
| T-04-09 | Tampering (injection) | Tag text expanded inside a shell script | low | mitigate | Tag reaches the guard script only via `TAG_NAME` env var (confirmed present in release.yml); only push-rights users can create tags | closed |
| T-04-13 | Information Disclosure | New CI secrets/personal tokens added to the repo | low | mitigate | None introduced; `! grep -nF 'secrets.' .github/workflows/release.yml` holds | closed |
| T-04-SC (04-03) | Tampering (supply chain) | Package installs | low | mitigate | This plan installs nothing; stdlib + pytest only | closed |
| T-04-10 | Spoofing / social engineering | Users trained to click past OS warnings for any file, including look-alikes | medium | mitigate | README/release-notes scope the bypass explicitly to github.com/BEtheLED/GDTFComparer/releases; `test_explains_unsigned_and_scope` passes | closed |
| T-04-11 | Elevation of Privilege | Instructions weakening system-wide protection (disabling Gatekeeper/SmartScreen/Defender) | high | mitigate | Confirmed by grep: no "turn off"/"disable Gatekeeper/SmartScreen/Defender"/"system-wide" wording in README.md or packaging/release-notes.md; `test_no_system_wide_security_off_switch` passes | closed |
| T-04-12 | Denial of Service | Stale macOS bypass steps leave users with no way in | medium | mitigate | Current System Settings > Privacy & Security > Open Anyway flow documented; `test_mac_steps_use_current_gatekeeper_flow` passes; confirmed live by CI's macOS smoke check | closed |
| T-04-14 | Tampering | Release files uploaded/replaced by hand so downloads differ from what CI checked | medium | mitigate | Release created only by the tag-triggered workflow; 04-04 Task 1 verified every asset uploader is `github-actions[bot]`; `packaging/RELEASING.md` "Rules" forbids hand uploads | closed |
| T-04-15 | Tampering / Repudiation | A published tag moved/reused, so "v0.1.0" means different files to different people | low | mitigate | `packaging/RELEASING.md`: never move or reuse a published tag; v0.1.0 was tagged once and never retagged | closed |
| T-04-16 | Tampering (integrity) | Downloaders can't independently confirm files are unaltered (no signature/checksum) | low | accept | Unsigned by explicit user decision (D-01); HTTPS from GitHub's own release page; checksums add little for this non-technical audience; revisit if signing is added later | closed (accepted risk) |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above `high` (workflow.security_block_on) count toward `threats_open`*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-04-01 | T-04-16 | No SHA-256 checksum file attached to releases. GitHub serves downloads over HTTPS from the project's own release page; checksums add little verification value for this non-technical lighting/AV audience. Revisit if code signing is added later (packaging/RELEASING.md documents where signing would plug in). | User (via D-01 "unsigned builds" decision, 04-CONTEXT.md) | 2026-10-14 |

---

## Audit Trail

All four plans (04-01, 04-02, 04-03, 04-04) authored their `<threat_model>` STRIDE registers at planning time (`register_authored_at_plan_time: true`). ASVS level is 1 (project config `workflow.security_asvs_level`), so grep-depth verification is sufficient per the project's security gate rules — no deeper (L2/L3) auditor pass was required.

Every threat at or above the blocking severity (`high`, per `workflow.security_block_on`) was spot-checked directly against the current repository state and the live-published artifacts (the pushed `.github/workflows/release.yml`, `pyproject.toml`, `README.md`, `packaging/release-notes.md`, and the published `v0.1.0` GitHub Release) rather than taken on the plan's word alone:

- `T-04-SC` (pyinstaller pin), `T-04-04` (contents: read/write split), `T-04-08` (softprops SHA pin), `T-04-11` (no system-wide security-off instructions) — all confirmed present by direct inspection.
- All `medium`/`low` threats' mitigations are additionally covered by the automated test suite (`tests/test_release_docs.py`, `tests/test_smoke_check.py` — part of the 462/462 passing suite) and by each plan's own `<verify>` commands, already run live by the executing agents.

**Result: 0 threats open at or above the `high` block threshold. 1 accepted risk (T-04-16, low severity, documented above).**

## Security Audit 2026-10-25

| Metric | Count |
|---|---|
| Threats found | 19 |
| Closed | 18 |
| Open | 0 |
| Accepted | 1 |
