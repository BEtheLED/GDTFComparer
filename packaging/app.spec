# PyInstaller spec for GDTF Comparer.
#
# One spec builds the app on both macOS and Windows (D-02, D-04): run the
# same `pyinstaller packaging/app.spec` command on each OS's CI runner (Plan
# 04-02) or locally (this plan, macOS only). It produces a folder build
# (onedir), never a single-file build, for clean-machine reliability and
# fewer antivirus false alarms (RESEARCH PITFALLS 1 and 3). It is a windowed
# GUI app (no console window). `datas` stays empty: qt-material registers
# its own PyInstaller hook (RESEARCH Pattern 2) that bundles its theme,
# font and icon files automatically, so nothing is hand-listed here. There
# is no paid code signing (D-01) -- only PyInstaller's automatic ad-hoc
# signature on macOS, which is required for the build to launch at all on
# Apple silicon.

import os
import sys
import tomllib

# SPECPATH is injected by PyInstaller: the folder holding this spec file.
# Building REPO_ROOT from it (rather than hardcoding a path, and rather than
# assuming the checkout lives at a fixed location) means this exact command
# works unchanged from any checkout or CI runner (RESEARCH path-conflict
# note: avoids both RESEARCH's "../src" and PATTERNS' "src" assumptions).
REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))

# Must equal the application name (app.create_main_window) and the main
# window title (gui/main_window.py) so the smoke check's window-title and
# executable-path lookups line up with what the frozen app actually shows.
APP_NAME = "GDTF Comparer"

with open(os.path.join(REPO_ROOT, "pyproject.toml"), "rb") as _f:
    APP_VERSION = tomllib.load(_f)["project"]["version"]

a = Analysis(
    [os.path.join(REPO_ROOT, "src", "gdtf_comparer", "app.py")],
    pathex=[os.path.join(REPO_ROOT, "src")],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Stops qt-material's fallback import path from ever pulling a second
    # Qt binding into the build alongside PySide6.
    excludes=["PyQt5", "PyQt6"],
    noarchive=False,
    optimize=0,
)

# PyInstaller 6 shape: no bytecode-encryption argument and no zip-related
# Analysis attributes -- both were removed after PyInstaller 5.
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name=APP_NAME + ".app",
        icon=None,
        bundle_identifier="io.github.betheled.gdtfcomparer",
        version=APP_VERSION,
        info_plist={
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": APP_VERSION,
            "NSHighResolutionCapable": True,
        },
    )
