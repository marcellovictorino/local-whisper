"""Tests for British spelling normalisation."""

from local_whisper.spelling import AMERICAN_TO_BRITISH, apply


def test_map_contains_the_curated_american_to_british_pairs() -> None:
    assert AMERICAN_TO_BRITISH == {
        "realize": "realise",
        "color": "colour",
        "organize": "organise",
        "center": "centre",
        "favorite": "favourite",
        "analyze": "analyse",
        "defense": "defence",
        "license": "licence",
    }


def test_apply_normalises_complete_words_for_british_english() -> None:
    text = "I realize the color at the center is my favorite; analyse its defense and license it."

    assert apply(text, "en-GB") == (
        "I realise the colour at the centre is my favourite; analyse its defence and licence it."
    )


def test_apply_does_not_normalise_embedded_or_hyphenated_tokens() -> None:
    text = "realizer discolored color-code organize-centre favourite"

    assert apply(text, "en-GB") == text


def test_apply_preserves_supported_matched_casing() -> None:
    assert apply("realize Realize REALIZE", "en-GB") == "realise Realise REALISE"


def test_apply_leaves_other_variants_unchanged() -> None:
    text = "Realize the color."

    assert apply(text, "en-US") == text
    assert apply(text, None) == text
    assert apply(text, "en-AU") == text
