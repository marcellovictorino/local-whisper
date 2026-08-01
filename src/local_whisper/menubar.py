"""macOS menu-bar status item: status row, Session section, config, logs, reload, and docs.

The status item attaches to the *existing* accessory ``NSApplication`` created by
:class:`~local_whisper.overlay.RecordingOverlay` (no second app, no dock icon).
The action logic lives in :class:`MenuActions` — a plain, AppKit-free class — so
each menu item's behaviour is unit-testable without a real status bar. The
``NSObject`` controller that owns the AppKit objects is defined only when AppKit
is importable, mirroring the ``_macos.HAS_APPKIT`` guard used across the codebase.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from pathlib import Path

from local_whisper import __version__, theme
from local_whisper._macos import HAS_APPKIT, ns_color
from local_whisper.config import CONFIG_PATH

logger = logging.getLogger("local_whisper")

APP_NAME = "local-whisper"
LOG_PATH = Path.home() / "Library" / "Logs" / "local-whisper.log"
DOCS_URL = "https://github.com/marcellovictorino/local-whisper#usage"

# "Whisper Cut" brand mark: four rounded bars forming a stylised W / voice
# signature, drawn into an 18pt template image. Heights are the identity —
# tall, short, TALLEST, short — bottom-aligned so taller bars extend upward.
_ICON_BOX = 18.0
_ICON_BAR_W = 2.4
_ICON_BAR_R = 1.2
_ICON_PAD = 1.5
_ICON_BAR_X = (2.5, 6.4, 10.2, 14.1)
_ICON_BAR_H = (10.0, 7.5, 11.5, 6.5)


def icon_bar_rects() -> list[tuple[float, float, float, float]]:
    """Return each Whisper Cut bar as ``(x, y, w, h)``, bottom-aligned in the box.

    Pure geometry (no AppKit) so the mark's proportions are testable: the
    tall/short/TALLEST/short height envelope is what makes it the brand mark.
    """
    return [(x, _ICON_PAD, _ICON_BAR_W, h) for x, h in zip(_ICON_BAR_X, _ICON_BAR_H, strict=True)]


_DOT_BOX = 9.0
_DOT_D = 7.0


def status_row(mode: str | None) -> tuple[str, str, theme.RGB]:
    """Return ``(label, detail, dot colour)`` for the menu's first row.

    The dot reports daemon *state* (waiting / working / failed), never the mode —
    mode is the icon's job, and duplicating it in a colour here would mean two
    places to keep honest. Idle reads grey rather than green so a glance at an
    open menu distinguishes "waiting" from "recording right now".
    """
    if mode is None:
        return ("Listening", "idle", theme.STATUS_IDLE_RGB)
    if mode == theme.Mode.PROCESSING:
        return ("Transcribing", "working", theme.STATUS_OK_RGB)
    if mode == theme.Mode.ERROR:
        return ("Error", "see logs", theme.MODE_RGB[theme.Mode.ERROR])
    return ("Recording", str(mode), theme.STATUS_OK_RGB)


def _tinted_image(box: float, rgb: theme.RGB | None, draw: Callable[[], None]) -> object | None:
    """Run ``draw`` into a ``box``×``box`` image filled with ``rgb``, or None without AppKit.

    ``rgb=None`` produces a macOS *template* image: drawn in black, then auto-tinted
    by the system to match the menu bar's appearance. Template images discard
    colour, so anything that must keep a hue passes one and is not a template.
    """
    if not HAS_APPKIT:
        return None
    from AppKit import NSColor, NSImage

    image = NSImage.alloc().initWithSize_((box, box))
    image.lockFocus()
    (NSColor.blackColor() if rgb is None else ns_color(rgb)).set()
    draw()
    image.unlockFocus()
    image.setTemplate_(rgb is None)
    return image


def build_status_image(mode: str | None = None) -> object | None:
    """Draw the Whisper Cut mark for the status item, or None without AppKit.

    Static — the mark does not animate; the pill already carries the waveform,
    and a second 30fps redraw in the menu bar would buy nothing.

    Coloured modes fill the mark with that mode's hue, so the menu bar carries the
    same signal as the pill for anyone whose eyes are on their own text rather
    than the top of the screen. Idle *and* the white modes stay template images:
    white paint on a light menu bar is invisible, and white is precisely the
    absence of a tint, so letting macOS pick the ink is the honest rendering.
    """
    if mode is not None and theme.Mode(mode) not in theme.WHITE_MODES:
        rgb = theme.MODE_RGB[theme.Mode(mode)]
    else:
        rgb = None

    def draw() -> None:
        from AppKit import NSBezierPath

        for x, y, w, h in icon_bar_rects():
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(((x, y), (w, h)), _ICON_BAR_R, _ICON_BAR_R).fill()

    return _tinted_image(_ICON_BOX, rgb, draw)


def _build_dot_image(rgb: theme.RGB) -> object | None:
    """Draw the status dot as a small filled circle, or None without AppKit."""

    def draw() -> None:
        from AppKit import NSBezierPath

        inset = (_DOT_BOX - _DOT_D) / 2
        NSBezierPath.bezierPathWithOvalInRect_(((inset, inset), (_DOT_D, _DOT_D))).fill()

    return _tinted_image(_DOT_BOX, rgb, draw)


def config_open_target(config_path: Path = CONFIG_PATH) -> Path:
    """Return the path the "Edit config" action should open.

    Opens the config file when it exists; otherwise its containing directory, so
    a first-run user (config not yet created) still lands somewhere sensible
    instead of on a dead path.
    """
    return config_path if config_path.exists() else config_path.parent


def _open_path(path: Path) -> None:
    """Open a file or directory in its default app via NSWorkspace."""
    from local_whisper._macos import NSWorkspace

    NSWorkspace.sharedWorkspace().openFile_(str(path))


def _open_url(url: str) -> None:
    """Open a URL in the default browser via NSWorkspace."""
    from Foundation import NSURL

    from local_whisper._macos import NSWorkspace

    NSWorkspace.sharedWorkspace().openURL_(NSURL.URLWithString_(url))


class MenuActions:
    """Testable action logic for the menu-bar items — holds no AppKit objects.

    Split from the ``NSObject`` controller so that which path each item opens,
    that "Reload config" delegates to the shared reload handler, and that "Quit"
    runs the clean-shutdown callback are all verifiable without a status bar.
    """

    def __init__(
        self,
        reload_config: Callable[[], None],
        quit_app: Callable[[], None],
        config_path: Path = CONFIG_PATH,
        log_path: Path = LOG_PATH,
        docs_url: str = DOCS_URL,
        session_info: Callable[[], Mapping[str, str]] | None = None,
    ) -> None:
        self._reload_config = reload_config
        self._quit_app = quit_app
        self._config_path = config_path
        self._log_path = log_path
        self._docs_url = docs_url
        self._session_info = session_info

    def session_rows(self) -> list[tuple[str, str]]:
        """Return the Session section as ``(label, detail)`` pairs.

        Caller-supplied rows (model, backend) are read on every menu open, not
        cached: they change under a config reload, and a stale row here would
        misreport which model just ran. The version row is always last and always
        present — the daemon self-updates and runs for weeks without a window, so
        the menu is the only place a user can check which build is actually live.
        """
        rows = [] if self._session_info is None else [(k, str(v)) for k, v in self._session_info().items()]
        rows.append(("Version", __version__))
        return rows

    def edit_config(self) -> None:
        """Open the config TOML (or its dir, if not yet created) in the default editor."""
        _open_path(config_open_target(self._config_path))

    def open_logs(self) -> None:
        """Open the log file in the default viewer."""
        _open_path(self._log_path)

    def open_docs(self) -> None:
        """Open the online usage docs in the default browser."""
        _open_url(self._docs_url)

    def reload_config(self) -> None:
        """Reload config via the same handler the SIGHUP signal invokes."""
        self._reload_config()

    def quit(self) -> None:
        """Trigger a clean shutdown (stop the daemon, then terminate the app)."""
        self._quit_app()


if HAS_APPKIT:
    import objc
    from AppKit import (
        NSAttributedString,
        NSColor,
        NSFont,
        NSFontWeightSemibold,
        NSMenu,
        NSMenuItem,
        NSObject,
        NSStatusBar,
        NSVariableStatusItemLength,
    )
    from Foundation import NSMutableAttributedString

    # macOS menu metrics: 13px rows, 11px section headers (see the design system's
    # type-ui card). Secondary/tertiary inks are the standard AppKit label colours
    # rather than hard-coded greys, so the menu tracks the user's appearance.
    _ROW_PT = 13.0
    _HEADER_PT = 11.0

    def _row_title(label: str, detail: str) -> NSAttributedString:
        """Render ``label`` in primary ink with ``detail`` trailing in secondary."""
        title = NSMutableAttributedString.alloc().initWithString_attributes_(
            label,
            {"NSFont": NSFont.menuFontOfSize_(_ROW_PT), "NSColor": NSColor.labelColor()},
        )
        title.appendAttributedString_(
            NSAttributedString.alloc().initWithString_attributes_(
                f"   {detail}",
                {"NSFont": NSFont.menuFontOfSize_(_ROW_PT), "NSColor": NSColor.secondaryLabelColor()},
            )
        )
        return title

    def _header_title(label: str) -> NSAttributedString:
        """Render a small uppercase section header in tertiary ink."""
        return NSAttributedString.alloc().initWithString_attributes_(
            label.upper(),
            {
                "NSFont": NSFont.systemFontOfSize_weight_(_HEADER_PT, NSFontWeightSemibold),
                "NSColor": NSColor.tertiaryLabelColor(),
            },
        )

    class _MenuBarController(NSObject):
        """Owns the ``NSStatusItem`` + ``NSMenu`` and forwards clicks to MenuActions.

        Retained by :func:`install`'s caller for the app's lifetime — since macOS
        10.10 an ``NSStatusItem`` is dropped from the bar once its owner is
        released, so this controller (which strong-refs the item) must stay alive.
        """

        @objc.python_method
        def setup(self, actions: MenuActions) -> None:
            self._actions = actions
            self._mode: str | None = None
            status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
            button = status_item.button()
            button.setTitle_("")  # drop the placeholder emoji — use the template image
            button.setImage_(build_status_image())
            menu = self._build_menu()
            menu.setDelegate_(self)  # menuNeedsUpdate: refreshes status + session rows
            status_item.setMenu_(menu)
            self._status_item = status_item  # strong ref keeps the item on the bar

        @objc.python_method
        def _build_menu(self) -> NSMenu:
            """Assemble the menu: status first, actions last, Quit at the bottom."""
            menu = NSMenu.alloc().init()

            self._status_row = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("", None, "")
            self._status_row.setEnabled_(False)
            menu.addItem_(self._status_row)

            header = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("", None, "")
            header.setAttributedTitle_(_header_title("Session"))
            header.setEnabled_(False)
            menu.addItem_(NSMenuItem.separatorItem())
            menu.addItem_(header)
            # The section's shape is fixed at build time (model, backend, version);
            # only the values move, so each open retitles these rows in place
            # instead of reallocating menu items.
            self._session_rows = []
            for _label, _detail in self._actions.session_rows():
                row = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("", None, "")
                row.setEnabled_(False)
                menu.addItem_(row)
                self._session_rows.append(row)
            self._refresh_session_rows()

            menu.addItem_(NSMenuItem.separatorItem())
            for title, selector, key in (
                ("Edit config…", "editConfig:", ","),
                ("Reload config", "reloadConfig:", "r"),
                ("Open logs", "openLogs:", ""),
                ("How-to / Docs", "openDocs:", ""),
            ):
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, selector, key)
                item.setTarget_(self)
                menu.addItem_(item)

            menu.addItem_(NSMenuItem.separatorItem())
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(f"Quit {APP_NAME}", "quitApp:", "q")
            quit_item.setTarget_(self)
            menu.addItem_(quit_item)

            self._refresh_status_row()
            return menu

        @objc.python_method
        def _refresh_status_row(self) -> None:
            label, detail, dot = status_row(self._mode)
            self._status_row.setAttributedTitle_(_row_title(label, detail))
            self._status_row.setImage_(_build_dot_image(dot))

        @objc.python_method
        def _refresh_session_rows(self) -> None:
            for row, (label, detail) in zip(self._session_rows, self._actions.session_rows(), strict=True):
                row.setAttributedTitle_(_row_title(label, detail))

        def menuNeedsUpdate_(self, _menu: object) -> None:
            self._refresh_status_row()
            self._refresh_session_rows()

        @objc.python_method
        def set_mode(self, mode: str | None) -> None:
            """Mirror the pill's mode onto the status item. Main thread only.

            Only the icon is redrawn here — this fires on every show and hide,
            while the status row is invisible until the menu opens, and
            ``menuNeedsUpdate_`` refreshes it then.
            """
            self._mode = mode
            self._status_item.button().setImage_(build_status_image(mode))

        def editConfig_(self, _sender: object) -> None:
            self._actions.edit_config()

        def openLogs_(self, _sender: object) -> None:
            self._actions.open_logs()

        def reloadConfig_(self, _sender: object) -> None:
            self._actions.reload_config()

        def openDocs_(self, _sender: object) -> None:
            self._actions.open_docs()

        def quitApp_(self, _sender: object) -> None:
            self._actions.quit()


def install(
    overlay: object,
    reload_config: Callable[[], None],
    quit_app: Callable[[], None],
    session_info: Callable[[], Mapping[str, str]] | None = None,
) -> object | None:
    """Attach the menu-bar status item to the running NSApplication.

    Must be called on the main thread once ``NSApplication.sharedApplication()``
    exists. ``session_info`` supplies the Session section's rows (read on each
    menu open). The item subscribes itself to ``overlay``'s mode changes, so the
    mirroring contract lives here rather than in each caller. Returns the
    controller — **retain it for the app's lifetime**, as macOS drops the status
    item once its owner is released — or ``None`` when AppKit is unavailable,
    e.g. on headless CI.
    """
    if not HAS_APPKIT:
        logger.debug("AppKit unavailable — skipping menu-bar status item.")
        return None
    controller = _MenuBarController.alloc().init()
    controller.setup(MenuActions(reload_config=reload_config, quit_app=quit_app, session_info=session_info))
    overlay.set_mode_listener(controller.set_mode)
    return controller
