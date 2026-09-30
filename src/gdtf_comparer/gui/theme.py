"""qt-material theming that follows the OS light/dark color scheme live.

D-05: apply a qt-material Material-Design reskin rather than the stock Qt
"Fusion" look, satisfying UI-01's "modernized, visually refreshed" bar.
D-06: theme mode follows the OS setting rather than a fixed default, using
PySide6's built-in ``QStyleHints.colorScheme()`` / ``colorSchemeChanged``
signal (no ``darkdetect`` dependency needed -- RESEARCH Assumption A2).
D-07: accent color is Claude's discretion within qt-material's bundled
themes. This module uses the blue pair (``dark_blue.xml`` / ``light_blue.xml``):
blue reads as neutral and stays high-contrast in both modes, and it avoids
the amber/red end of the palette, which lighting/AV operators (this app's
audience) associate with warning or indicator colors on real fixtures and
consoles.
D-08: no custom QSS, fonts or icons are layered on top of qt-material's
defaults -- Phase 1's polish bar is a functional modern baseline, not a
custom visual identity.

Phase 2 D-05: the diff-highlight tint (diff_highlight_color) follows this
same live qt-material theme rather than a hardcoded color, so it reads
correctly in both light and dark mode and across a live OS switch.
"""

import functools
from typing import Optional

from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication

from qt_material import apply_stylesheet, get_theme

LIGHT_THEME = "light_blue.xml"
DARK_THEME = "dark_blue.xml"

#: Dynamic Qt property stashed on the QApplication recording the theme name
#: currently applied, so re-applying the same theme is a no-op (avoids
#: re-apply loops if a palette change echoes back through colorSchemeChanged).
THEME_PROPERTY = "gdtf_comparer_theme"

# The qt-material theme key used for the diff-highlight tint (Phase 2 D-05).
# qt-material already uses this same key for its own alternating-row (0.1
# alpha) and inactive-selection (0.2 alpha) tints -- reusing it keeps the
# highlight visually related to the app's existing accent, not a foreign
# color.
DIFF_HIGHLIGHT_THEME_KEY = "primaryColor"

# Alpha applied to DIFF_HIGHLIGHT_THEME_KEY for the diff-highlight tint
# (Phase 2 D-05). Stronger than qt-material's own 0.1 alternating-row and 0.2
# inactive-selection tints of the same color, so a differing cell is never
# mistaken for either. Contrast computed at planning time: light theme
# #555555 text on the tint is about 4.7:1, dark theme white text about
# 7.8:1 (both comfortably above WCAG AA's 4.5:1 for normal text).
DIFF_HIGHLIGHT_ALPHA = 0.35


def theme_for_scheme(scheme: Qt.ColorScheme) -> str:
    """Map an OS color scheme to a qt-material theme file name.

    Parameters:
        scheme: The OS color scheme reported by QStyleHints.colorScheme().

    Returns:
        DARK_THEME when scheme is Dark; LIGHT_THEME for Light or Unknown
        (e.g. platforms/backends -- such as the offscreen platform -- that
        cannot report a scheme).
    """
    if scheme == Qt.ColorScheme.Dark:
        return DARK_THEME
    return LIGHT_THEME


def apply_theme(app: QApplication, theme: str) -> bool:
    """Apply a qt-material theme to app, unless it is already applied.

    Parameters:
        app: The QApplication to theme.
        theme: A qt-material theme file name (e.g. "dark_blue.xml").

    Returns:
        True if the stylesheet was (re-)applied; False if theme already
        matched the app's current THEME_PROPERTY and nothing was done.
    """
    if app.property(THEME_PROPERTY) == theme:
        return False
    apply_stylesheet(app, theme=theme, invert_secondary=theme.startswith("light_"))
    app.setProperty(THEME_PROPERTY, theme)
    return True


class OsThemeFollower(QObject):
    """Keeps an app's qt-material theme in sync with the OS color scheme.

    Parented to the QApplication it follows so it lives for the app's
    lifetime; install_os_theme() ensures only one follower exists per app.
    """

    def __init__(self, app: QApplication) -> None:
        super().__init__(app)
        self._app = app
        app.styleHints().colorSchemeChanged.connect(self.on_color_scheme_changed)

    @Slot(Qt.ColorScheme)
    def on_color_scheme_changed(self, scheme: Qt.ColorScheme) -> None:
        """Re-theme the app when the OS color scheme changes."""
        apply_theme(self._app, theme_for_scheme(scheme))

    @property
    def current_theme(self) -> Optional[str]:
        """The theme file name currently applied to the followed app, if any."""
        return self._app.property(THEME_PROPERTY)


@functools.lru_cache(maxsize=None)
def _theme_color_hex(theme_name: str, key: str) -> Optional[str]:
    """Return one hex color from a qt-material theme, parsed at most once.

    Parameters:
        theme_name: A qt-material theme file name (e.g. "dark_blue.xml").
        key: A qt-material theme color key (e.g. "primaryColor").

    Returns:
        The hex color string for key, or None if get_theme returns None.

    Cached per (theme_name, key): qt_material.get_theme() re-reads the theme
    XML from disk and writes to os.environ on every call (RESEARCH Pattern 4
    pitfall). QAbstractTableModel.data() is invoked per visible cell on every
    repaint, so this lookup must never run there -- MainWindow calls
    diff_highlight_color() once per theme change instead, and the model only
    stores the resulting QBrush.
    """
    theme = get_theme(theme_name, invert_secondary=theme_name.startswith("light_"))
    if theme is None:
        return None
    return theme.get(key)


def diff_highlight_color(theme_name: str) -> QColor:
    """Return the diff-highlight tint QColor for a qt-material theme.

    Parameters:
        theme_name: A qt-material theme file name (e.g. "dark_blue.xml").

    Returns:
        A fresh QColor built from theme_name's DIFF_HIGHLIGHT_THEME_KEY color
        (falling back to LIGHT_THEME's when theme_name's theme cannot be
        read), with alpha set to DIFF_HIGHLIGHT_ALPHA. A new QColor object is
        returned on every call so no caller can mutate a cached color
        (DIFF-01, Phase 2 D-05: follow the qt-material theme, light and dark,
        rather than a hardcoded color -- Claude's discretion per
        02-CONTEXT.md).
    """
    hex_value = _theme_color_hex(theme_name, DIFF_HIGHLIGHT_THEME_KEY)
    if hex_value is None:
        hex_value = _theme_color_hex(LIGHT_THEME, DIFF_HIGHLIGHT_THEME_KEY)
    color = QColor(hex_value)
    color.setAlphaF(DIFF_HIGHLIGHT_ALPHA)
    return color


def current_theme_name(app: QApplication) -> str:
    """Return the qt-material theme file name currently applied to app.

    Parameters:
        app: The QApplication to inspect.

    Returns:
        app's THEME_PROPERTY value when it is a non-empty str (set by
        apply_theme); otherwise theme_for_scheme(app.styleHints().colorScheme())
        so a window built without install_os_theme (as tests do) still gets a
        real theme name.
    """
    property_value = app.property(THEME_PROPERTY)
    if isinstance(property_value, str) and property_value:
        return property_value
    return theme_for_scheme(app.styleHints().colorScheme())


def install_os_theme(app: QApplication) -> OsThemeFollower:
    """Apply the OS-appropriate theme to app and keep it following live.

    Reuses an existing OsThemeFollower child of app if one is already
    installed, so calling this more than once (e.g. across repeated
    create_main_window calls) never creates duplicate signal connections.

    Parameters:
        app: The QApplication to theme.

    Returns:
        The (possibly pre-existing) OsThemeFollower now watching app.
    """
    follower = app.findChild(OsThemeFollower)
    if follower is None:
        follower = OsThemeFollower(app)
    apply_theme(app, theme_for_scheme(app.styleHints().colorScheme()))
    return follower
