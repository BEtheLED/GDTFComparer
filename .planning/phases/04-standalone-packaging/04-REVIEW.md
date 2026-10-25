---
phase: 04-standalone-packaging
reviewed: 2026-10-25T14:54:04Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - pyproject.toml
  - packaging/app.spec
  - packaging/smoke_check.py
  - tests/test_smoke_check.py
  - .github/workflows/release.yml
  - README.md
  - packaging/release-notes.md
  - tests/test_release_docs.py
  - packaging/RELEASING.md
findings:
  critical: 0
  warning: 3
  info: 4
  total: 7
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-10-25T14:54:04Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

This is the first code review of phase 04 (standalone-packaging). A dedicated STRIDE security audit (`04-SECURITY.md`) was already run and closed with 0 open threats at or above `high`, so this review does not re-litigate that register. Instead it focuses on correctness, error handling, and maintainability in the packaging/CI/docs surface: `packaging/app.spec`, `packaging/smoke_check.py` + its tests, `.github/workflows/release.yml`, and the two first-launch documents + their shared test suite.

The full test suite (462 tests, including `tests/test_smoke_check.py` and `tests/test_release_docs.py`) passes locally, and the documented claims in the four plan SUMMARYs match what is actually on disk (pyproject.toml's single added pin line, `packaging/__init__.py` absent, `datas=[]` in the spec, etc.).

No Critical/blocker-level defects were found — the shipped macOS/Windows paths (the only platforms this project actually builds and distributes) are exercised by both the local Mac build and a green CI run, per the SUMMARYs, and nothing in this review contradicts that. The findings below are robustness and maintainability gaps: two correctness gaps in `smoke_check.py`'s exception handling that would violate its own documented single-line CLI contract on error paths that aren't currently exercised by any test or by CI (unsupported platform, corrupt/malformed zip), plus a defense-in-depth gap in zip extraction, and a handful of smaller consistency/test-coverage notes.

## Warnings

### WR-01: `extract_zip()`'s `zipfile.extractall()` has no path-traversal guard (zip-slip)

**File:** `packaging/smoke_check.py:162-164`
**Issue:** On non-macOS platforms, `extract_zip()` extracts an arbitrary zip with plain `zipfile.ZipFile(zip_path).extractall(dest)`. `extractall()` does not sanitize member names: a crafted zip containing an entry like `../../evil` (or an absolute path on some zip producers) can write outside `dest` (CWE-22 / "zip slip"). Today the only callers pass zips that are either produced by this project's own CI (`GDTF-Comparer-windows.zip`) or supplied by a developer invoking `packaging/smoke_check.py --zip <file>` locally, so the practical exposure is low — this is a build/dev tool, not something the shipped app exposes to end users, and it is a different code path from the STRIDE register in `04-SECURITY.md` (which covers the *release pipeline's* tampering/DoS threats, not this extraction call itself). Still, the function offers no protection if it is ever pointed at a zip of unknown origin (e.g. a maintainer accidentally runs `--zip` against a downloaded file to "just check" it).
**Fix:**
```python
def extract_zip(zip_path: Path, dest: Path) -> Path:
    ...
    else:
        with zipfile.ZipFile(zip_path) as archive:
            dest_resolved = dest.resolve()
            for member in archive.namelist():
                target = (dest_resolved / member).resolve()
                if not str(target).startswith(str(dest_resolved) + os.sep):
                    raise ValueError(f"zip entry escapes destination: {member!r}")
            archive.extractall(dest)
    return dest
```

### WR-02: Unhandled exceptions on uncommon paths bypass `smoke_check.py`'s own "exactly one final line" CLI contract

**File:** `packaging/smoke_check.py:115` (and `145-165`)
**Issue:** The module docstring promises: "0 Printed one line starting with 'SMOKE PASS:'. 1 Printed one line starting with 'SMOKE FAIL:' ... 2 argparse usage error." Two paths violate that contract with an uncaught exception instead of a clean `SMOKE FAIL:` line:
- `find_executable()` (line 115) `raise RuntimeError(f"unsupported platform for smoke check: {sys.platform}")` on any platform other than `darwin`/`win32`. This is called directly from `main()` with no surrounding `try/except`, so on an unsupported platform (e.g. a Linux dev machine) the script crashes with a Python traceback rather than printing `SMOKE FAIL: unsupported platform ...` and exiting 1. The plan's own Task 2 action text for this function says "On any other platform, a SMOKE FAIL naming the platform. Return the path" — i.e. the function was specified to *return* something nameable, not raise, so `main()` could still produce the standard one-line message.
- `extract_zip()`'s `subprocess.run([...ditto...], check=True)` (macOS) can raise `subprocess.CalledProcessError` on a corrupt/incompatible zip, and `zipfile.ZipFile(zip_path)` (Windows) can raise `BadZipFile`. Neither is caught in `main()`, so a malformed release zip produces a raw traceback instead of `SMOKE FAIL: ...`.

Not currently exercised by `tests/test_smoke_check.py` (which only drives `--exe`/`--dist`) or by CI (which only runs on macOS/Windows with well-formed zips it just built itself), so this hasn't caused a visible failure yet — but it is a real gap relative to the script's documented contract, and the whole point of this tool (per its own docstring, quoting PITFALLS 1) is to "fail loudly" in exactly one recognizable way for every failure mode.
**Fix:** Wrap the body of `main()`'s source-resolution logic in a `try/except Exception as exc: print(f"SMOKE FAIL: {exc}"); return 1` (or catch the specific exception types), so every failure — expected or not — still honors the one-line contract.

