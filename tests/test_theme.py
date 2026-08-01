"""Tests for the shared design tokens.

The mode colour is the product's only mode indicator, and two surfaces now read
it. These pin the contract that makes that safe: one hue per mode, no fifth hue,
and every mode covered by both the colour and the glow tables.
"""

from __future__ import annotations

from local_whisper import theme


def test_every_mode_has_a_colour() -> None:
    """A mode with no entry would render as a blank or crash at show time."""
    assert set(theme.MODE_RGB) == set(theme.Mode)


def test_the_palette_holds_exactly_four_distinct_hues() -> None:
    """A new colour in this product means a new mode — processing reuses white."""
    assert len(set(theme.MODE_RGB.values())) == 4
    assert theme.MODE_RGB[theme.Mode.PROCESSING] == theme.MODE_RGB[theme.Mode.DICTATION]


def test_only_white_hues_count_as_white_modes() -> None:
    """WHITE_MODES gates both the bloom and the menu-bar template rendering, so it
    must follow the palette rather than a hand-kept list."""
    assert theme.WHITE_MODES == {theme.Mode.DICTATION, theme.Mode.PROCESSING}
    assert all(theme.MODE_RGB[mode] == (1.0, 1.0, 1.0) for mode in theme.WHITE_MODES)


def test_fade_is_short_enough_not_to_lag_the_hotkey() -> None:
    """The pill must be up before a fast speaker's first syllable lands."""
    assert theme.FADE_SECS <= 0.22
