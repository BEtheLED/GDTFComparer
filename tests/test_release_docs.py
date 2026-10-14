"""Guards PKG-03's first-launch instructions in both user-facing documents."""

from __future__ import annotations

import re
from pathlib import Path
from typing import List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
RELEASE_NOTES = REPO_ROOT / "packaging" / "release-notes.md"
RELEASES_URL = "https://github.com/BEtheLED/GDTFComparer/releases"
LATEST_URL = RELEASES_URL + "/latest"
ISSUES_URL = "https://github.com/BEtheLED/GDTFComparer/issues"
MAC_ZIP = "GDTF-Comparer-macos.zip"
WINDOWS_ZIP = "GDTF-Comparer-windows.zip"
SECTION = "## Download and run (no Python needed)"
MAC = "### On a Mac"
WINDOWS = "### On Windows"
WHY = "### Why do I see a warning?"
SCOPE_PHRASE = "Only do this for a copy you downloaded from"
APP_PATH = "/Applications/GDTF Comparer.app"
DOCS = [README, RELEASE_NOTES]

FORBIDDEN_PHRASES = [
    "spctl",
    "master-disable",
    "disable gatekeeper",
    "turn off gatekeeper",
    "disable smartscreen",
    "turn off smartscreen",
    "turn off smart app control",
    "disable smart app control",
    "disable real-time protection",
    "turn off real-time protection",
    "disable windows defender",
    "turn off windows defender",
    "disable microsoft defender",
    "turn off microsoft defender",
    "set-mppreference",
    "sudo ",
]

REMOVED_MAC_SHORTCUTS = [
    "right-click",
    "right click",
    "control-click",
    "control click",
    "ctrl-click",
    "ctrl click",
]


def _heading_level(heading: str) -> int:
    marker = heading.split(" ", 1)[0]
    return len(marker)


def section(text: str, heading: str) -> str:
    """Return the lines from `heading` up to (not including) the next
    markdown heading of the same or a higher level (fewer '#' characters).

    Fails with a clear message if `heading` is missing from `text`.
    """
    lines = text.splitlines()
    level = _heading_level(heading)
    try:
        start = lines.index(heading)
    except ValueError as exc:
        raise AssertionError(f"heading {heading!r} not found in document") from exc

    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i]
        if line.startswith("#"):
            this_level = len(line) - len(line.lstrip("#"))
            if this_level <= level:
                end = i
                break
    return "\n".join(lines[start:end])


def _read(doc: Path) -> str:
    return doc.read_text(encoding="utf-8")


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_download_section_links_latest_release(doc: Path) -> None:
    text = _read(doc)
    assert SECTION in text
    assert LATEST_URL in text


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_names_both_downloads(doc: Path) -> None:
    text = section(_read(doc), SECTION)
    assert MAC_ZIP in text
    assert WINDOWS_ZIP in text
    assert "Apple silicon" in text


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_mac_steps_use_current_gatekeeper_flow(doc: Path) -> None:
    text = section(_read(doc), MAC)
    assert "Privacy & Security" in text
    assert "Open Anyway" in text
    lowered = text.lower()
    for shortcut in REMOVED_MAC_SHORTCUTS:
        assert shortcut not in lowered, f"stale shortcut {shortcut!r} found in Mac section"


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_mac_damaged_fallback_is_scoped_to_the_app(doc: Path) -> None:
    full_text = _read(doc)
    mac_text = section(full_text, MAC)
    assert "is damaged" in mac_text
    for line in full_text.splitlines():
        if "xattr" in line:
            assert APP_PATH in line, f"xattr line missing scoped app path: {line!r}"


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_windows_steps(doc: Path) -> None:
    text = section(_read(doc), WINDOWS)
    for phrase in (
        "Extract All",
        "_internal",
        "GDTF Comparer.exe",
        "Windows protected your PC",
        "More info",
        "Run anyway",
        "Smart App Control",
        "isn't commonly downloaded",
    ):
        assert phrase in text, f"missing {phrase!r} in Windows section"


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_explains_unsigned_and_scope(doc: Path) -> None:
    text = section(_read(doc), WHY)
    assert re.search(r"(isn't|is not|not) signed", text, re.IGNORECASE)
    scope_index = text.find(SCOPE_PHRASE)
    assert scope_index != -1, "scope sentence not found"
    releases_index = text.find(RELEASES_URL, scope_index)
    assert releases_index != -1, "RELEASES_URL must appear after the scope sentence"


@pytest.mark.parametrize("doc", DOCS, ids=lambda d: d.name)
def test_no_system_wide_security_off_switch(doc: Path) -> None:
    lowered = _read(doc).lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in lowered, f"forbidden phrase {phrase!r} found in {doc.name}"


def test_readme_marks_source_sections_as_developer_only() -> None:
    text = section(_read(README), "## Requirements")
    assert "only needed to run GDTF Comparer from its source code" in text


_MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def test_release_notes_links_are_absolute() -> None:
    text = _read(RELEASE_NOTES)
    targets: List[str] = _MARKDOWN_LINK.findall(text)
    for target in targets:
        assert target.startswith("https://"), f"non-absolute link target: {target!r}"


def test_release_notes_point_to_full_readme_instructions() -> None:
    text = _read(RELEASE_NOTES)
    assert "https://github.com/BEtheLED/GDTFComparer#download-and-run-no-python-needed" in text


def test_release_notes_have_no_developer_setup() -> None:
    text = _read(RELEASE_NOTES)
    assert "pip install" not in text
    assert "venv" not in text
    assert "## Requirements" not in text


_ZIP_NAME = re.compile(r"[\w.-]+\.zip")


def test_docs_agree_on_download_names() -> None:
    for doc in DOCS:
        text = _read(doc)
        assert MAC_ZIP in text
        assert WINDOWS_ZIP in text
        names = set(_ZIP_NAME.findall(text))
        assert names <= {MAC_ZIP, WINDOWS_ZIP}, f"unexpected zip name(s) in {doc.name}: {names - {MAC_ZIP, WINDOWS_ZIP}}"
