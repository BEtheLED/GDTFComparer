# Phase 4: Standalone Packaging - Pattern Map

**Mapped:** 2026-10-14
**Files analyzed:** 4 (greenfield deliverables)
**Analogs found:** 4 / 4 (config-convention analogs only — no CI/packaging precedent exists in this repo)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|----------------|
| `pyproject.toml` (modified: add `pyinstaller` to `dev`) | config | batch | `pyproject.toml` `[project.optional-dependencies] dev` (existing) | exact — same file, same list, additive edit |
| `packaging/app.spec` (new) | config | batch (build-time transform: Python src -> frozen binary) | `pyproject.toml` `[project.gui-scripts]` entry point + `src/gdtf_comparer/app.py` module layout | role-match — no existing build-spec file; app.py/app:main is the thing the spec must target |
| `.github/workflows/release.yml` (new) | config | event-driven (triggered by `git push --tags`) | none in-repo — no `.github/workflows/` exists | no analog — use RESEARCH.md Code Examples verbatim |
| Bypass-instructions doc (new: README section or `packaging/BYPASS.md`) | config/docs | request-response (human-readable, no code) | `README.md` (existing doc conventions) | role-match — follow existing README section style/tone |

## Pattern Assignments

### `pyproject.toml` (config, batch) — add `pyinstaller` to dev deps

**Analog:** `pyproject.toml` itself, lines 18-22 (existing `dev` list)

**Current pattern to extend** (verbatim, lines 18-22):
```toml
[project.optional-dependencies]
dev = [
    "pytest==9.1.1",
    "pytest-qt==4.5.0",
]
```

**Pattern to apply:** Add `"pyinstaller==6.22.3",` as a third pinned entry in this same list — exact-version pin, same style as the two existing entries (`==` pin, trailing comma, alphabetized-by-insertion not alphabetical). Do NOT add it to `[project] dependencies` (lines 11-16) — it is a build-time tool, not a runtime dependency of the shipped app, matching RESEARCH.md's explicit guidance.

