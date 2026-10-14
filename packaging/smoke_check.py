"""Smoke check for the frozen GDTF Comparer build.

Purpose: a PyInstaller build that exits 0 only proves the *build step*
succeeded -- it says nothing about whether the frozen app actually opens on
a machine with no Python or Qt installed (RESEARCH inherited PITFALLS 1:
"launch the built artifact, not just build it"). This script launches the
real executable (or the real .app bundle on macOS) with a stripped-down
environment and a fresh fake home folder, waits for qt-material to apply its
theme (direct evidence the app's data files were bundled correctly and the
app is alive past startup), and then requires it to stay up for a short
"settle" period before declaring success.

This module is standard library only. It never imports the application, Qt
or qt_material, so it stays usable even when the frozen app is broken in a
way that would make importing it crash the checker too.

CLI:
    python packaging/smoke_check.py [--dist DIR | --zip FILE | --exe FILE]
        [--startup-timeout SECONDS] [--settle SECONDS]

    --dist DIR    Look for the built app inside DIR (default "dist"), using
                  the standard PyInstaller COLLECT/BUNDLE layout.
    --zip FILE    Extract a release zip into a temporary folder first, then
                  check what a user downloading that zip would get.
    --exe FILE    Launch a raw executable directly, skipping the macOS code
                  signature check. Only meant for tests and local debugging;
                  CI never uses this flag.
    --startup-timeout SECONDS  How long to wait for the theme-icon evidence
                  before giving up (default DEFAULT_STARTUP_TIMEOUT).
    --settle SECONDS           How long the process must stay alive after
                  startup evidence appears before this script is satisfied
                  (default DEFAULT_SETTLE).

Exit codes:
    0  Printed one line starting with "SMOKE PASS:".
    1  Printed one line starting with "SMOKE FAIL:" naming the reason.
    2  argparse usage error (e.g. two mutually exclusive flags given).
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

APP_NAME = "GDTF Comparer"
MAIN_WINDOW_TITLE = "GDTF Comparer"

# Title of PyInstaller's Windows bootloader crash dialog
# (pyi_exception_dialog.c, Windows-only). Seeing this title means the app
# started but immediately hit an unhandled exception.
PYINSTALLER_ERROR_DIALOG_TITLE = "Unhandled exception in script"

# Evidence that qt_material.apply_stylesheet() ran inside the frozen app:
# it writes recolored SVG icons into this folder under whatever HOME the
# process sees (gui/theme.py install_os_theme, called before MainWindow()
# is built). If the theme XML/template were missing from the bundle, either
# the stylesheet call is silently skipped or the app crashes -- either way
# no icons would appear here.
THEME_ICON_GLOB = ".qt_material/theme/primary/*.svg"

DEFAULT_STARTUP_TIMEOUT = 90.0
DEFAULT_SETTLE = 10.0

# Environment variables removed before launch so the developer's own Python
# or Qt setup can never prop up a build that would be broken on a clean
# machine (RESEARCH inherited PITFALLS 1; T-04-03 in this plan's threat
# model).
STRIPPED_ENV_VARS = (
    "PYTHONPATH",
    "PYTHONHOME",
    "PYTHONSTARTUP",
    "PYTHONEXECUTABLE",
    "VIRTUAL_ENV",
    "QT_QPA_PLATFORM",
    "QT_PLUGIN_PATH",
    "QT_QPA_PLATFORM_PLUGIN_PATH",
    "QML2_IMPORT_PATH",
)

# How often run_smoke polls for the startup evidence.
_POLL_INTERVAL = 0.25

# How long the finally block waits for a terminated process to exit before
# escalating to kill().
_TERMINATE_GRACE = 10.0

# How many trailing lines of the app's own stdout/stderr log to include in a
# failure message, to help diagnose without needing to re-run.
_LOG_TAIL_LINES = 40


def find_executable(root: Path) -> Path:
    """Return the path to the frozen app's main executable under root.

    Parameters:
        root: The build output folder (a `--dist` folder, or the folder a
            `--zip` was extracted into).

    Returns:
        The expected path to the main executable for the current platform.
        The caller is responsible for checking existence and reporting
        "not found" -- this function always returns a path, even one that
        does not exist, so callers can include it in a failure message.
    """
    if sys.platform == "darwin":
        return root / f"{APP_NAME}.app" / "Contents" / "MacOS" / APP_NAME
    if sys.platform == "win32":
        return root / APP_NAME / f"{APP_NAME}.exe"
    raise RuntimeError(f"unsupported platform for smoke check: {sys.platform}")


def verify_app_signature(app_bundle: Path) -> Optional[str]:
    """Verify a macOS .app bundle's code signature.

    Parameters:
        app_bundle: Path to the `.app` bundle (not the inner executable).

    Returns:
        None if the signature is valid. Otherwise, codesign's combined
        stdout/stderr output describing why verification failed.
    """
    result = subprocess.run(
        [
            "/usr/bin/codesign",
            "--verify",
            "--deep",
            "--strict",
            "--verbose=2",
            str(app_bundle),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return None
    return (result.stdout or "") + (result.stderr or "")


def extract_zip(zip_path: Path, dest: Path) -> Path:
    """Extract a release zip into dest, preserving platform-relevant metadata.

    Parameters:
        zip_path: The release zip to extract (e.g. GDTF-Comparer-macos.zip).
        dest: An existing, empty destination folder.

    Returns:
        dest, for chaining.
    """
    if sys.platform == "darwin":
        # ditto preserves symlinks and the .app's code signature; a plain
        # zipfile extraction can silently corrupt both.
        subprocess.run(
            ["/usr/bin/ditto", "-x", "-k", str(zip_path), str(dest)],
            check=True,
        )
    else:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(dest)
    return dest


def smoke_environment(fake_home: Path) -> Dict[str, str]:
    """Build the environment the smoke-checked process is launched with.

    Parameters:
        fake_home: A fresh, empty temporary folder to use as the process's
            home folder, isolating it from the developer's real home, Qt
            setup and Python environment.

    Returns:
        A copy of os.environ with every name in STRIPPED_ENV_VARS removed,
        and HOME, USERPROFILE, APPDATA and LOCALAPPDATA pointed at fake_home
        (APPDATA/LOCALAPPDATA folders are created so Windows apps that write
        per-user files, such as this app's compare profiles, stay contained
        inside fake_home).
    """
    env = dict(os.environ)
    for name in STRIPPED_ENV_VARS:
        env.pop(name, None)

    env["HOME"] = str(fake_home)
    env["USERPROFILE"] = str(fake_home)

    appdata = fake_home / "AppData" / "Roaming"
    local_appdata = fake_home / "AppData" / "Local"
    appdata.mkdir(parents=True, exist_ok=True)
    local_appdata.mkdir(parents=True, exist_ok=True)
    env["APPDATA"] = str(appdata)
    env["LOCALAPPDATA"] = str(local_appdata)

    return env


def _tail(path: Path, lines: int) -> str:
    """Return the last `lines` lines of a text file, or "" if unreadable."""
    try:
        content = path.read_text(errors="replace")
    except OSError:
        return ""
    return "\n".join(content.splitlines()[-lines:])


def run_smoke(
    exe: Path, startup_timeout: float, settle: float
) -> Tuple[bool, str]:
    """Launch exe in isolation and check it starts, themes and stays up.

    Parameters:
        exe: Path to the executable to launch.
        startup_timeout: Seconds to wait for theme-icon evidence before
            giving up.
        settle: Seconds the process must stay alive after startup evidence
            appears.

    Returns:
        A (passed, message) tuple. message is a human-readable summary
        suitable for the final SMOKE PASS/FAIL line.
    """
    # Resolve to an absolute path before changing the child's cwd below --
    # otherwise a relative exe (e.g. "dist/GDTF Comparer.app/...") would be
    # looked up relative to fake_home instead of the caller's cwd.
    exe = exe.resolve()
    fake_home = Path(tempfile.mkdtemp(prefix="gdtf-smoke-home-"))
    log_path = fake_home / "app.log"
    process: Optional[subprocess.Popen] = None
    try:
        env = smoke_environment(fake_home)
        with open(log_path, "wb") as log_file:
            process = subprocess.Popen(
                [str(exe)],
                env=env,
                cwd=str(fake_home),
                stdout=log_file,
                stderr=subprocess.STDOUT,
            )

        theme_glob = THEME_ICON_GLOB
        deadline = time.monotonic() + startup_timeout
        themed = False
        while time.monotonic() < deadline:
            exit_code = process.poll()
            if exit_code is not None:
                return (
                    False,
                    f"exited during startup with code {exit_code}\n"
                    f"{_tail(log_path, _LOG_TAIL_LINES)}",
                )
            if any(fake_home.glob(theme_glob)):
                themed = True
                break
            time.sleep(_POLL_INTERVAL)

        if not themed:
            return (
                False,
                f"no qt-material theme icons after {startup_timeout} seconds\n"
                f"{_tail(log_path, _LOG_TAIL_LINES)}",
            )

        settle_deadline = time.monotonic() + settle
        while time.monotonic() < settle_deadline:
            exit_code = process.poll()
            if exit_code is not None:
                return (
                    False,
                    f"exited during the settle period with code {exit_code}\n"
                    f"{_tail(log_path, _LOG_TAIL_LINES)}",
                )
            time.sleep(_POLL_INTERVAL)

        return (
            True,
            f"{exe} started, applied its theme and stayed up {settle} s",
        )
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=_TERMINATE_GRACE)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        shutil.rmtree(fake_home, ignore_errors=True)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run the smoke check from the command line.

    Parameters:
        argv: Command-line arguments; defaults to sys.argv[1:] when None.

    Returns:
        0 on SMOKE PASS, 1 on SMOKE FAIL. argparse itself exits with 2 on a
        usage error (e.g. two mutually exclusive source flags given).
    """
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--dist", default=None, help="Build output folder")
    source.add_argument("--zip", default=None, help="Release zip to extract and check")
    source.add_argument("--exe", default=None, help="Raw executable to launch directly")
    parser.add_argument(
        "--startup-timeout",
        type=float,
        default=DEFAULT_STARTUP_TIMEOUT,
    )
    parser.add_argument("--settle", type=float, default=DEFAULT_SETTLE)
    args = parser.parse_args(argv)

    extracted_zip_dir: Optional[Path] = None
    check_signature = False
    try:
        if args.exe is not None:
            exe = Path(args.exe)
        elif args.zip is not None:
            extracted_zip_dir = Path(tempfile.mkdtemp(prefix="gdtf-smoke-zip-"))
            extract_zip(Path(args.zip), extracted_zip_dir)
            exe = find_executable(extracted_zip_dir)
            check_signature = True
        else:
            dist_dir = Path(args.dist) if args.dist is not None else Path("dist")
            exe = find_executable(dist_dir)
            check_signature = True

        if not exe.exists():
            print(f"SMOKE FAIL: {exe} not found")
            return 1

        if sys.platform == "darwin" and check_signature:
            app_bundle = exe.parents[2]
            signature_error = verify_app_signature(app_bundle)
            if signature_error is not None:
                print(f"SMOKE FAIL: invalid code signature\n{signature_error}")
                return 1

        passed, message = run_smoke(exe, args.startup_timeout, args.settle)
        if passed:
            print(f"SMOKE PASS: {message}")
            return 0
        print(f"SMOKE FAIL: {message}")
        return 1
    finally:
        if extracted_zip_dir is not None:
            shutil.rmtree(extracted_zip_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
