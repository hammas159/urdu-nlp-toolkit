"""Tests for urdu-nlp-toolkit.

Each one encodes a real property of Urdu text rather than a convenient example, so a
failure means the library is wrong about the language, not about a fixture.
"""

from __future__ import annotations

import pytest

from urdunlp import (
    character_ngrams,
    fix_spacing,
    is_stopword,
    is_urdu,
    normalize,
    remove_stopwords,
    remove_urls_and_mentions,
    sentences,
    transliterate_to_roman,
    transliterate_to_urdu,
    transliterate_with_confidence,
    words,
)


class TestNormalize:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("كتاب", "کتاب"),  # ARABIC KAF -> KEHEH
            ("يہ", "یہ"),  # ARABIC YEH -> FARSI YEH
            ("کِتاب", "کتاب"),  # diacritics dropped
            ("کـــتاب", "کتاب"),  # tatweel dropped
            ("أحمد", "احمد"),  # hamza above alef
        ],
    )
    def test_variants_collapse_to_one_form(self, raw, expected):
        assert normalize(raw) == expected

    def test_arabic_and_urdu_spellings_become_equal(self):
        """The whole point: the same word must compare equal after normalisation."""
        assert normalize("كتاب") == normalize("کتاب")

    def test_idempotent(self):
        once = normalize("كتاب کِتاب")
        assert normalize(once) == once

    def test_urdu_digits_are_kept_by_default(self):
        """Converting them changes how the text reads, not how it is encoded."""
        assert normalize("۱۲۳") == "۱۲۳"
        assert normalize("۱۲۳", normalize_digits=True) == "123"

    def test_urdu_punctuation_is_kept_by_default(self):
        assert normalize("کیا؟") == "کیا؟"
        assert normalize("کیا؟", normalize_punctuation=True) == "کیا?"

    def test_whitespace_collapses(self):
        assert normalize("  یہ   ایک  جملہ ہے  ") == "یہ ایک جملہ ہے"

    def test_empty(self):
        assert normalize("") == ""


class TestIsUrdu:
    def test_urdu(self):
        assert is_urdu("یہ ایک جملہ ہے")

    def test_english(self):
        assert not is_urdu("this is english")

    def test_numbers_do_not_dilute_the_verdict(self):
        """Counting all characters would make a sentence with a year look less Urdu."""
        assert is_urdu("یہ 2026 کا سال ہے")

    def test_empty_is_not_urdu(self):
        assert not is_urdu("")


class TestTokenize:
    def test_splits_on_urdu_full_stop(self):
        assert len(sentences("میرا نام علی ہے۔ آپ کیسے ہیں؟")) == 2

    def test_urdu_punctuation_is_separated_when_asked(self):
        """Urdu punctuation sits inside the Arabic block, so a naive letter range
        swallows it."""
        assert words("کیا، واقعی؟", keep_punctuation=True) == ["کیا", "،", "واقعی", "؟"]

    def test_punctuation_is_dropped_by_default(self):
        assert words("کیا، واقعی؟") == ["کیا", "واقعی"]

    def test_mixed_script(self):
        assert words("Urdu اور English") == ["Urdu", "اور", "English"]

    def test_merged_compound_is_split(self):
        assert fix_spacing("اس نے کام کردیا") == "اس نے کام کر دیا"

    def test_merge_does_not_fire_on_a_substring(self):
        """An aggressive splitter does more damage than an incomplete one."""
        assert fix_spacing("کردیانہ") == "کردیانہ"

    def test_ngrams_are_padded(self):
        assert character_ngrams("کتاب", 3)[0].startswith("<")

    def test_ngram_shorter_than_n(self):
        assert character_ngrams("کا", 5) == ["<کا>"]


class TestStopwords:
    def test_function_words_are_stopwords(self):
        assert is_stopword("کا") and is_stopword("ہے")

    def test_content_words_are_not(self):
        assert not is_stopword("کتاب")

    def test_negation_survives_by_default(self):
        """A stopword list that deletes نہیں inverts every sentiment label."""
        assert "نہیں" in remove_stopwords(words("یہ اچھا نہیں ہے"))

    def test_negation_can_be_removed_explicitly(self):
        assert "نہیں" not in remove_stopwords(
            words("یہ اچھا نہیں ہے"), include_negation=True
        )


class TestTransliteration:
    @pytest.mark.parametrize(
        ("roman", "urdu"),
        [
            ("main theek hoon", "میں ٹھیک ہوں"),
            ("aap kaise hain", "آپ کیسے ہیں"),
            ("bohat shukriya", "بہت شکریہ"),
            ("yeh bohat acha kaam hai", "یہ بہت اچھا کام ہے"),
        ],
    )
    def test_common_phrases_use_the_lexicon(self, roman, urdu):
        assert transliterate_to_urdu(roman) == urdu

    def test_spelling_variants_reach_the_same_word(self):
        """Roman Urdu has no standard orthography; the lexicon absorbs the variation."""
        forms = {transliterate_to_urdu(w) for w in ("nahi", "nahin", "nhi", "naheen")}
        assert forms == {"نہیں"}

    def test_unknown_words_fall_back_to_rules(self):
        result = transliterate_with_confidence("Hammas")
        assert result.sources[0][1] == "rules"
        assert result.text

    def test_coverage_is_reported_honestly(self):
        """Callers must be able to tell a lookup from a guess."""
        assert transliterate_with_confidence("main theek hoon").lexicon_coverage == 1.0
        assert transliterate_with_confidence("Zzzq Xylo").lexicon_coverage == 0.0

    def test_digits_are_not_glued_to_the_previous_word(self):
        assert transliterate_to_urdu("main 25 saal ka hoon") == "میں 25 سال کا ہوں"

    def test_aspiration_does_not_take_a_vowel(self):
        """ھ marks aspiration on the letter before it - کھ is one sound, not two."""
        assert transliterate_to_roman("کھانا") == "khana"

    def test_short_vowels_are_inserted_between_consonants(self):
        """Urdu does not write short vowels, so a literal mapping gives jmlh."""
        assert transliterate_to_roman("جملہ") != transliterate_to_roman(
            "جملہ", insert_short_vowels=False
        )

    def test_roman_output_is_ascii(self):
        assert transliterate_to_roman("میرا نام علی ہے").isascii()


class TestCleaning:
    def test_urls_and_handles_are_removed(self):
        assert remove_urls_and_mentions("دیکھیں https://x.com/a @user #tag") == "دیکھیں"


class TestRoundTrip:
    def test_normalising_a_transliteration_is_stable(self):
        urdu = transliterate_to_urdu("main theek hoon")
        assert normalize(urdu) == urdu