**Entry point to target** (verbatim, lines 24-25 — this is what `packaging/app.spec`'s `Analysis(['...'])` must resolve to):
```toml
[project.gui-scripts]
gdtf-comparer = "gdtf_comparer.app:main"
```

**Module path confirmed on disk:** `src/gdtf_comparer/app.py` defines `main()` (verified via Read — composition root that builds `QApplication` + `MainWindow`, calls `install_os_theme(app)` from `gdtf_comparer.gui.theme`). The spec's `Analysis` entry script should point at this file path (`src/gdtf_comparer/app.py`), and `pathex=['src']` (relative to repo root, matching `[tool.setuptools.packages.find] where = ["src"]` and `[tool.pytest.ini_options] pythonpath = ["src"]` conventions already established at lines 27-28 and 32).

**Existing pytest config convention to mirror for any new tool config section** (lines 30-34):
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "--import-mode=importlib -ra"
qt_api = "pyside6"
```
If a `[tool.pyinstaller]`-style config block were ever needed (not required per RESEARCH.md — PyInstaller is driven by the `.spec` file, not `pyproject.toml`), follow this same `[tool.X]` TOML-table style.

---

### `packaging/app.spec` (config, batch)

**No in-repo analog** — this is a new file type for this repo. Source the structure from RESEARCH.md's verbatim Pattern 1 example (lines 163-218 of 04-RESEARCH.md), which is already tailored to this repo's actual entry point. Key points to carry over from this repo's real structure (not generic boilerplate):

- `Analysis(['src/gdtf_comparer/app.py'], pathex=['src'], ...)` — matches the verified `src/` layout and `app.py:main()` entry point above.
- `datas=[]` and leave qt-material bundling to its self-registered `pyinstaller40` hook (verified in RESEARCH.md against the installed `qt_material-2.17` package — do not hand-write `--add-data` for `qt_material/fonts`, `qt_material/themes`, `qt_material/resources`, `dock_theme.ui`, `material.qss.template`).
- `name='GDTF Comparer'` — matches `app.setApplicationName("GDTF Comparer")` already set in `app.py` (line ~27), so the frozen binary's display name is consistent with the app's own runtime-set name.
- `console=False` (the `--windowed` equivalent) — this is a GUI app (`gui-scripts` entry point, not `scripts`), no console window should appear.
- `icon=None` — confirmed no `.icns`/`.ico` exists anywhere in `src/` or repo root; omitting is the correct default per RESEARCH.md Open Question 2.
- `BUNDLE(... bundle_identifier='dev.brandoneckstorm.gdtfcomparer')` — only takes effect on macOS; no-op on Windows, so one spec file is safe to share across both CI jobs per D-02/D-04.

---

### `.github/workflows/release.yml` (config, event-driven)

**No in-repo analog** — `.github/workflows/` does not exist. Use RESEARCH.md's Code Examples section verbatim (04-RESEARCH.md lines 305-368): three jobs (`build-macos`, `build-windows`, `release`), triggered on `push: tags: 'v*'` plus `workflow_dispatch`, using `actions/checkout@v4`, `actions/setup-python@v5`, `pip install -e .[dev]`, `pip install pyinstaller==6.22.3`, `pyinstaller packaging/app.spec`, OS-native zip (`ditto` on macOS / `Compress-Archive` on Windows), `actions/upload-artifact@v4`, and a fan-in `release` job using `softprops/action-gh-release@v2`.

**Repo-specific substitutions to make into that template:**
- `pip install -e .[dev]` resolves correctly against this repo's actual `pyproject.toml` (the `dev` extra, once `pyinstaller` is added per above).
- `pyinstaller packaging/app.spec` — path matches the `packaging/app.spec` file created above.
- No existing CI secrets are configured in this repo (confirmed no other `.github/workflows/*.yml` to cross-reference) — only the automatically provided `GITHUB_TOKEN` is needed; do not introduce new secrets this phase (per RESEARCH.md Security Domain).

---

### Bypass-instructions doc (docs)

**Analog:** `README.md` (existing doc) — read its existing heading/tone conventions before adding a new section (Claude's Discretion per CONTEXT.md on placement: README section vs. standalone file).

**Content to ship (corrected per RESEARCH.md Pitfall P1 — do NOT use "right-click → Open," which is stale since macOS Sequoia):**
- macOS: attempt launch (blocked) -> System Settings -> Privacy & Security -> scroll to the blocked-app message -> "Open Anyway" -> re-attempt launch -> "Open" -> authenticate. Optional terminal alternative: `xattr -cr "/Applications/GDTF Comparer.app"`.
- Windows: attempt launch -> "Windows protected your PC" SmartScreen dialog -> "More info" -> "Run anyway".
- Scope the instructions narrowly to "only do this for a build downloaded directly from this project's GitHub Releases page" per RESEARCH.md's Security Domain guidance (avoid training users into a general habit of clicking through security warnings).

## Shared Patterns

### Version pinning convention
**Source:** `pyproject.toml` lines 11-16, 18-22 (every dependency uses exact `==` pins)
**Apply to:** `pyinstaller==6.22.3` in `dev` extras, and the `@v4`/`@v2` GitHub Action version pins in `release.yml` (pin exact major versions, not floating `@latest`).

### `src/` layout + entry-point convention
**Source:** `[tool.setuptools.packages.find] where = ["src"]`, `[tool.pytest.ini_options] pythonpath = ["src"]`, `[project.gui-scripts] gdtf-comparer = "gdtf_comparer.app:main"` (pyproject.toml lines 27-28, 32, 24-25)
**Apply to:** `packaging/app.spec`'s `Analysis(['src/gdtf_comparer/app.py'], pathex=['src'], ...)` — the spec file must target the same module path the existing entry point already uses, not a new/duplicate launcher script.

### No secrets beyond `GITHUB_TOKEN`
**Source:** RESEARCH.md Security Domain (no existing workflow files to reference in-repo; this is a new-repo convention, not an existing pattern)
**Apply to:** `.github/workflows/release.yml` — `softprops/action-gh-release@v2` uses the auto-provided `GITHUB_TOKEN`; no new PAT/secret should be added this phase.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `.github/workflows/release.yml` | config | event-driven | No CI workflow of any kind exists in this repo yet — first CI file for the project. Use RESEARCH.md Code Examples (lines 305-368) as the template of record instead of an in-repo analog. |
| `packaging/app.spec` | config | batch | No `.spec`, `build/`, or `dist/` artifact or file exists anywhere in this repo. Use RESEARCH.md Pattern 1 (lines 163-218) as the template of record, adapted with this repo's verified `src/gdtf_comparer/app.py` path. |

## Metadata

**Analog search scope:** repo root (`pyproject.toml`, `README.md`), `src/gdtf_comparer/` (package layout, `app.py` entry point), `.github/` (confirmed absent), `packaging/` (confirmed absent)
**Files scanned:** `pyproject.toml`, `src/gdtf_comparer/app.py` (imports/header), `src/gdtf_comparer/` directory listing, repo root directory listing
**Pattern extraction date:** 2026-10-14
