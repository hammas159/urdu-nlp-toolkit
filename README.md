# urdu-nlp-toolkit

[![ci](https://github.com/hammas159/urdu-nlp-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/hammas159/urdu-nlp-toolkit/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![dependencies](https://img.shields.io/badge/dependencies-none-success)
![license](https://img.shields.io/badge/license-MIT-green)

**Urdu and Roman Urdu text processing. Pure Python, zero dependencies, no model
downloads.**

```python
from urdunlp import normalize, transliterate_to_urdu, words

normalize("كتاب")                        # 'کتاب'   Arabic kaf -> Urdu keheh
transliterate_to_urdu("main theek hoon") # 'میں ٹھیک ہوں'
words("کیا، واقعی؟", keep_punctuation=True)  # ['کیا', '،', 'واقعی', '؟']
```

---

## Why this exists

Urdu is the national language of a country of 240 million people, and the tooling for
it is close to nonexistent. Every Urdu project starts by rewriting the same four
things badly. This is those four things, written once, with tests.

### The problem nobody handles: the same word has several encodings

Urdu uses a Perso-Arabic script, and text scraped from the web freely mixes Arabic
codepoints with Urdu ones, because most keyboards and many fonts do not distinguish
them:

| Looks like | Arabic codepoint | Urdu codepoint |
|---|---|---|
| ی | `U+064A` ARABIC YEH | `U+06CC` FARSI YEH |
| ک | `U+0643` ARABIC KAF | `U+06A9` KEHEH |
| ہ | `U+0647` ARABIC HEH | `U+06C1` HEH GOAL |

They render identically and compare unequal. Without normalisation, exact match fails,
vocabularies fragment, and every downstream model quietly learns three versions of the
same word.

```python
normalize("كتاب") == normalize("کتاب")   # True. Without it: False.
```

### Roman Urdu, which is what people actually type

Most Pakistanis type Urdu in Latin script — in messages, comments, reviews, support
tickets. It has **no standard orthography**:

```
نہیں  ->  nahi, nahin, nhi, nahee, naheen
ہے    ->  hai, hay, he, h
```

This library does not pretend that is solved. It works in two stages and **tells you
which one answered**:

```python
r = transliterate_with_confidence("mera naam Ali hai")
r.text               # 'میرا نام علی ہے'
r.lexicon_coverage   # 0.5  — half looked up, half guessed by rule
```

A curated lexicon covers the closed-class vocabulary — pronouns, postpositions,
auxiliaries — which is where most tokens in real text actually are, and which rules
cannot disambiguate (`khana` is کھانا *food* or خانہ *compartment*). Longest-match
grapheme rules handle the rest, because no lexicon covers proper nouns. Hiding that
distinction behind a single string would be the dishonest design.

## What it does

| Module | |
|---|---|
| `normalize` | Arabic↔Urdu unification, diacritics, tatweel, zero-width, digits, punctuation. `is_urdu()` script detection. |
| `tokenize` | Sentence splitting on `۔` and `؟`, word tokenisation, merged-compound repair, character n-grams. |
| `translit` | Roman Urdu ↔ Urdu script, with per-token confidence. |
| `stopwords` | 115 function words — **with negation held separately**. |

### Three details that are usually wrong elsewhere

**Urdu punctuation lives inside the Arabic block**, interleaved with the letters. A
range like `؀-ۿ` silently swallows `،` `؟` `۔` into your word tokens. The letter
ranges here skip each punctuation codepoint individually.

**`ھ` (do-chashmi he) marks aspiration**, not a separate consonant — `کھ` is one
sound. Transliterating it as its own letter turns کھانا into `kahana`. It is also a
different codepoint from standalone `ہ`, and confusing the two is the most common
mistake in machine-produced Urdu.

**Negation is not a stopword.** `نہیں` carries the entire meaning of a sentence, and
a stopword list that deletes it inverts every sentiment label. It is kept in a
separate `NEGATION` set and preserved by default:

```python
remove_stopwords(words("یہ اچھا نہیں ہے"))   # ['اچھا', 'نہیں']  — negation survives
```

## Install

```bash
pip install urdu-nlp-toolkit
```

No dependencies, deliberately. This is the layer other Urdu projects sit on, and a
dependency here becomes a dependency of all of them.

## Tests

```bash
pytest
```

**40 tests.** Each encodes a real property of the language rather than a convenient
example, so a failure means the library is wrong about Urdu, not about a fixture.

## Known limits

Stated plainly, because a toolkit that overclaims wastes its users' time:

- **Roman → Urdu is ambiguous by nature.** `sher` is شیر (lion) or شعر (couplet).
  Outside the lexicon it is a best-effort guess, and `lexicon_coverage` tells you how
  much of a given string was guessed.
- **Urdu → Roman is lossy and one-way.** س ص ث all give `s`; the merge cannot be
  undone.
- **Short vowels are inserted heuristically.** Urdu does not write them, so a literal
  mapping gives `jmlh` for جملہ. An `a` between consonants gives `jamalah` — right
  more often than not, wrong sometimes, and disabled with
  `insert_short_vowels=False`.
- **Compound-splitting is a fixed list**, not a model. Deliberately: an aggressive
  splitter does more damage than an incomplete one.
- **No stemmer or lemmatiser.** Urdu morphology needs a lexicon that does not exist
  openly. Use `character_ngrams` as the cheap substitute.

## License

MIT