### WR-03: `test_release_notes_links_are_absolute` never exercises a real markdown link

**File:** `tests/test_release_docs.py:165-170`, `packaging/release-notes.md`
**Issue:** The test extracts markdown link targets (`[text](url)`) from `packaging/release-notes.md` and asserts each starts with `https://`. But `packaging/release-notes.md` contains zero bracketed markdown links — every URL in it is a bare `https://...` string, not `[label](url)` syntax. `_MARKDOWN_LINK.findall(text)` therefore returns an empty list and the `for target in targets:` loop never executes a single assertion. The test currently passes vacuously; it would not catch a real relative-link regression unless someone happens to introduce a bracketed link in the future (at which point it would start doing useful work). This isn't a functional bug today, but it is a test that currently provides no actual verification despite appearing in the "passed" count, which can give false confidence when triaging `tests/test_release_docs.py`'s pass rate.
**Fix:** Either assert `len(targets) >= 1` somewhere relevant (so an accidental future revert to zero links is visible), or add an explicit regression-style fixture link (even a self-referential one) to keep the assertion live, with a comment noting why it's needed.

## Info

### IN-01: Duplicated `windows_window_titles()` call and asymmetric diagnostics in `run_smoke()`'s settle loop

**File:** `packaging/smoke_check.py:325-338`
**Issue:** `windows_window_titles(process.pid)` is called once inside the settle `while` loop (to catch the PyInstaller error dialog early) and again immediately after the loop exits (to check for the main window). The two win32-only failure returns in this stretch (`"PyInstaller error dialog shown"` and `"no '<title>' window ..."`) also don't call `_print_diagnostic(_tail(log_path, _LOG_TAIL_LINES))` the way every other failure branch in this function does, so a CI failure on these two specific Windows paths won't include the app's log tail in the diagnostic output, making them slightly harder to debug than the other five failure modes.
**Fix:** Extract the "poll + collect titles" step into a small helper to avoid the duplicate `EnumWindows` round-trip, and add the same `_print_diagnostic(_tail(...))` call to both win32-specific failure returns for consistency with the other branches.

### IN-02: No unit test exercises `extract_zip()` or the `--zip` CLI path

**File:** `tests/test_smoke_check.py`, `packaging/smoke_check.py:145-165`
**Issue:** All 7 tests in `tests/test_smoke_check.py` drive the smoke check via `--exe` or `--dist`; none constructs a zip and runs `--zip`. `extract_zip()` and the `--zip` branch of `main()` (including `check_signature = True` for `--zip`) are therefore only exercised live, by the real CI run against the real build artifacts (per the 04-02/04-04 SUMMARYs) — there's no local, fast, repeatable regression test for this path. A regression here (e.g. the zip-slip gap in WR-01, or a future refactor breaking `--zip`) would only surface on the next CI run or release, not in `pytest`.
**Fix:** Add a test that builds a minimal zip with `zipfile.ZipFile` (POSIX layout mirroring the macOS/Windows structure) and asserts `extract_zip()` lands the expected files in `dest`, independent of a real PyInstaller build.

### IN-03: `FORBIDDEN_PHRASES` doesn't cover all Windows Defender exclusion cmdlets

**File:** `tests/test_release_docs.py:27-44`
**Issue:** The list guards against `"set-mppreference"` (lowercased) but not other PowerShell Defender-exclusion cmdlets such as `Add-MpPreference -ExclusionPath` or `Remove-MpThreat`. If a future doc edit added Defender-bypass instructions using one of those cmdlets instead of `Set-MpPreference`, `test_no_system_wide_security_off_switch` would not catch it, even though it clearly violates the same PKG-03 prohibition the list exists to enforce.
**Fix:** Broaden the guard to a substring match on `"mppreference"` (catching `Set-`, `Add-`, and any future `*-MpPreference` cmdlet) rather than the single exact cmdlet name.

### IN-04: Three near-identical checkout/setup-python/pip-install step sequences in `release.yml`

**File:** `.github/workflows/release.yml:28-41,69-80,107-115`
**Issue:** `build-macos`, `build-windows`, and `release` each repeat the same "checkout (persist-credentials: false) → setup-python 3.12" preamble, and `build-macos`/`build-windows` additionally repeat an identical `pip install ".[dev]"` + PyInstaller build invocation. This is a reasonable, explicitly-chosen tradeoff per the plan ("explicit named jobs instead of a matrix... Claude's discretion"), and GitHub Actions has no first-class way to share steps across jobs without a separate composite action or reusable workflow — so this is not a defect, just a note that a future maintainer touching one job's checkout/setup step should remember to check the other two for drift (there is no test enforcing the three stay in sync, unlike the doc-consistency guarantee `tests/test_release_docs.py` gives the README/release-notes pair).
**Fix (optional, not required):** If this workflow grows further, consider extracting the common checkout+setup-python+install steps into a composite action under `.github/actions/`.

---

_Reviewed: 2026-10-25T14:54:04Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
