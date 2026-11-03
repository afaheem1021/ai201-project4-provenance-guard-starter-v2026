"""Transparent style heuristics, independent of the language-model signal."""

import re
import statistics
import unicodedata

import config


def sentences(text: str) -> list[str]:
    """Approximate sentence boundaries; abbreviations can split incorrectly."""
    return [p for p in re.split(r"(?<=[.!?])\s+", text.strip()) if p.strip()]


def words(text: str) -> list[str]:
    """Unicode words, case folded; this is not language-specific segmentation."""
    return re.findall(r"[^\W_]+(?:['’][^\W_]+)*", text.casefold())


def sentence_length_spread(text: str) -> float:
    """Population standard deviation / mean word count; 0 for <2 sentences."""
    lengths = [len(words(s)) for s in sentences(text) if words(s)]
    if len(lengths) < 2:
        return 0.0
    return statistics.pstdev(lengths) / statistics.mean(lengths)


def type_token_ratio(text: str) -> float:
    tokens = words(text)
    return len(set(tokens)) / len(tokens) if tokens else 0.0


def punctuation_density(text: str) -> float:
    """Unicode punctuation count / all characters, including whitespace."""
    return sum(unicodedata.category(c).startswith("P") for c in text) / len(text) if text else 0.0


def style_signal(text: str) -> float:
    """Higher = more AI-like shape; insufficient style evidence is neutral."""
    if len(words(text)) < config.STYLE_MIN_WORDS or sum(bool(words(s)) for s in sentences(text)) < 2:
        return 0.5
    regularity = 1 - min(sentence_length_spread(text), 1.0)
    repetition = 1 - type_token_ratio(text)
    sparse_punctuation = 1 - min(punctuation_density(text) / config.STYLE_PUNCTUATION_SCALE, 1.0)
    return round(config.STYLE_WEIGHT_SPREAD * regularity
                 + config.STYLE_WEIGHT_VOCAB * repetition
                 + config.STYLE_WEIGHT_PUNCTUATION * sparse_punctuation, 4)


if __name__ == "__main__":
    import sys
    text = " ".join(sys.argv[1:]) or "The system works well. It handles most cases correctly and provides good results. Users generally find it easy to use and understand."
    for measure in (sentence_length_spread, type_token_ratio, punctuation_density, style_signal):
        print(f"{measure.__name__:25} {measure(text):.4f}")
