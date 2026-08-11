"""British spelling normalisation for completed transcriptions."""

from __future__ import annotations

import re

AMERICAN_TO_BRITISH = {
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

_WORD_PATTERN = re.compile(
    rf"(?<![\w-])({'|'.join(re.escape(word) for word in AMERICAN_TO_BRITISH)})(?![\w-])",
    re.IGNORECASE,
)


def apply(text: str, variant: str | None) -> str:
    """Normalise curated American spellings when the requested variant is British."""
    if variant != "en-GB":
        return text

    def replace(match: re.Match[str]) -> str:
        matched = match.group()
        replacement = AMERICAN_TO_BRITISH[matched.lower()]
        if matched.isupper():
            return replacement.upper()
        if matched[0].isupper() and matched[1:].islower():
            return replacement.capitalize()
        return replacement

    return _WORD_PATTERN.sub(replace, text)
