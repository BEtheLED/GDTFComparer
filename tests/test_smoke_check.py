"""Proof that packaging/smoke_check.py is not vacuous.

Mirrors tests/test_architecture.py::test_import_checker_detects_violations:
a guard that always passes is worthless. Each test here builds a small fake
"frozen app" (a POSIX executable script) that fails in one specific way a
real frozen build could fail, and checks that the smoke check actually
reports that failure -- plus one case where the fake behaves well and the
smoke check reports success.

Skipped entirely on Windows: the fakes below are POSIX shell/Python scripts
launched directly as an "executable", which Windows cannot run the same way.
Windows-specific behavior (the PyInstaller error-dialog check and the
"GDTF Comparer" window-title check, both driven by windows_window_titles())
is exercised by the CI windows job added in Plan 04-02, not here.
"""

import importlib.util
import json
import os
import stat
import sys
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="fake executables are POSIX scripts; Windows behavior is exercised by the CI windows job in Plan 04-02",
)

REPO_ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "gdtf_smoke_check", REPO_ROOT / "packaging" / "smoke_check.py"
)
smoke_check = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(smoke_check)


def _fake_app(tmp_path: Path, body: str) -> Path:
    """Write an executable Python script at tmp_path/"fake_app" and return it.

    Parameters:
        tmp_path: Directory to write the script into.
        body: Python source (without a shebang) forming the script's body.

    Returns:
        The path to the now-executable script.
    """
    script = tmp_path / "fake_app"
    script.write_text(f"#!{sys.executable}\n{body}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return script


# Shared preamble every fake uses to announce its pid, so tests can confirm
# the process is really gone after the smoke check's cleanup.
_RECORD_PID = """
import os
_pid_file = os.environ.get("SMOKE_TEST_PID_FILE")
if _pid_file:
    with open(_pid_file, "w") as _f:
        _f.write(str(os.getpid()))
"""

_WRITE_THEME_ICON = """
import os
from pathlib import Path as _Path
_home = _Path(os.environ["HOME"])
_theme_dir = _home / ".qt_material" / "theme" / "primary"
_theme_dir.mkdir(parents=True, exist_ok=True)
(_theme_dir / "icon.svg").write_text("<svg></svg>")
"""


def _process_is_gone(pid: int) -> bool:
    """Return True once os.kill(pid, 0) raises ProcessLookupError."""
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        time.sleep(0.1)
    return False


def test_fails_when_app_exits_during_startup(tmp_path, capsys):
    fake = _fake_app(
        tmp_path,
        _RECORD_PID + "import sys\nsys.exit(3)\n",
    )
    pid_file = tmp_path / "pid"

    with _monkeypatch_env(SMOKE_TEST_PID_FILE=str(pid_file)):
        returncode = smoke_check.main(
            ["--exe", str(fake), "--startup-timeout", "5", "--settle", "1"]
        )

    captured = capsys.readouterr()
    final_line = captured.out.strip().splitlines()[-1]
    assert returncode == 1
    assert final_line.startswith("SMOKE FAIL")
    assert "exited during startup" in final_line
    assert "3" in final_line


def test_fails_when_app_never_applies_theme(tmp_path, capsys):
    fake = _fake_app(tmp_path, _RECORD_PID + "import time\ntime.sleep(30)\n")
    pid_file = tmp_path / "pid"

    with _monkeypatch_env(SMOKE_TEST_PID_FILE=str(pid_file)):
        returncode = smoke_check.main(
            ["--exe", str(fake), "--startup-timeout", "2", "--settle", "1"]
        )

    captured = capsys.readouterr()
    final_line = captured.out.strip().splitlines()[-1]
    assert returncode == 1
    assert final_line.startswith("SMOKE FAIL")
    assert "theme" in final_line

    pid = int(pid_file.read_text())
    assert _process_is_gone(pid)


def test_passes_for_app_that_themes_and_stays_up(tmp_path, capsys):
    fake = _fake_app(
        tmp_path,
        _RECORD_PID + _WRITE_THEME_ICON + "import time\ntime.sleep(60)\n",
    )
    pid_file = tmp_path / "pid"

    with _monkeypatch_env(SMOKE_TEST_PID_FILE=str(pid_file)):
        returncode = smoke_check.main(
            ["--exe", str(fake), "--startup-timeout", "5", "--settle", "1"]
        )

    captured = capsys.readouterr()
    final_line = captured.out.strip().splitlines()[-1]
    assert returncode == 0
    assert final_line.startswith("SMOKE PASS")

    pid = int(pid_file.read_text())
    assert _process_is_gone(pid)


def test_fails_when_app_dies_during_settle(tmp_path, capsys):
    fake = _fake_app(
        tmp_path,
        _RECORD_PID
        + _WRITE_THEME_ICON
        + "import time, sys\ntime.sleep(0.5)\nsys.exit(0)\n",
    )
    pid_file = tmp_path / "pid"

    with _monkeypatch_env(SMOKE_TEST_PID_FILE=str(pid_file)):
        returncode = smoke_check.main(
            ["--exe", str(fake), "--startup-timeout", "5", "--settle", "2"]
        )

    captured = capsys.readouterr()
    final_line = captured.out.strip().splitlines()[-1]
    assert returncode == 1
    assert "settle" in final_line


def test_child_environment_is_isolated(tmp_path, monkeypatch, capsys):
    env_file = tmp_path / "child_env.json"
    fake = _fake_app(
        tmp_path,
        _RECORD_PID
        + f"""
import json, os
with open({str(env_file)!r}, "w") as _f:
    json.dump(dict(os.environ), _f)
"""
        + _WRITE_THEME_ICON
        + "import time\ntime.sleep(3)\n",
    )

    monkeypatch.setenv("PYTHONPATH", "/somewhere/not/real")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    real_home = str(Path.home())
    returncode = smoke_check.main(
        ["--exe", str(fake), "--startup-timeout", "5", "--settle", "1"]
    )

    captured = capsys.readouterr()
    final_line = captured.out.strip().splitlines()[-1]
    assert returncode == 0
    assert final_line.startswith("SMOKE PASS")

    child_env = json.loads(env_file.read_text())
    assert child_env["HOME"] == child_env["USERPROFILE"]
    assert child_env["HOME"] != real_home
    assert Path(child_env["HOME"]).parent == Path(os_tempdir())
    assert "PYTHONPATH" not in child_env
    assert "QT_QPA_PLATFORM" not in child_env
    assert child_env["APPDATA"].startswith(child_env["HOME"])
    assert not Path(child_env["HOME"]).exists()


def os_tempdir() -> str:
    """Return the system temp folder, matching tempfile.mkdtemp()'s parent."""
    import tempfile

    return tempfile.gettempdir()


def test_missing_executable_is_reported(tmp_path, capsys):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    returncode = smoke_check.main(["--dist", str(empty_dir)])

    captured = capsys.readouterr()
    final_line = captured.out.strip().splitlines()[-1]
    assert returncode == 1
    assert "not found" in final_line


@pytest.mark.skipif(sys.platform != "darwin", reason="macOS-only code signature check")
def test_rejects_unsigned_app_bundle(tmp_path, capsys):
    macos_dir = tmp_path / "GDTF Comparer.app" / "Contents" / "MacOS"
    macos_dir.mkdir(parents=True)
    fake = macos_dir / "GDTF Comparer"
    fake.write_text(f"#!{sys.executable}\n" + _RECORD_PID + "import time\ntime.sleep(5)\n")
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    pid_file = tmp_path / "pid"

    with _monkeypatch_env(SMOKE_TEST_PID_FILE=str(pid_file)):
        returncode = smoke_check.main(["--dist", str(tmp_path)])

    captured = capsys.readouterr()
    final_line = captured.out.strip().splitlines()[-1]
    assert returncode == 1
    assert "invalid code signature" in final_line
    assert not pid_file.exists()


class _monkeypatch_env:
    """Minimal context manager to set/restore env vars without pytest's fixture.

    Used in tests that need the env var set only around a single main() call
    rather than for the whole test (pytest's monkeypatch fixture already
    covers the whole test and is used directly elsewhere in this file).
    """

    def __init__(self, **values: str) -> None:
        self._values = values
        self._previous = {}

    def __enter__(self) -> "_monkeypatch_env":
        for key, value in self._values.items():
            self._previous[key] = os.environ.get(key)
            os.environ[key] = value
        return self

    def __exit__(self, *exc_info) -> None:
        for key, previous in self._previous.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous
