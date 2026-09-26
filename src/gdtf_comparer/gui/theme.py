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
"""

from typing import Optional

from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtWidgets import QApplication

from qt_material import apply_stylesheet

LIGHT_THEME = "light_blue.xml"
DARK_THEME = "dark_blue.xml"

#: Dynamic Qt property stashed on the QApplication recording the theme name
#: currently applied, so re-applying the same theme is a no-op (avoids
#: re-apply loops if a palette change echoes back through colorSchemeChanged).
THEME_PROPERTY = "gdtf_comparer_theme"


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
