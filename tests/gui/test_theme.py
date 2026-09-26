"""Tests for gdtf_comparer.gui.theme: qt-material theme selection and the
OS color-scheme follower (D-05/D-06/D-07)."""

import qt_material
from PySide6.QtCore import Qt

from gdtf_comparer.app import create_main_window
from gdtf_comparer.gui import theme as theme_module
from gdtf_comparer.gui.main_window import MainWindow
from gdtf_comparer.gui.theme import (
    DARK_THEME,
    LIGHT_THEME,
    THEME_PROPERTY,
    OsThemeFollower,
    install_os_theme,
    theme_for_scheme,
)


def test_theme_names_exist_in_qt_material():
    themes = qt_material.list_themes()
    assert LIGHT_THEME in themes
    assert DARK_THEME in themes


def test_dark_scheme_selects_dark_theme():
    assert theme_for_scheme(Qt.ColorScheme.Dark) == DARK_THEME


def test_light_and_unknown_select_light_theme():
    assert theme_for_scheme(Qt.ColorScheme.Light) == LIGHT_THEME
    assert theme_for_scheme(Qt.ColorScheme.Unknown) == LIGHT_THEME


def test_install_applies_stylesheet(qapp):
    install_os_theme(qapp)

    assert qapp.styleSheet() != ""
    assert qapp.property(THEME_PROPERTY) == theme_for_scheme(
        qapp.styleHints().colorScheme()
    )


def test_color_scheme_change_switches_theme(qapp, monkeypatch):
    follower = install_os_theme(qapp)
    # Known baseline so the first "Dark" call below is guaranteed to change
    # the theme, regardless of what earlier tests left qapp in.
    theme_module.apply_theme(qapp, LIGHT_THEME)

    calls = []
    original_apply_stylesheet = theme_module.apply_stylesheet

    def _counting_apply_stylesheet(*args, **kwargs):
        calls.append((args, kwargs))
        return original_apply_stylesheet(*args, **kwargs)

    monkeypatch.setattr(theme_module, "apply_stylesheet", _counting_apply_stylesheet)

    follower.on_color_scheme_changed(Qt.ColorScheme.Dark)
    assert qapp.property(THEME_PROPERTY) == DARK_THEME
    assert len(calls) == 1

    # A second identical call must not re-apply the stylesheet.
    follower.on_color_scheme_changed(Qt.ColorScheme.Dark)
    assert len(calls) == 1

    follower.on_color_scheme_changed(Qt.ColorScheme.Light)
    assert qapp.property(THEME_PROPERTY) == LIGHT_THEME
    assert len(calls) == 2


def test_create_main_window_applies_theme(qapp, qtbot):
    window1 = create_main_window(qapp)
    qtbot.addWidget(window1)
    assert isinstance(window1, MainWindow)
    assert qapp.styleSheet() != ""

    window2 = create_main_window(qapp)
    qtbot.addWidget(window2)

    followers = qapp.findChildren(OsThemeFollower)
    assert len(followers) == 1
