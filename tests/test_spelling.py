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
        "behavior": "behaviour",
        "honor": "honour",
        "labor": "labour",
        "neighbor": "neighbour",
        "humor": "humour",
        "traveling": "travelling",
        "canceled": "cancelled",
        "dialog": "dialogue",
        "catalog": "catalogue",
        "gray": "grey",
    }


def test_apply_normalises_complete_words_for_british_english() -> None:
    text = (
        "I realize the color at the center is my favorite; analyze its defense and license it. "
        "His behavior brings honor to the labor next door; the neighbor's humor made traveling "
        "after a canceled dialog about the gray catalog pleasant."
    )

    assert apply(text, "en-GB") == (
        "I realise the colour at the centre is my favourite; analyse its defence and license it. "
        "His behaviour brings honour to the labour next door; the neighbour's humour made travelling "
        "after a cancelled dialogue about the grey catalogue pleasant."
    )


def test_apply_does_not_normalise_embedded_or_hyphenated_tokens() -> None:
    text = "realizer discolored color-code organize-centre favourite"

    assert apply(text, "en-GB") == text


def test_apply_preserves_supported_matched_casing() -> None:
    assert (
        apply(
            "behavior Behavior BEHAVIOR canceled Canceled CANCELED catalog Catalog CATALOG",
            "en-GB",
        )
        == "behaviour Behaviour BEHAVIOUR cancelled Cancelled CANCELLED catalogue Catalogue CATALOGUE"
    )


def test_apply_leaves_other_variants_unchanged() -> None:
    text = "Realize the color."

    assert apply(text, "en-US") == text
    assert apply(text, None) == text
    assert apply(text, "en-AU") == text
