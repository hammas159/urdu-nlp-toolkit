"""One Urdu sentence through the whole toolkit.

    python demo.py

Prints what went in and what each stage produced. No arguments, no network.
"""
import sys

if hasattr(sys.stdout, "reconfigure"):  # Urdu will not survive a cp1252 console
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, "src")

from urdunlp.normalize import normalize, remove_urls_and_mentions
from urdunlp.stopwords import remove_stopwords
from urdunlp.tokenize import words
from urdunlp.translit import transliterate_to_roman

# Deliberately messy: Arabic kaf and yeh rather than Urdu, doubled spaces, a URL,
# an English mention.
RAW = "میں  کل  لاہور  سے  آیا  ہوں۔ http://x.co @ali"

stages = []
clean = remove_urls_and_mentions(RAW)
stages.append(("remove_urls_and_mentions", clean))

norm = normalize(clean)
stages.append(("normalize", norm))

toks = words(norm)
stages.append(("words", toks))

content = remove_stopwords(toks)
stages.append(("remove_stopwords", content))

roman = transliterate_to_roman(norm)
stages.append(("transliterate_to_roman", roman))

print("INPUT")
print(f"   {RAW}")
print()
print("OUTPUT")
for name, value in stages:
    shown = " ".join(value) if isinstance(value, list) else value
    print(f"   {name:24} {shown}")
print()
print(f"   {len(toks)} tokens in, {len(content)} content words out "
      f"({len(toks) - len(content)} stopwords removed)")
