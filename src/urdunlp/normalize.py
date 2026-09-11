"""Urdu text normalisation.

Urdu is written in a Perso-Arabic script, and the same word routinely appears in
several byte sequences that look identical on screen. Text scraped from the web mixes
Arabic codepoints with Urdu ones, because most keyboards and many fonts do not
distinguish them:

    ي  U+064A  ARABIC YEH        vs  ی  U+06CC  FARSI YEH
    ك  U+0643  ARABIC KAF        vs  ک  U+06A9  KEHEH
    ه  U+0647  ARABIC HEH        vs  ہ  U+06C1  HEH GOAL

Without normalisation these are different strings, so exact match fails, vocabularies
fragment, and every downstream model silently learns three versions of the same word.
This module is the first thing any Urdu pipeline needs and the piece most often
missing.

Every transformation here is reversible in meaning, not in bytes: normalisation is
lossy on purpose, because the distinctions it removes carry no information in Urdu.
"""

from __future__ import annotations

import re
import unicodedata

# --- Character-level equivalences ------------------------------------------------
# Arabic codepoint -> the Urdu one that is actually correct.
ARABIC_TO_URDU = {
    "ي": "ی",  # ARABIC YEH        -> FARSI YEH
    "ى": "ی",  # ALEF MAKSURA      -> FARSI YEH
    "ك": "ک",  # ARABIC KAF        -> KEHEH
    "ګ": "گ",  # GAF WITH RING     -> GAF
    "ة": "ۃ",  # TEH MARBUTA       -> TEH MARBUTA GOAL
    "أ": "ا",  # ALEF WITH HAMZA ABOVE -> ALEF
    "إ": "ا",  # ALEF WITH HAMZA BELOW -> ALEF
    "آ": "آ",  # ALEF WITH MADDA is a real Urdu letter; kept
    "ؤ": "ؤ",  # WAW WITH HAMZA is real; kept
    "ۀ": "ۂ",  # HEH WITH YEH ABOVE -> HEH GOAL WITH HAMZA ABOVE
}

# Digits. Urdu uses Extended Arabic-Indic (U+06F0), Arabic uses U+0660. Both occur.
ARABIC_INDIC_DIGITS = {chr(0x0660 + i): str(i) for i in range(10)}
URDU_DIGITS = {chr(0x06F0 + i): str(i) for i in range(10)}

# Punctuation that has an Urdu-specific form.
URDU_PUNCTUATION = {
    "،": ",",  # ARABIC COMMA
    "؛": ";",  # ARABIC SEMICOLON
    "؟": "?",  # ARABIC QUESTION MARK
    "۔": ".",  # URDU FULL STOP
    "٫": ".",  # ARABIC DECIMAL SEPARATOR
    "٬": ",",  # ARABIC THOUSANDS SEPARATOR
}

# Harakat / diacritics. Optional in Urdu, almost always absent, and their presence in
# some copies of a word but not others fragments the vocabulary for no gain.
DIACRITICS = re.compile("[ً-ْٰٓ-ٕٖ-ٟۖ-ۭ]")

# Tatweel stretches a letter for typographic justification. It is never meaningful.
TATWEEL = "ـ"

# Zero-width joiner/non-joiner. ZWNJ is meaningful in Urdu compound words, so it is
# preserved by default and removed only when explicitly requested.
ZWNJ = "‌"
ZWJ = "‍"
_ZERO_WIDTH_OTHER = re.compile("[​‎‏﻿⁠]")

_SPACES = re.compile(r"[ \t  -   　]+")
_NEWLINES = re.compile(r"\s*\n\s*")

_ARABIC_TRANSLATION = str.maketrans(ARABIC_TO_URDU)
_DIGIT_TRANSLATION = str.maketrans({**ARABIC_INDIC_DIGITS, **URDU_DIGITS})
_PUNCT_TRANSLATION = str.maketrans(URDU_PUNCTUATION)


def normalize(
    text: str,
    *,
    unify_characters: bool = True,
    strip_diacritics: bool = True,
    normalize_digits: bool = False,
    normalize_punctuation: bool = False,
    strip_zwnj: bool = False,
    collapse_whitespace: bool = True,
) -> str:
    """Normalise Urdu text.

    The defaults are the ones you almost always want: unify the Arabic/Urdu
    look-alikes and drop diacritics, but keep Urdu digits and Urdu punctuation, since
    converting those changes how the text reads rather than how it is encoded.

    >>> normalize("كتاب") == "کتاب"
    True
    """
    if not text:
        return ""

    # NFC first: composed forms make every table below single-codepoint.
    text = unicodedata.normalize("NFC", text)
    text = _ZERO_WIDTH_OTHER.sub("", text)
    text = text.replace(TATWEEL, "")

    if unify_characters:
        text = text.translate(_ARABIC_TRANSLATION)
    if strip_diacritics:
        text = DIACRITICS.sub("", text)
    if normalize_digits:
        text = text.translate(_DIGIT_TRANSLATION)
    if normalize_punctuation:
        text = text.translate(_PUNCT_TRANSLATION)
    if strip_zwnj:
        text = text.replace(ZWNJ, "").replace(ZWJ, "")

    if collapse_whitespace:
        text = _NEWLINES.sub("\n", text)
        text = _SPACES.sub(" ", text)
        text = text.strip()

    return text


def is_urdu(text: str, *, threshold: float = 0.5) -> bool:
    """Whether the text is predominantly Urdu script.

    Measured over letters only. Counting all characters would make any Urdu sentence
    containing a number or a Latin brand name look less Urdu than it is.
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return False
    urdu = sum(1 for c in letters if "؀" <= c <= "ۿ" or "ﭐ" <= c <= "﷿")
    return urdu / len(letters) >= threshold


def remove_urls_and_mentions(text: str) -> str:
    """Strip URLs, @mentions and #hashtags. Common first step on scraped Urdu text."""
    text = re.sub(r"https?://\S+|www\.\S+", " ", text)
    text = re.sub(r"[@#]\w+", " ", text)
    return _SPACES.sub(" ", text).strip()
