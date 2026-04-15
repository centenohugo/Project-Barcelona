"""
Simple CEFR classifier (A1-C2) for each word on channel 0 (student) of a
Deepgram transcription JSON. Uses cefrpy word-level lookup with hardcoded
whitelists for common contractions and interjections.

Usage:  python analyze_cefr.py <input.json>
Input:  Deepgram JSON with results.channels[0].alternatives[0].words[]
        (each token: word, start, end, confidence).
Output: output/<Student-X>_<lesson-Y>_<NN>.json with
        - words[]: {start, end, word, confidence, cefr_level}
        - stats:   total_words, unique_words, cefr_distribution, unknown_words
"""

import json
import sys
from collections import Counter
from pathlib import Path

from cefrpy import CEFRAnalyzer


LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2", "UNKNOWN"]

# Common interjections and contractions not reliably found in cefrpy
A1_WHITELIST = frozenset({
    "hello", "hi", "hey", "bye", "goodbye", "thanks", "please", "sorry",
    "yeah", "yep", "yes", "nope", "ok", "okay", "uh", "um", "oh", "ah",
    "hmm", "mhm", "wow",
    "don't", "doesn't", "didn't", "can't", "won't", "wouldn't", "couldn't",
    "shouldn't", "isn't", "aren't", "wasn't", "weren't", "haven't", "hasn't",
    "hadn't", "i'm", "you're", "he's", "she's", "it's", "we're", "they're",
    "that's", "there's", "what's", "where's", "who's", "how's",
    "i've", "you've", "we've", "they've",
    "i'd", "you'd", "he'd", "she'd", "we'd", "they'd",
    "i'll", "you'll", "he'll", "she'll", "we'll", "they'll",
    "let's",
})

def _variants(word):
    """Yield the word itself plus contraction-stripped forms."""
    yield word
    if word.endswith("'s"):
        yield word[:-2]
    if "'" in word:
        yield word.split("'", 1)[0]


def classify(analyzer, word):
    """Return the CEFR level for a single word using whitelists then cefrpy."""
    if word.isdigit():
        return "A1"
    for variant in _variants(word):
        if variant in A1_WHITELIST:
            return "A1"
        if variant in A2_WHITELIST:
            return "A2"
        level = analyzer.get_average_word_level_CEFR(variant)
        if level is not None:
            return str(level)
    return "UNKNOWN"


def analyze(input_path: Path) -> dict:
    """Classify every token from channel 0 and aggregate statistics."""
    with input_path.open(encoding="utf-8") as f:
        data = json.load(f)

    # Channel 0 = student speech
    raw_words = data["results"]["channels"][0]["alternatives"][0]["words"]
    analyzer = CEFRAnalyzer()

    words = []
    for w in raw_words:
        token = w.get("word", "").strip()
        if not token:
            continue
        words.append({
            "start": w["start"],
            "end": w["end"],
            "word": token,
            "confidence": w["confidence"],
            "cefr_level": classify(analyzer, token),
        })

    # Aggregate CEFR distribution
    counts = Counter(item["cefr_level"] for item in words)
    total = len(words)
    distribution = {
        lvl: {
            "count": counts.get(lvl, 0),
            "percent": round(100 * counts.get(lvl, 0) / total, 2) if total else 0.0,
        }
        for lvl in LEVELS
    }

    unknown_types = sorted({
        item["word"] for item in words if item["cefr_level"] == "UNKNOWN"
    })

    stats = {
        "total_words": total,
        "unique_words": len({item["word"] for item in words}),
        "cefr_distribution": distribution,
        "unknown_words": unknown_types,
    }

    return {"words": words, "stats": stats}


def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_cefr.py <input.json>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    result = analyze(input_path)

    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    parts = input_path.with_suffix("").parts[-3:]
    output_path = output_dir / ("_".join(parts) + ".json")

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"Wrote {output_path}")
    print(f"  total_words={result['stats']['total_words']}  unique={result['stats']['unique_words']}")
    for lvl, d in result["stats"]["cefr_distribution"].items():
        print(f"  {lvl}: {d['count']} ({d['percent']}%)")


if __name__ == "__main__":
    main()
