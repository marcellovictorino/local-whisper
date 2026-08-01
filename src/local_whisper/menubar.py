"""macOS menu-bar status item: quick access to config, logs, reload, and docs.

The status item attaches to the *existing* accessory ``NSApplication`` created by
:class:`~local_whisper.overlay.RecordingOverlay` (no second app, no dock icon).
The action logic lives in :class:`MenuActions` — a plain, AppKit-free class — so
each menu item's behaviour is unit-testable without a real status bar. The
``NSObject`` controller that owns the AppKit objects is defined only when AppKit
is importable, mirroring the ``_macos.HAS_APPKIT`` guard used across the codebase.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from pathlib import Path

from local_whisper._macos import HAS_APPKIT
from local_whisper.config import CONFIG_PATH

logger = logging.getLogger("local_whisper")

APP_NAME = "local-whisper"
LOG_PATH = Path.home() / "Library" / "Logs" / "local-whisper.log"
DOCS_URL = "https://github.com/marcellovictorino/local-whisper#usage"


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
    ) -> None:
        self._reload_config = reload_config
        self._quit_app = quit_app
        self._config_path = config_path
        self._log_path = log_path
        self._docs_url = docs_url

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
        NSMenu,
        NSMenuItem,
        NSObject,
        NSStatusBar,
        NSVariableStatusItemLength,
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
            status_item = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
            status_item.button().setTitle_("🎙")
            status_item.setMenu_(self._build_menu())
            self._status_item = status_item  # strong ref keeps the item on the bar

        @objc.python_method
        def _build_menu(self) -> NSMenu:
            menu = NSMenu.alloc().init()

            header = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(APP_NAME, None, "")
            header.setEnabled_(False)
            menu.addItem_(header)
            menu.addItem_(NSMenuItem.separatorItem())

            for title, selector in (
                ("Edit config…", "editConfig:"),
                ("Open logs", "openLogs:"),
                ("Reload config", "reloadConfig:"),
                ("How-to / Docs", "openDocs:"),
            ):
                item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, selector, "")
                item.setTarget_(self)
                menu.addItem_(item)

            menu.addItem_(NSMenuItem.separatorItem())
            quit_item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("Quit", "quitApp:", "q")
            quit_item.setTarget_(self)
            menu.addItem_(quit_item)
            return menu

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


def install(reload_config: Callable[[], None], quit_app: Callable[[], None]) -> object | None:
    """Attach the menu-bar status item to the running NSApplication.

    Must be called on the main thread once ``NSApplication.sharedApplication()``
    exists. Returns the controller (retain it for the app's lifetime) or ``None``
    when AppKit is unavailable, e.g. on headless CI.
    """
    if not HAS_APPKIT:
        logger.debug("AppKit unavailable — skipping menu-bar status item.")
        return None
    controller = _MenuBarController.alloc().init()
    controller.setup(MenuActions(reload_config=reload_config, quit_app=quit_app))
    return controller
