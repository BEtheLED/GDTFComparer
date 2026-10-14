# Phase 4: Standalone Packaging - Research

**Researched:** 2026-10-14
**Domain:** PyInstaller packaging of a PySide6 + qt-material desktop app for macOS and Windows; GitHub Actions CI build/release; macOS Gatekeeper and Windows SmartScreen unsigned-app bypass UX
**Confidence:** MEDIUM-HIGH (PyInstaller/qt-material mechanics verified directly against installed package source and official docs; Gatekeeper/SmartScreen current-UI claims cross-checked across multiple independent sources but not reproduced on a physical test machine this session)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**D-01 (Signing & Security Warnings):** Ship both the macOS and Windows builds unsigned — no Apple Developer Program enrollment ($99/yr) and no Windows code-signing certificate purchase. Instead, ship clear user-facing instructions for the one-time bypass on each OS (macOS: right-click the app → Open; Windows: "Windows protected your PC" → More info → Run anyway). This satisfies PKG-03's "signed OR otherwise configured to avoid being blocked" wording via the "otherwise configured" path. — Reversibility: reversible.

> **Research correction to the wording above (not to the decision itself):** macOS Sequoia (15, Sept 2024) and every macOS release since removed the right-click/Control-click → Open Gatekeeper override. The decision to ship unsigned + bypass instructions stands (D-01's substance is unchanged); only the *exact steps text* needs correcting in the actual bypass instructions this phase ships — see Pitfall/Finding below. "Exact wording of the bypass instructions" is explicitly Claude's Discretion per CONTEXT.md, so this correction is applied within that discretion, not a re-litigation of D-01.

**D-02 (Build Process):** Build via GitHub Actions CI — one job on a `macos-latest` runner, one job on a `windows-latest` runner — rather than manual local builds, since PyInstaller cannot cross-compile. — Reversibility: costly.

**D-03 (Distribution Channel):** Distribute via GitHub Releases — a tagged release attaches both the macOS and Windows build artifacts. — Reversibility: reversible.

**D-04 (Platform Scope):** macOS and Windows ship together in one release (not staggered). — Reversibility: reversible.

### Claude's Discretion
- Exact wording/formatting of the user-facing bypass instructions for Gatekeeper and SmartScreen (README section, in-app message, or a text file alongside the build — Claude's call).
- GitHub Actions workflow structure (triggers, job naming, artifact upload mechanics, caching strategy).
- PyInstaller spec file details (`--windowed`, `--add-data` for qt-material theme/icon assets per `.planning/research/STACK.md`, exact `--name` string).
- Versioning/tagging scheme for releases (e.g., whether to bump `pyproject.toml`'s `version` field automatically or manually per release).

### Deferred Ideas (OUT OF SCOPE)
- **Project license change (GPLv3 → MIT):** Raised during discussion but is a repo-wide, project-level decision, not part of Phase 4's packaging scope. To be handled as its own follow-up task (e.g., `/gsd-quick`).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-01 | User can download and run a standalone macOS build with no separate Python install | PyInstaller `--onedir --windowed` spec (Code Examples §1), macOS CI job (Code Examples §3), clean-machine verification gate (Pitfalls §P1, inherited from PITFALLS.md) |
| PKG-02 | User can download and run a standalone Windows build with no separate Python install | Same PyInstaller spec targeted at `windows-latest` (Code Examples §1/§3), Qt platform-plugin pitfall fix (Pitfalls §P4) |
| PKG-03 | Standalone builds are signed/notarized OR otherwise configured to avoid being blocked by Gatekeeper/SmartScreen on first launch | Corrected Gatekeeper bypass steps (Pitfalls §P2/Common Pitfalls), SmartScreen click-through steps (Common Pitfalls §Windows SmartScreen) |
</phase_requirements>

## Summary

This phase has one real technical unknown and one dangerous assumption already baked into the phase's own context file. The real unknown is mechanical: how to produce a correct PyInstaller build of a PySide6 + qt-material app that targets the existing `gdtf-comparer = "gdtf_comparer.app:main"` entry point, from a GitHub Actions matrix, and attach the result to a GitHub Release. That part is well-trodden — PyInstaller 6.22.3 has mature built-in PySide6 support, and **a verified, in-repo discovery changes the plan materially: `qt_material` ships its own PyInstaller hook and self-registers it via the standard `pyinstaller40` entry-point mechanism** (confirmed by reading `qt_material-2.17.dist-info/entry_points.txt` and the hook file itself, both already installed in this project's `.venv`). That means **no manual `--add-data` flags are needed for qt-material's theme/font/resource files** — PyInstaller auto-discovers and bundles them the moment `qt-material` is `pip install`-ed into the build environment. This directly corrects an assumption recorded in 04-CONTEXT.md's "Integration Points" section (which assumed qt-material "won't be auto-bundled").

The dangerous assumption is in D-01's bypass-instructions wording itself: "macOS: right-click the app → Open" **no longer works** on macOS Sequoia (15, released September 2024) or any later macOS version — Apple removed that Gatekeeper override. The correct 2026 flow requires the user to attempt the launch (it gets blocked), then go to **System Settings → Privacy & Security → scroll down → Open Anyway → re-attempt → Open → authenticate**. This is corrected within Claude's Discretion over the exact wording (the underlying D-01 decision — ship unsigned, document a bypass — is unaffected), but getting this wrong in the shipped instructions means real non-technical users (lighting/AV professionals, per PROJECT.md) will be stuck with no working path to open the app at all, which directly contradicts this phase's success criteria.

**Primary recommendation:** Use a single cross-platform `.spec` file (not raw CLI flags) invoked identically by both CI jobs, letting PyInstaller's PySide6 built-in hooks and qt-material's self-registered hook do the Qt/theme bundling automatically; ship `--onedir` output (not `--onefile`) per the existing PITFALLS.md guidance (clean-machine reliability + lower AV false-positive rate); zip the `--onedir` output per OS before uploading as a release asset; trigger the workflow on `v*` tag pushes using `softprops/action-gh-release@v2`; and replace "right-click → Open" in the bypass instructions with the corrected System-Settings flow (with `xattr -cr` as a terminal-savvy alternative).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Freezing the Python app into a standalone binary | Build/CI (GitHub Actions runner) | — | PyInstaller must run on the target OS itself (no cross-compile); this is a build-time concern, not an app-runtime concern |
| Bundling GUI framework assets (Qt plugins, qt-material themes/fonts) | Build/CI (PyInstaller hook resolution) | — | Resolved at freeze time via PyInstaller's hook-discovery mechanism, not at app runtime |
| Release artifact storage/distribution | GitHub Releases (hosted static storage) | — | No app-side or server-side component; purely a CI → GitHub Releases API hand-off |
| OS security gate (Gatekeeper/SmartScreen) bypass | OS / End-user action | Documentation (README/release notes) | These are OS-level gates outside the app's control; the only lever this phase has is user-facing instructions, not code |
| Versioning/release tagging | Build/CI (git tag → workflow trigger) | — | Git tag is the trigger and the version source of truth; no app code reads or needs this at runtime |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyInstaller | 6.22.3 | Freezes the `gdtf-comparer` entry point into a standalone macOS `.app` / Windows `.exe` with no separate Python install | Already the locked tool choice per `.planning/research/STACK.md`; verified current via `pip index versions pyinstaller` → `6.22.3` (latest, published 2026-09-12) [VERIFIED: pip index versions pyinstaller, 2026-10-14] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `softprops/action-gh-release` | `@v2` (GitHub Action, not a PyPI package) | Attaches built macOS/Windows artifacts to a GitHub Release from CI | Use in the release job after both build jobs complete; simpler than scripting `gh release create`/`upload` by hand across two OS runners [CITED: github.com/softprops/action-gh-release] |
| `actions/upload-artifact` / `actions/download-artifact` | `@v4` | Passes build output between the per-OS build jobs and a single release job | Standard GitHub Actions pattern for matrix-build → single-release fan-in [CITED: githubusercontent multi-OS PyInstaller tutorials] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `softprops/action-gh-release` | `gh release create` / `gh release upload` via the GitHub CLI directly in a shell step | More manual scripting (upload URL plumbing across two runner OSes), no real benefit for this project's single-maintainer scale; `softprops/action-gh-release` is simpler and still widely maintained |
| Two explicit named jobs (`build-macos`, `build-windows`) | A `strategy.matrix: os: [macos-latest, windows-latest]` single job | Matrix is more compact but makes OS-specific PyInstaller invocation differences (zip vs exe output, path separators in `--add-data` if any manual ones are added) harder to read at a glance; either works — Claude's Discretion per CONTEXT.md. This research recommends **explicit named jobs** for readability given there are only two platforms and the per-OS steps genuinely differ (zipping a `.app` bundle vs. shipping a bare `.exe`). |

**Installation:**
```bash
pip install pyinstaller==6.22.3
```
Add to `pyproject.toml`'s `[project.optional-dependencies] dev` list alongside the existing `pytest`/`pytest-qt` entries (no `[project.dependencies]` change — PyInstaller is a build-time tool, not a runtime dependency of the shipped app).

**Version verification:** `pip index versions pyinstaller` → `6.22.3` is current (latest), confirming STACK.md's pin is still accurate as of 2026-10-14. [VERIFIED: pip index versions pyinstaller — ran this session]

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pyinstaller | PyPI | published 2026-09-12 (this version); project itself is 10+ years old, industry-standard | unknown (tool returned null) | pyinstaller.org (project homepage; actual source at github.com/pyinstaller/pyinstaller) | SUS (reason: `unknown-downloads`) | Flagged by the automated check only because download-count telemetry was unavailable to the tool, not because of any actual legitimacy concern — PyInstaller is long-established, already named and justified in `.planning/research/STACK.md`, and already installed/imported by this project's own `.venv` tooling. **Still, per protocol, the planner must add a `checkpoint:human-verify` task before the `pip install pyinstaller==6.22.3` step**, even though this researcher's own assessment is that the package is legitimate. |
| qt-material | PyPI | published 2025-04-21 | unknown (tool returned null) | github.com/dunderlab/qt-material | SUS (reason: `unknown-downloads`) | Already an existing runtime dependency in `pyproject.toml` (pinned `qt-material==2.17`, in active use by `src/gdtf_comparer/gui/theme.py`) — not newly introduced by this phase. No new install action needed in this phase's plan; included here only because this phase's packaging work directly depends on its bundling behavior. No checkpoint needed (not a new install this phase). |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** `pyinstaller` — planner must add a `checkpoint:human-verify` task before the install step, per protocol, despite the SUS verdict resting solely on an availability gap in the legitimacy tool's download-count signal rather than any actual red flag in the package's history, maintainer, or source repo.

## Architecture Patterns

### System Architecture Diagram

```
 git push v1.0.0 tag
        |
        v
 GitHub Actions workflow triggers (on: push: tags: 'v*')
        |
        +------------------------------+
        |                              |
        v                              v
 [build-macos job]              [build-windows job]
 runs-on: macos-latest          runs-on: windows-latest
   1. checkout                    1. checkout
   2. setup-python 3.11/3.12      2. setup-python 3.11/3.12
   3. pip install .[dev]          3. pip install .[dev]
      + pyinstaller==6.22.3          + pyinstaller==6.22.3
   4. pyinstaller app.spec        4. pyinstaller app.spec
      -> dist/GDTF Comparer.app      -> dist/GDTF Comparer/ (+.exe)
   5. zip the .app bundle         5. zip the onedir folder
   6. upload-artifact             6. upload-artifact
        |                              |
        +--------------+---------------+
                        v
              [release job]
              runs-on: ubuntu-latest
                needs: [build-macos, build-windows]
                1. download-artifact (both)
                2. softprops/action-gh-release@v2
                   -> attaches both zips to the
                      GitHub Release tagged v1.0.0
                        |
                        v
             GitHub Releases page (D-03)
                        |
          +-------------+-------------+
          v                           v
    macOS user downloads        Windows user downloads
    .app.zip -> unzips ->       exe.zip -> unzips ->
    double-click -> Gatekeeper  double-click -> SmartScreen
    blocks (unsigned) ->        blocks (unsigned) ->
    System Settings > Privacy   "More info" > "Run anyway"
    & Security > Open Anyway    (D-01 bypass instructions,
    (corrected D-01 bypass       README/release notes)
     instructions)
```

### Recommended Project Structure
```
GDTFComparer/
├── pyproject.toml              # existing; add pyinstaller to [dev] optional deps
├── packaging/
│   └── app.spec                # single cross-platform PyInstaller spec file
├── .github/
│   └── workflows/
│       └── release.yml         # build-macos, build-windows, release jobs
└── src/gdtf_comparer/
    └── app.py                  # existing entry point, main() — unchanged
```

### Pattern 1: Single cross-platform `.spec` file, not raw CLI flags per-OS
**What:** One `packaging/app.spec` file, invoked identically (`pyinstaller packaging/app.spec`) by both the macOS and Windows CI jobs. OS-specific differences (if any manual `--add-data` entries are ever added) are handled *inside* the spec file with `os.pathsep`/`sys.platform` checks, not by maintaining two separate CLI command strings in the workflow YAML.
**When to use:** Any time the same build needs to run unmodified on two OSes via CI — avoids drift between a "macOS command" and a "Windows command" that are supposed to produce equivalent output.
**Example:**
```python
# packaging/app.spec
# Source: PyInstaller official spec-files docs (pyinstaller.org/en/stable/spec-files.html)
# [CITED: https://pyinstaller.org/en/stable/spec-files.html]
import sys

block_cipher = None

a = Analysis(
    ['../src/gdtf_comparer/app.py'],
    pathex=['../src'],
    binaries=[],
    datas=[],          # qt_material's own hook supplies its datas automatically --
                        # see "Don't Hand-Roll" below. No manual entry needed here.
    hiddenimports=[],   # PyInstaller's built-in PySide6 hook covers the standard
                        # modules; add entries here only if a specific
                        # "ModuleNotFoundError" surfaces during the clean-machine
                        # smoke test (see Pitfalls).
    hookspath=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GDTF Comparer',
    console=False,        # --windowed equivalent
    icon=None,             # no app icon exists in this repo yet (verified: no
                           # .icns/.ico under src/ or project root) -- add one
                           # later if desired; omitting is safe for PKG-01/02/03
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='GDTF Comparer',
)

app = BUNDLE(
    coll,
    name='GDTF Comparer.app',
    icon=None,
    bundle_identifier='dev.brandoneckstorm.gdtfcomparer',
)
# BUNDLE() is a no-op on Windows -- PyInstaller only produces .app bundles
# when run on macOS. Both platforms can safely share this same spec file.
```
[VERIFIED: /Users/brandon/GDTFComparer/.venv/lib/python3.12/site-packages/qt_material/hook-qt_material.py (full file, 20 lines) and /Users/brandon/GDTFComparer/.venv/lib/python3.12/site-packages/qt_material-2.17.dist-info/METADATA / entry_points.txt — read this session]

### Pattern 2: Rely on qt-material's self-registered PyInstaller hook — do not hand-write `--add-data` for it
**What:** `qt_material` ships `qt_material/hook-qt_material.py` *inside its own installed package*, and its `dist-info/entry_points.txt` declares:
```
[pyinstaller40]
hook-dirs = qt_material:get_hook_dirs
```
[VERIFIED: .venv/lib/python3.12/site-packages/qt_material-2.17.dist-info/entry_points.txt — read this session; file content quoted verbatim above]

The hook file itself contains (quoted verbatim):
```python
import qt_material
from pathlib import Path

qt_material_path = Path(qt_material.__file__).parent

fonts_path = qt_material_path / "fonts"
datas = [(str(fonts_path), "qt_material/fonts")]

themes_path = qt_material_path / "themes"
datas += [(str(themes_path), "qt_material/themes")]

dock_path = qt_material_path / "dock_theme.ui"
datas += [(str(dock_path), "qt_material")]

template_path = qt_material_path / "material.qss.template"
datas += [(str(template_path), "qt_material")]

resources_path = qt_material_path / "resources"
datas += [(str(resources_path), "qt_material/resources")]
```
[VERIFIED: .venv/lib/python3.12/site-packages/qt_material/hook-qt_material.py, lines 1-20 — read in full this session]

`pyinstaller40` is PyInstaller's standard entry-point group for third-party packages to self-register hook directories (supported since PyInstaller 4.4+) — PyInstaller automatically discovers and loads this hook the moment `qt-material` is `pip install`-ed into the same environment PyInstaller runs in. **No `--add-data` flags for qt-material's themes/fonts/resources are needed in the spec file or CI command.**

**This corrects an assumption recorded in 04-CONTEXT.md** ("Integration Points": *"qt-material's theme files and any icon assets... will need explicit `--add-data` flags... they are not pure Python and won't be auto-bundled"*) — that statement is informational context, not one of the four locked Decisions (D-01–D-04), so correcting it does not re-litigate anything locked. If, after the clean-machine smoke test (Pitfalls, below), any qt-material asset is still found missing, add the specific missing path via `--add-data` *then* — don't pre-emptively hand-write entries this researcher has verified are already automatic.

**When to use:** Whenever a dependency ships its own `pyinstaller40` hook-dirs entry point — check `<package>.dist-info/entry_points.txt` before manually writing `--add-data`/`hiddenimports` for that dependency.

### Anti-Patterns to Avoid
- **Hand-writing `--add-data` for qt-material themes/fonts:** Redundant (see Pattern 2) and creates a second source of truth that can drift from qt-material's own hook if qt-material adds/renames theme files in a future version bump.
- **Shipping `--onefile` as the primary distribution format:** Already flagged in `.planning/research/PITFALLS.md` Pitfall 3 — `--onefile`'s self-extraction-to-temp-dir behavior is the most-cited cause of Windows AV/SmartScreen false positives, and it also slows every app launch. Use `--onedir`, zipped for distribution.
- **Maintaining two different CLI invocations (one per OS) instead of one shared `.spec` file:** Invites silent drift between the macOS and Windows build configuration.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bundling qt-material's theme XML/font/resource files | Manual `--add-data` list for every qt_material subfolder | qt-material's self-registered `pyinstaller40` hook (automatic) | Verified present and functional in the installed package this session — see Pattern 2 |
| Detecting PySide6's required Qt plugins/DLLs | Manually enumerating every `.dll`/`.so`/`.dylib` PySide6 needs | PyInstaller's built-in PySide6 support (ships inside PyInstaller core itself, not a separate hooks package) | PyInstaller has shipped first-class PySide6 hook coverage for years; manual enumeration is exactly the kind of fragile, version-drift-prone work PyInstaller's hook system exists to avoid |
| Attaching release assets across two OS runners | Hand-rolled `curl`/`gh api` calls to GitHub's upload-release-asset REST endpoint from each OS's shell | `actions/upload-artifact` (fan-in) + `softprops/action-gh-release` (fan-out to the release) | Handles auth, retries, and the awkward upload-URL plumbing that hand-rolled REST calls get wrong on first attempt (see "Alternatives Considered" above for why this is preferred over raw `gh release upload`) |

**Key insight:** This phase's temptation to hand-roll is almost entirely in the packaging-asset-bundling space (qt-material files, Qt plugins) — and in every case investigated this session, the ecosystem tooling (PyInstaller's hook-discovery mechanism) already solves it automatically once the dependency is simply installed in the build environment. The only genuinely manual work left is the OS-level Gatekeeper/SmartScreen bypass instructions, which are inherently a documentation problem, not a code problem — there's no package to install that makes an *unsigned* binary stop being flagged by the OS.

## Common Pitfalls

> `.planning/research/PITFALLS.md` already covers three directly relevant pitfalls in depth (clean-machine verification, Gatekeeper "damaged app," Windows SmartScreen/AV false positives). The entries below add only what that document does **not** already cover: the exact current-OS bypass click-path (which has changed since PITFALLS.md was researched 2026-09-25) and PySide6-specific PyInstaller plugin-loading failures.

### Pitfall P1 (correction to existing PITFALLS.md Pitfall 2): "Right-click → Open" no longer bypasses Gatekeeper on current macOS
**What goes wrong:** The bypass instructions locked into D-01's wording ("macOS: right-click the app → Open") describe a Gatekeeper override that **Apple removed in macOS Sequoia (15, released September 2024)**. A user on Sequoia or any later release who follows "right-click → Open" will see the app still refuses to launch, with no obvious next step — exactly the "scares away non-technical users" failure mode PITFALLS.md Pitfall 2 already warns about, except now triggered by instructions that look correct but are stale.
**Why it happens:** Apple's own stated rationale (per Apple Developer News) was to stop malicious installers from instructing victims to "right-click → Open" past security prompts — so they removed the shortcut and now require a deliberate trip through System Settings instead. [CITED: developer.apple.com/news/?id=saqachfa; cross-checked against support.apple.com/en-us/102445, AppleInsider, iboysoft, idownloadblog, Christian Tietze's forum — MEDIUM confidence, multiple independent corroborating sources, not reproduced on a physical test machine this session]
**How to avoid:** Ship bypass instructions with the **current** flow:
1. Download and unzip the app; double-click to launch.
2. macOS blocks it ("Apple could not verify..." / "is damaged and can't be opened" — wording varies by exact macOS version).
3. Open **System Settings → Privacy & Security**.
4. Scroll down to the security message about the blocked app; click **Open Anyway**.
5. The original block dialog reappears; click **Open** to confirm.
6. Authenticate with an administrator password/Touch ID if prompted.
7. The app is now permanently allowlisted — future launches are normal double-clicks.

