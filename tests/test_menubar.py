"""Tests for menubar.MenuActions and config_open_target — the AppKit-free core.

These verify the *why* of each menu item (which path/URL it opens, that reload
reuses the shared handler, that quit runs the clean-shutdown callback) without a
real status bar, so they pass on headless CI where AppKit is absent.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from local_whisper import menubar
from local_whisper.menubar import DOCS_URL, MenuActions, config_open_target, icon_bar_rects


def test_config_open_target_returns_file_when_it_exists(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("")
    assert config_open_target(config) == config


def test_config_open_target_falls_back_to_dir_before_first_run(tmp_path: Path) -> None:
    """A first-run user has no config file yet — open the dir, not a dead path."""
    config = tmp_path / "config.toml"  # never created
    assert config_open_target(config) == tmp_path


def test_edit_config_opens_the_config_path(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("")
    actions = MenuActions(reload_config=MagicMock(), quit_app=MagicMock(), config_path=config)
    with patch("local_whisper.menubar._open_path") as open_path:
        actions.edit_config()
    open_path.assert_called_once_with(config)


def test_open_logs_targets_the_log_path(tmp_path: Path) -> None:
    log = tmp_path / "local-whisper.log"
    actions = MenuActions(reload_config=MagicMock(), quit_app=MagicMock(), log_path=log)
    with patch("local_whisper.menubar._open_path") as open_path:
        actions.open_logs()
    open_path.assert_called_once_with(log)


def test_open_docs_targets_the_usage_url() -> None:
    actions = MenuActions(reload_config=MagicMock(), quit_app=MagicMock())
    with patch("local_whisper.menubar._open_url") as open_url:
        actions.open_docs()
    open_url.assert_called_once_with(DOCS_URL)
    assert DOCS_URL == "https://github.com/marcellovictorino/local-whisper#usage"


def test_reload_config_delegates_to_the_shared_handler() -> None:
    """Reload must reuse the same function SIGHUP invokes, not a fresh path."""
    reload_config = MagicMock()
    actions = MenuActions(reload_config=reload_config, quit_app=MagicMock())
    actions.reload_config()
    reload_config.assert_called_once_with()


def test_quit_triggers_the_clean_shutdown_callback() -> None:
    quit_app = MagicMock()
    actions = MenuActions(reload_config=MagicMock(), quit_app=quit_app)
    actions.quit()
    quit_app.assert_called_once_with()


def test_install_is_a_no_op_without_appkit() -> None:
    """On headless CI (no status bar) install must return None, not raise."""
    with patch.object(menubar, "HAS_APPKIT", False):
        assert menubar.install(reload_config=MagicMock(), quit_app=MagicMock()) is None


def test_whisper_cut_bars_follow_the_tall_short_tallest_short_envelope() -> None:
    """The mark's identity is its height envelope — bar 2 tallest, 1 & 3 shortest."""
    heights = [h for _x, _y, _w, h in icon_bar_rects()]
    assert len(heights) == 4
    tallest = max(heights)
    assert heights.index(tallest) == 2
    ratios = [round(h / tallest, 3) for h in heights]
    assert ratios == [0.87, 0.652, 1.0, 0.565]


def test_status_image_is_a_macos_template() -> None:
    """A template image lets macOS auto-tint the mark to the menu bar's theme."""
    image = menubar.build_status_image()
    if not menubar.HAS_APPKIT:
        assert image is None
        pytest.skip("AppKit unavailable — no image to inspect")
    assert image.isTemplate()
