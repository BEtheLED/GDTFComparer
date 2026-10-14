# Phase 4: Standalone Packaging - Context

**Gathered:** 2026-10-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce installable/runnable standalone builds of the app for macOS and Windows, with no separate Python install required by the end user, and with the OS-level security warnings (Gatekeeper on macOS, SmartScreen on Windows) handled in a way that doesn't block a normal person from running the app. This phase covers the build/package/distribute pipeline only — it does not touch app functionality (parsing, comparison, UI) built in Phases 1-3, and does not include MVR-xchange networking (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### Signing & Security Warnings
- **D-01:** Ship both the macOS and Windows builds unsigned — no Apple Developer Program enrollment ($99/yr) and no Windows code-signing certificate purchase. Instead, ship clear user-facing instructions for the one-time bypass on each OS (macOS: right-click the app → Open; Windows: "Windows protected your PC" → More info → Run anyway). This satisfies PKG-03's "signed OR otherwise configured to avoid being blocked" wording via the "otherwise configured" path. — **Reversibility:** reversible — signing can be added in a later release by inserting a signing/notarization step into the existing CI pipeline (D-02) without changing its shape.

### Build Process
- **D-02:** Build via GitHub Actions CI — one job on a `macos-latest` runner, one job on a `windows-latest` runner — rather than manual local builds, since PyInstaller cannot cross-compile (each OS's build must run on that OS). This matches the research recommendation in `.planning/research/STACK.md` and avoids requiring the user to personally own or borrow both a Mac and a Windows PC for every future release. — **Reversibility:** costly — once the release process and any release documentation are built around CI, reverting to manual builds means rewriting that process and relearning the manual steps.

### Distribution Channel
- **D-03:** Distribute via GitHub Releases — a tagged release attaches both the macOS and Windows build artifacts. Pairs naturally with the CI pipeline (D-02); no separate hosting/website needed. — **Reversibility:** reversible — artifacts could be mirrored or moved elsewhere later without changing how they're built.

### Platform Scope
- **D-04:** macOS and Windows ship together in one release (not staggered) — matches the ROADMAP's success criteria treating both platforms as equally required for this phase. — **Reversibility:** reversible.

### Claude's Discretion
- Exact wording/formatting of the user-facing bypass instructions for Gatekeeper and SmartScreen (README section, in-app message, or a text file alongside the build — Claude's call).
- GitHub Actions workflow structure (triggers, job naming, artifact upload mechanics, caching strategy).
- PyInstaller spec file details (`--windowed`, `--add-data` for qt-material theme/icon assets per `.planning/research/STACK.md`, exact `--name` string).
- Versioning/tagging scheme for releases (e.g., whether to bump `pyproject.toml`'s `version` field automatically or manually per release).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Packaging Tool & Platform Research
- `.planning/research/STACK.md` — PyInstaller rationale and version (6.22.3), the "no cross-compile" constraint, the Apple Developer Program / codesign+notarization cost note, GitHub Actions CI recommendation, and the "Alternatives Considered" table (why not Nuitka/Briefcase for this milestone)

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` — PKG-01 (macOS standalone run), PKG-02 (Windows standalone run), PKG-03 (signed/notarized OR otherwise configured to avoid Gatekeeper/SmartScreen block — this phase takes the "otherwise configured" path per D-01)
- `.planning/ROADMAP.md` Phase 4 section — goal and success criteria (macOS/Windows run with no Python install; no Gatekeeper "damaged app" block; no Windows SmartScreen block on first run)

### Project-Level Context
- `.planning/PROJECT.md` — "Revenue model: None — free tool for personal and community use" and "Success metric: People other than the creator can download and run the packaged app without installing Python" directly informed D-01 (no paid signing budget for a free tool)

### Project Metadata
- `pyproject.toml` — existing `[project.gui-scripts]` entry point (`gdtf-comparer = "gdtf_comparer.app:main"`) that PyInstaller should target; no `dev` dependency on PyInstaller yet (needs adding)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pyproject.toml`'s `[project.gui-scripts]` entry point (`gdtf_comparer.app:main`) is the natural PyInstaller entry point — no separate launcher script needed.

### Established Patterns
- No CI configuration exists yet (`.github/workflows/` is absent) — this is a greenfield setup, not a modification of existing automation.
- No `.spec` file, `build/`, or `dist/` directory exists yet — packaging work starts from zero in this phase.

### Integration Points
- `qt-material`'s theme files and any icon assets (per `.planning/research/STACK.md`) will need explicit `--add-data` flags in the PyInstaller build command/spec — they are not pure Python and won't be auto-bundled.

</code_context>

<specifics>
## Specific Ideas

The "free community tool, no revenue" framing (from PROJECT.md) was the deciding factor against paying for either platform's code-signing/notarization — the user explicitly chose the free "ship unsigned + bypass instructions" path for both macOS and Windows rather than a hybrid (e.g., paying for just one platform).

</specifics>

<deferred>
## Deferred Ideas

- **Project license change (GPLv3 → MIT):** Raised during this discussion but is a repo-wide, project-level decision, not part of Phase 4's packaging scope. The user confirmed they want MIT (to match the "keep it open, avoid GPL obligations" intent already baked into the PySide6-over-PyQt6 and MVR-xchange-reimplementation decisions). To be handled as its own follow-up task (e.g., `/gsd-quick`), not inside this phase's plan.

</deferred>

---

*Phase: 4-standalone-packaging*
*Context gathered: 2026-10-14*
