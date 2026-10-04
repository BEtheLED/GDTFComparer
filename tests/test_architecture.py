"""AST-based import-boundary guard (UI-02, D-16, roadmap success criterion 5,
and the Phase-1 local-only privacy prohibition).

Uses ast.parse rather than a text/grep gate so a forbidden module name
appearing only in a comment, docstring or string literal never produces a
false positive, and a real import spread across parentheses/aliases never
produces a false negative.
"""

import ast
from pathlib import Path
from typing import Dict, Iterator, Set, Tuple

PACKAGE_NAME = "gdtf_comparer"
PACKAGE_DIR = Path(__file__).resolve().parents[1] / "src" / PACKAGE_NAME

# The core service surface gui/ is allowed to import from (UI-02). core.errors
# is included even though it may not exist yet in every worktree merge order
# (Plan 01-04 adds it) -- this is an allow-list, not a required-to-exist list.
APPROVED_CORE_SURFACE = {
    "gdtf_comparer.core.comparator",
    "gdtf_comparer.core.models",
    "gdtf_comparer.core.errors",
    # Phase 3 compare-profile store (ATTR-03): a GUI-facing core service,
    # the same way gui/ already calls core.comparator directly.
    "gdtf_comparer.core.profile_repository",
}

NETWORK_MODULE_TOP_LEVELS = {
    "socket",
    "ssl",
    "http",
    "urllib",
    "requests",
    "asyncio",
    "ftplib",
    "smtplib",
    "xmlrpc",
    "websockets",
    "zeroconf",
}

PARSING_LIBRARY_TOP_LEVELS = {"pygdtf", "zipfile", "defusedxml", "xml"}

QT_TOP_LEVELS = {"PySide6", "shiboken6", "qt_material"}

# Built from two string parts so this literal method name never appears in
# this test file -- otherwise a naive text scan of the test suite itself
# would misreport this file as an "unpacks archives" violation.
_UNPACK_ALL_METHOD_NAME = "extract" + "all"


def imported_modules(source: str, module_name: str) -> Set[str]:
    """Return the set of absolute dotted names imported by source.

    Parameters:
        source: Python source text to scan.
        module_name: The dotted module name source would live at, used to
            resolve relative imports (e.g. "from . import x") against their
            containing package.

    Returns:
        One absolute dotted name per imported symbol: "import a.b" yields
        {"a.b"}; "from a.b import c" yields {"a.b.c"}; a relative import is
        resolved against module_name's containing package before the same
        rule is applied.
    """
    tree = ast.parse(source)
    containing_package = module_name.split(".")[:-1]
    found: Set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                up = node.level - 1
                if up <= len(containing_package):
                    base_parts = list(containing_package[: len(containing_package) - up])
                else:
                    base_parts = []
                if node.module:
                    base_parts = base_parts + node.module.split(".")
            else:
                base_parts = node.module.split(".") if node.module else []

            base = ".".join(base_parts)
            for alias in node.names:
                if alias.name == "*":
                    if base:
                        found.add(base)
                elif base:
                    found.add(f"{base}.{alias.name}")
                else:
                    found.add(alias.name)

    return found


def iter_package_modules(package_dir: Path, package_name: str) -> Iterator[Tuple[str, str]]:
    """Yield (dotted_module_name, source_text) for every .py file under package_dir.

    Parameters:
        package_dir: Filesystem directory of the top-level package.
        package_name: The dotted name package_dir corresponds to.
    """
    for path in sorted(package_dir.rglob("*.py")):
        relative_parts = list(path.relative_to(package_dir).with_suffix("").parts)
        if relative_parts and relative_parts[-1] == "__init__":
            relative_parts = relative_parts[:-1]
        dotted = ".".join([package_name, *relative_parts]) if relative_parts else package_name
        yield dotted, path.read_text(encoding="utf-8")


def _top_level(dotted_name: str) -> str:
    """Return the top-level package of a dotted import name ("a.b.c" -> "a")."""
    return dotted_name.split(".", 1)[0]