Optionally, offer a terminal one-liner for comfortable users as a faster alternative: `xattr -cr "/Applications/GDTF Comparer.app"` (strips the quarantine attribute entirely, skipping the GUI flow). [CITED: multiple sources corroborate `xattr -cr`/`xattr -d com.apple.quarantine` as the terminal-based quarantine removal — MEDIUM confidence]
**Warning signs:** Any shipped instructions that say only "right-click → Open" with no System Settings step — this will silently fail for every user on macOS 15+ (which, as of October 2026, is almost the entire active macOS user base).
**Phase to address:** This phase — the bypass instructions text is produced here (Claude's Discretion per CONTEXT.md), so this is the only point where the correction can land before real users see it.

### Pitfall P2: PySide6 "could not find or load the Qt platform plugin windows/cocoa" after PyInstaller freeze
**What goes wrong:** The frozen app launches on the build machine (where a full PySide6 install's plugin directory is on disk) but fails immediately on a clean target machine with `qt.qpa.plugin: Could not find the Qt platform plugin "windows" in ""` (Windows) or the `cocoa` equivalent (macOS) — the app exits instantly with no window, no crash dialog, often just a console message if `console=True`/visible, or a silent exit if `--windowed`.
**Why it happens:** PyInstaller's built-in PySide6 hook usually bundles the `platforms/` plugin subdirectory automatically, but version-to-version PySide6/PyInstaller interactions have intermittently broken this (see `pyinstaller/pyinstaller#5493`, Qt forum threads for PySide6 6.3+). [CITED: github.com/pyinstaller/pyinstaller/issues/5493; forum.qt.io/topic/122641 and /140809 — MEDIUM confidence, multiple independent reports of the same symptom across PyInstaller/PySide6 version combinations]
**How to avoid:**
- After the first build, actually launch the frozen binary (not just confirm the build command exited 0) — this is the same clean-machine gate PITFALLS.md Pitfall 1 already requires.
- If this specific error appears, add an explicit datas entry pointing at PySide6's own plugins directory, e.g. in the spec file: `datas += [(str(Path(PySide6.__file__).parent / "plugins" / "platforms"), "PySide6/plugins/platforms")]`, or diagnose first with `QT_DEBUG_PLUGINS=1` set as an environment variable before launching the frozen binary, which prints exactly which plugin paths Qt tried and why each failed.
**Warning signs:** App works via `python -m gdtf_comparer.app` but the frozen build exits instantly with no visible window and no error dialog.
**Phase to address:** This phase, verified during the required clean-machine smoke test (inherited from PITFALLS.md Pitfall 1 — this phase's plan must include that gate, not just "pyinstaller exits 0").

## Code Examples

### GitHub Actions workflow: two explicit jobs + fan-in release job
```yaml
# Source: synthesized from PyInstaller+GitHub Actions multi-OS tutorials
# [CITED: data-dive.com/multi-os-deployment-in-cloud-using-pyinstaller-and-github-actions/,
#  dmnfarrell.github.io/software/github-actions-pyinstaller,
#  github.com/softprops/action-gh-release — MEDIUM confidence, cross-checked pattern]
name: Release

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:   # allows a manual re-run without pushing a new tag

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pip install pyinstaller==6.22.3
      - run: pyinstaller packaging/app.spec
      - run: ditto -c -k --sequesterRsrc --keepParent "dist/GDTF Comparer.app" "GDTF-Comparer-macos.zip"
      - uses: actions/upload-artifact@v4
        with:
          name: macos-build
          path: GDTF-Comparer-macos.zip

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pip install pyinstaller==6.22.3
      - run: pyinstaller packaging/app.spec
      - run: Compress-Archive -Path "dist/GDTF Comparer" -DestinationPath "GDTF-Comparer-windows.zip"
      - uses: actions/upload-artifact@v4
        with:
          name: windows-build
          path: GDTF-Comparer-windows.zip

  release:
    needs: [build-macos, build-windows]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: macos-build
      - uses: actions/download-artifact@v4
        with:
          name: windows-build
      - uses: softprops/action-gh-release@v2
        with:
          files: |
            GDTF-Comparer-macos.zip
            GDTF-Comparer-windows.zip
```
Note: `ditto` (macOS-native zip tool) is preferred over plain `zip` for `.app` bundles because it preserves resource forks/extended attributes correctly; `Compress-Archive` is PowerShell's built-in zip cmdlet, available by default on `windows-latest` runners.

### Triggering on tag push vs. manual dispatch
`on: push: tags: ['v*']` triggers automatically whenever a version tag (e.g. `v0.2.0`) is pushed — matches D-03/D-04 (one tagged release, both platforms together). Adding `workflow_dispatch:` alongside it (shown above) is a low-cost addition that lets the maintainer manually re-run the exact same build (e.g., after fixing a CI config bug) without needing to delete and re-push a tag. [CITED: github.blog/changelog/2020-07-06-github-actions-manual-triggers-with-workflow_dispatch]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Right-click (Control-click) → Open to bypass Gatekeeper on an unsigned app | Attempt open (blocked) → System Settings → Privacy & Security → Open Anyway → confirm Open | macOS Sequoia (15), September 2024 | Any bypass documentation written before Sept 2024 (including training-data-era knowledge) is now incorrect and must be corrected before shipping to real users |
| Hand-writing `--add-data` for every third-party Qt-adjacent package's asset files | Check `<package>.dist-info/entry_points.txt` for a `pyinstaller40` `hook-dirs` entry first — many modern packages (qt-material included) self-register | Ongoing (PyInstaller 4.4+ supported this mechanism for years; this session verified qt-material 2.17 specifically uses it) | Saves maintenance burden and avoids drift between manually-written `--add-data` lists and the package's actual asset layout |

**Deprecated/outdated:**
- "Right-click → Open" as a universal macOS Gatekeeper bypass instruction — stale advice as of any macOS release from Sequoia (Sept 2024) onward; do not ship this wording.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The exact current-macOS Gatekeeper bypass click-path (System Settings → Privacy & Security → Open Anyway) is accurate for whatever specific macOS version(s) real end users run in practice, including the current 2026 release | Common Pitfalls P1 | If Apple has further changed this flow in a macOS release after the sources consulted this session (all dated 2024-2026 but not independently reproduced on a live Mac this session), shipped instructions could still mislead users; mitigate by having a human tester actually walk through the flow on a real current-OS Mac before the release ships, not just trusting this write-up |
| A2 | `pyinstaller==6.22.3`'s built-in PySide6 hook coverage is sufficient without any manual `hiddenimports`/`datas` entries beyond what qt-material's self-registered hook already provides | Pattern 1/2, Code Examples | If a specific PySide6 submodule (e.g. a QML/multimedia feature not currently used by this app) is dynamically imported somewhere not yet written, the clean-machine smoke test would surface a missing-module error, requiring one additional `hiddenimports` entry — low risk since this app only uses `QtWidgets`/`QtCore`/`QtGui`, PyInstaller's best-covered PySide6 surface |
| A3 | `softprops/action-gh-release@v2` remains actively maintained and safe to pin at `@v2` without a specific commit SHA | Standard Stack, Code Examples | Low risk — widely used Action with a stable major-version tag; if ever a concern, pin to a specific release SHA instead of the floating `@v2` tag |

**If this table is empty:** N/A — see above.

## Open Questions

1. **Exact current-macOS version's precise Gatekeeper dialog wording**
   - What we know: the System Settings → Privacy & Security → Open Anyway flow is correct as of macOS Sequoia (15, 2024) onward, cross-checked across five independent sources this session.
   - What's unclear: the literal text of the blocking dialog ("Apple could not verify..." vs. "...is damaged and can't be opened...") varies slightly by exact macOS point release and by whether the app is ad-hoc-signed vs. fully unsigned (PyInstaller's default output is unsigned, no ad-hoc signature, per D-01's explicit choice not to sign).
   - Recommendation: when the planner/executor writes the actual bypass-instructions text, phrase it to match either dialog wording ("you may see a message like 'Apple could not verify...' or 'is damaged...'") rather than quoting one exact string, and have a human confirm against a real current-macOS machine before the release ships (this is a `checkpoint:human-verify`-worthy step given PKG-03's correctness is user-facing and safety-relevant to adoption).

2. **Whether an app icon should be added this phase**
   - What we know: no `.icns`/`.ico` file exists anywhere in this project's own source tree (verified: only PySide6's own bundled tool icons were found under `.venv/`, none belonging to this app).
   - What's unclear: whether shipping without a custom icon (falling back to a generic/blank icon in the Dock/Taskbar) is acceptable for this phase, or whether the planner should scope in sourcing/creating one.
   - Recommendation: Claude's Discretion per CONTEXT.md did not explicitly call out an icon requirement, and PKG-01/02/03 don't require one — treat as out of scope for this phase unless the planner decides otherwise; omitting `icon=` in the spec file (as shown in Code Examples) is a safe, low-risk default.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PyInstaller | Freezing the app for both OSes | ✗ (not yet installed in this project's `.venv` or `pyproject.toml`) | — | Install via `pip install pyinstaller==6.22.3` as part of this phase's work — not a blocker, just not yet done |
| GitHub Actions | CI build/release pipeline (D-02) | ✓ (repo is already hosted on GitHub per git status/commit history) | n/a (hosted service) | — |
| `.github/workflows/` directory | CI workflow file | ✗ (does not exist yet — confirmed via `ls .github/workflows/`) | — | This phase creates it; not a blocker |
| macOS/Windows physical test machines for the clean-machine smoke test (PITFALLS.md Pitfall 1) | Verifying PKG-01/02 actually work on a machine with no Python | Unknown — not probed this session (outside this researcher's reach) | — | If unavailable, the GitHub Actions runners themselves (`macos-latest`/`windows-latest`) are themselves "clean machines" with no developer Python install beyond what the workflow explicitly sets up — running the frozen binary as a CI smoke-test step (not just building it) is a viable substitute if no physical second machine is available to the user |

**Missing dependencies with no fallback:** none — both missing items (PyInstaller, `.github/workflows/`) are simply this phase's own deliverables, not external blockers.

**Missing dependencies with fallback:** physical clean-machine access — fallback is using the CI runner itself as the clean-machine smoke-test environment (launch the frozen binary as a build step, not just build it).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.1.1 + pytest-qt 4.5.0 (existing, per `pyproject.toml` [VERIFIED: /Users/brandon/GDTFComparer/pyproject.toml, lines 19-22 — read this session: `dev = [\n    "pytest==9.1.1",\n    "pytest-qt==4.5.0",\n]`]) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` (existing) [VERIFIED: pyproject.toml lines 28-32 — read this session: `[tool.pytest.ini_options]\ntestpaths = ["tests"]\npythonpath = ["src"]\naddopts = "--import-mode=importlib -ra"\nqt_api = "pyside6"`] |
| Quick run command | `pytest tests/ -x` |
| Full suite command | `pytest tests/` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | macOS user can download and run the packaged app with no Python install | smoke (manual-only, see justification) | n/a — frozen-binary launch cannot be exercised by pytest; CI step: `open "dist/GDTF Comparer.app"` then a short-lived liveness check, or manual launch on a real Mac | ❌ Wave 0 — add a CI smoke step, not a pytest test |
| PKG-02 | Windows user can download and run the packaged app with no Python install | smoke (manual-only, see justification) | n/a — same reasoning; CI step: run `dist/GDTF Comparer/GDTF Comparer.exe` headlessly with a timeout, or manual launch on a real Windows machine | ❌ Wave 0 — add a CI smoke step, not a pytest test |
| PKG-03 | Build launches without Gatekeeper "damaged app" block / SmartScreen block, "otherwise configured" via bypass instructions | manual-only | n/a — inherently an OS-security-dialog interaction; no automated test can click through a native OS security prompt | ❌ Manual UAT required — human must actually walk the documented bypass steps against a real downloaded artifact before calling PKG-03 done |

**Justification for manual-only classification:** All three requirements are about what happens when a *frozen binary*, downloaded via browser (so the OS quarantine/reputation flags are genuinely set), is launched on a machine with no Python and no prior trust established with that specific binary. Pytest/pytest-qt exercise the *app's own code* once it's already running inside a Python interpreter — they cannot exercise PyInstaller's freeze process, OS-level Gatekeeper/SmartScreen dialogs, or quarantine-attribute behavior, all of which only manifest on a genuinely downloaded, unsigned, frozen artifact. This matches the existing PITFALLS.md "Looks Done But Isn't" checklist, which already specifies the correct verification for this phase: launch the *actual built artifact* on a *different* machine downloaded via browser, not a pytest assertion.

### Sampling Rate
- **Per task commit:** N/A for packaging-specific tasks (no new application code is being added/changed this phase — see Architectural Responsibility Map, this is purely build/CI/docs work). Existing `pytest tests/ -x` should still be run if any `pyproject.toml` edits risk breaking the existing test configuration.
- **Per wave merge:** Full existing suite (`pytest tests/`) to confirm packaging-phase changes to `pyproject.toml` haven't broken anything already working.
- **Phase gate:** Manual UAT per the three rows above — a human must download the actual release artifact (not a local build) for both OSes and walk through the documented bypass steps before this phase can be considered verified. This is **not optional and not automatable** — flag explicitly in the plan as a `checkpoint:human-verify` gate, separate from and in addition to the package-legitimacy checkpoint already required for the `pyinstaller` SUS verdict above.

### Wave 0 Gaps
- [ ] `.github/workflows/release.yml` — does not exist yet (confirmed via `ls`); this phase's primary deliverable.
- [ ] `packaging/app.spec` — does not exist yet; this phase's primary deliverable.
- [ ] No automated test can substitute for the manual cross-machine Gatekeeper/SmartScreen walkthrough — document this limitation explicitly in the plan rather than treating "pytest passes" as sufficient evidence PKG-01/02/03 are done.

## Security Domain

> `security_enforcement` is enabled per `.planning/config.json` (absent key would also default to enabled; here it is explicitly `true`).

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | This phase has no login/auth surface — it's a packaging/distribution pipeline |
| V3 Session Management | No | N/A |
| V4 Access Control | No | N/A |
| V5 Input Validation | No (not newly introduced this phase) | Existing `defusedxml`/size-limit work from earlier phases already covers the app's actual untrusted-input surface (GDTF/XML files); this phase adds no new input-handling code |
| V6 Cryptography | Partially — code signing is the relevant control, explicitly declined | D-01 is a documented, reversible decision to ship without code-signing/notarization. No cryptographic code is written by this phase; "signing" here means Apple/Microsoft's platform-level signing infrastructure, not an application concern. The ASVS-relevant mitigation this phase *does* apply is honest, correct user communication about the unsigned status (the corrected bypass instructions above) rather than silently hoping users don't notice |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Supply-chain risk in CI (a compromised/typosquatted PyPI package installed during the GitHub Actions build) | Tampering | Pin exact versions (`pyinstaller==6.22.3`, matching STACK.md) rather than open ranges; this research's Package Legitimacy Audit above already flags `pyinstaller` for a mandatory human checkpoint before install, consistent with this concern |
| Users trained to blindly click through OS security warnings ("Open Anyway" / "Run anyway") for *any* app, not just this one | Social engineering / Repudiation (of the warning's intent) | This is an acknowledged, explicit tradeoff of D-01 (ship unsigned) rather than something this phase can engineer around — the bypass instructions should be scoped narrowly ("only do this for a build you downloaded directly from the project's GitHub Releases page, verify the URL") to avoid training users into a dangerous general habit, without overstating the risk for what is, per PROJECT.md, a free community tool with no revenue motive to abuse this |
| GitHub Actions workflow secrets/token exposure | Information Disclosure | This workflow needs no secrets beyond the automatically-provided `GITHUB_TOKEN` (which `softprops/action-gh-release` uses by default for release creation) — do not introduce any additional PATs/secrets for this phase; if future signing is added (D-01 is explicitly reversible), that would be the point to introduce a properly-scoped signing secret, not before |

## Sources

### Primary (HIGH confidence)
- `/Users/brandon/GDTFComparer/.venv/lib/python3.12/site-packages/qt_material/hook-qt_material.py` — read in full this session, quoted verbatim above
- `/Users/brandon/GDTFComparer/.venv/lib/python3.12/site-packages/qt_material-2.17.dist-info/entry_points.txt` and `METADATA` — read this session, quoted verbatim above
- `/Users/brandon/GDTFComparer/pyproject.toml` — read this session, quoted verbatim above
- `pip index versions pyinstaller` (ran this session) → confirms 6.22.3 is current/latest, published 2026-09-12

### Secondary (MEDIUM confidence)
- https://pyinstaller.org/en/stable/usage.html and https://pyinstaller.org/en/stable/spec-files.html — official PyInstaller docs, `--add-data` separator syntax and spec-file structure
- https://support.apple.com/en-us/102445, https://developer.apple.com/news/?id=saqachfa, https://appleinsider.com/articles/24/08/06/apple-removes-control-click-option-for-skipping-gatekeeper-in-macos-sequoia, https://www.idownloadblog.com/2024/08/07/apple-macos-sequoia-gatekeeper-change-install-unsigned-apps-mac/, https://forum.christiantietze.de/posts/2024/11/running-unsigned-applications-macos-sequoia/ — cross-checked corroboration (5 independent sources) of the macOS Sequoia+ Gatekeeper bypass change
- https://www.flamingo.run/blog/microsoft-defender-smartscreen, https://www.minitool.com/backup-tips/windows-protected-your-pc.html, https://www.techeia.com/blog/fix-smartscreen-unrecognized-app-windows-11, https://vovsoft.com/blog/how-to-solve-windows-protected-your-pc/ — cross-checked SmartScreen "More info → Run anyway" flow
- https://github.com/pyinstaller/pyinstaller/issues/5493, https://forum.qt.io/topic/122641, https://forum.qt.io/topic/140809 — PySide6 Qt-platform-plugin-not-found pitfall and fix
- https://github.com/softprops/action-gh-release — release-attachment Action usage pattern
- https://data-dive.com/multi-os-deployment-in-cloud-using-pyinstaller-and-github-actions/, https://dmnfarrell.github.io/software/github-actions-pyinstaller — multi-OS GitHub Actions + PyInstaller workflow pattern synthesis

### Tertiary (LOW confidence)
- None used directly in final claims — all web-sourced claims above were either tied to official docs/support pages or cross-checked across 3+ independent sources and promoted to MEDIUM.

## Metadata

**Confidence breakdown:**
- Standard stack (PyInstaller version, qt-material hook mechanism): HIGH — directly verified against installed package files and `pip index versions` this session
- Architecture (CI workflow pattern): MEDIUM — synthesized from multiple consistent tutorial sources, not executed/tested end-to-end this session
- Pitfalls (Gatekeeper/SmartScreen current UX): MEDIUM — cross-checked across several independent sources but not reproduced on a live, current macOS/Windows machine this session; flagged as an Open Question recommending a human `checkpoint:human-verify` before shipping the final bypass-instructions wording

**Research date:** 2026-10-14
**Valid until:** 30 days for the PyInstaller/qt-material mechanics (stable, slow-moving); 7-14 days for the Gatekeeper/SmartScreen UX claims specifically, since OS vendors change these flows without much warning (as the Sequoia change itself demonstrates) — re-verify against a live machine at UAT time regardless of this document's age.

---
*Phase: 4-standalone-packaging*
*Research completed: 2026-10-14*