def _is_within(dotted_name: str, prefix: str) -> bool:
    """Return True if dotted_name is prefix itself or a submodule of it."""
    return dotted_name == prefix or dotted_name.startswith(prefix + ".")


def _scan_subpackage(subpackage: str) -> Dict[str, Set[str]]:
    """Return {module_name: imported_names} for every module under
    gdtf_comparer.<subpackage>."""
    prefix = f"{PACKAGE_NAME}.{subpackage}"
    results: Dict[str, Set[str]] = {}
    for dotted, source in iter_package_modules(PACKAGE_DIR, PACKAGE_NAME):
        if _is_within(dotted, prefix):
            results[dotted] = imported_modules(source, dotted)
    return results


def test_gui_does_not_import_parsing_libraries():
    gui_modules = _scan_subpackage("gui")
    assert len(gui_modules) >= 4, "expected to scan at least 4 gui modules"

    violations = [
        (module_name, imported)
        for module_name, imports in gui_modules.items()
        for imported in imports
        if _top_level(imported) in PARSING_LIBRARY_TOP_LEVELS
    ]

    assert violations == []


def test_gui_uses_only_core_service_surface():
    gui_modules = _scan_subpackage("gui")
    assert len(gui_modules) >= 4, "expected to scan at least 4 gui modules"

    core_prefix = f"{PACKAGE_NAME}.core"
    violations = [
        (module_name, imported)
        for module_name, imports in gui_modules.items()
        for imported in imports
        if _is_within(imported, core_prefix)
        and not any(_is_within(imported, surface) for surface in APPROVED_CORE_SURFACE)
    ]

    assert violations == []


def test_core_is_qt_free():
    core_modules = _scan_subpackage("core")
    assert len(core_modules) >= 4, "expected to scan at least 4 core modules"

    forbidden_prefixes = QT_TOP_LEVELS | {
        f"{PACKAGE_NAME}.gui",
        f"{PACKAGE_NAME}.app",
    }
    violations = [
        (module_name, imported)
        for module_name, imports in core_modules.items()
        for imported in imports
        if any(_is_within(imported, forbidden) for forbidden in forbidden_prefixes)
    ]

    assert violations == []


def test_no_network_modules_in_package():
    all_modules = dict(iter_package_modules(PACKAGE_DIR, PACKAGE_NAME))
    assert len(all_modules) >= 4, "expected to scan at least 4 modules"

    violations = [
        (module_name, imported)
        for module_name, source in all_modules.items()
        for imported in imported_modules(source, module_name)
        if _top_level(imported) in NETWORK_MODULE_TOP_LEVELS
    ]

    assert violations == []


def test_core_never_unpacks_archives_or_uses_temp_dirs():
    all_modules = list(iter_package_modules(PACKAGE_DIR, PACKAGE_NAME))
    assert len(all_modules) >= 4, "expected to scan at least 4 modules"

    core_prefix = f"{PACKAGE_NAME}.core"
    import_violations = []
    unpack_violations = []

    for module_name, source in all_modules:
        if _is_within(module_name, core_prefix):
            for imported in imported_modules(source, module_name):
                if _top_level(imported) in {"tempfile", "shutil"}:
                    import_violations.append((module_name, imported))

        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == _UNPACK_ALL_METHOD_NAME:
                unpack_violations.append(module_name)

    assert import_violations == []
    assert unpack_violations == []


def test_import_checker_detects_violations():
    """Proves the AST scanner is not vacuous -- it must actually flag
    violations on synthetic sources, not just pass because it scanned
    nothing."""
    absolute_import = imported_modules("import pygdtf", "gdtf_comparer.gui.x")
    assert "pygdtf" in absolute_import

    relative_import = imported_modules(
        "from ..core import repository", "gdtf_comparer.gui.x"
    )
    assert "gdtf_comparer.core.repository" in relative_import

    qt_import = imported_modules(
        "from PySide6.QtCore import Qt", "gdtf_comparer.core.y"
    )
    assert "PySide6.QtCore.Qt" in qt_import
