"""
Segment merged.txt speech into properly separated sentences.

Treats the entire merged.txt as one continuous speech block (joining all
lines), runs spaCy sentence segmentation, and writes one sentence per line
to validated-sentence-separation.txt in the same directory.

Usage
-----
# Process all merged.txt files found under processed_data/sentences/:
    python separate_sentences.py

# Process specific file(s):
    python separate_sentences.py processed_data/sentences/Student-1/lesson-1/merged.txt
"""

import argparse
import re
import sys
from pathlib import Path

import spacy

PROCESSED_ROOT = Path(__file__).parent / "processed_data" / "sentences"
OUTPUT_NAME = "validated-sentence-separation.txt"


def _word_key(word: str) -> str:
    """Lowercase + strip non-alphanumeric — used to compare adjacent words."""
    return re.sub(r"[^\w]", "", word).lower()


def _remove_consecutive_repeats(sentence: str) -> str:
    """
    Collapse runs of repeated words OR phrases into a single occurrence.

    Handles both single-word runs ('to to to buy' → 'to buy') and phrase-level
    repetitions ('so my so my name' → 'so my name', 'I didn't I didn't know'
    → 'I didn't know').  Comparison is case- and punctuation-insensitive; the
    original casing/punctuation of the first occurrence is preserved.
    Multiple passes are applied until the sentence stabilises.
    """
    words = sentence.split()
    if not words:
        return sentence

    changed = True
    while changed:
        changed = False
        new_words: list[str] = []
        i = 0
        while i < len(words):
            max_k = (len(words) - i) // 2
            found = False
            for k in range(max_k, 0, -1):
                phrase_a = [_word_key(w) for w in words[i:i + k]]
                phrase_b = [_word_key(w) for w in words[i + k:i + 2 * k]]
                if phrase_a == phrase_b:
                    new_words.extend(words[i:i + k])   # keep first occurrence
                    i += 2 * k                           # skip duplicate
                    found = True
                    changed = True
                    break
            if not found:
                new_words.append(words[i])
                i += 1
        words = new_words

    return " ".join(words)


def _normalize(text: str) -> str:
    """Lowercase + strip punctuation + collapse whitespace — used only for dedup keying."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def segment_file(merged_path: Path, nlp: spacy.Language) -> tuple[Path, int, int]:
    """
    Read merged_path, join all lines into one text, run sentence segmentation,
    deduplicate (case- and punctuation-insensitive), and write one sentence per
    line to OUTPUT_NAME in the same directory.

    Returns (output_path, sentences_before_dedup, sentences_after_dedup).
    """
    raw_lines = merged_path.read_text(encoding="utf-8").splitlines()
    # Join all non-empty lines with a space — treats the file as one speech block.
    joined = " ".join(line.strip() for line in raw_lines if line.strip())

    doc = nlp(joined)
    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    # Remove consecutive word repetitions within each sentence ('to to to' → 'to').
    sentences = [_remove_consecutive_repeats(s) for s in sentences]

    before = len(sentences)

    # Deduplicate: keep first occurrence of each sentence when normalised.
    seen: set[str] = set()
    unique: list[str] = []
    for sent in sentences:
        key = _normalize(sent)
        if key and key not in seen:
            seen.add(key)
            unique.append(sent)

    output_path = merged_path.parent / OUTPUT_NAME
    output_path.write_text("\n".join(unique) + "\n", encoding="utf-8")

    return output_path, before, len(unique)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files",
        nargs="*",
        metavar="merged.txt",
        help=(
            "Specific merged.txt files to process. "
            "If omitted, all merged.txt files under processed_data/sentences/ are processed."
        ),
    )
    args = parser.parse_args()

    if args.files:
        paths = [Path(f) for f in args.files]
        missing = [p for p in paths if not p.exists()]
        if missing:
            for p in missing:
                print(f"ERROR: file not found: {p}", file=sys.stderr)
            sys.exit(1)
    else:
        paths = sorted(PROCESSED_ROOT.glob("*/*/merged.txt"))

    if not paths:
        print("No merged.txt files found.", file=sys.stderr)
        sys.exit(1)

    print("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")
    print(f"Model ready: {nlp.meta['name']} v{nlp.meta['version']}\n")

    for path in paths:
        output_path, before, after = segment_file(path, nlp)
        rel = path.relative_to(Path(__file__).parent)
        removed = before - after
        print(f"  {rel}  ->  {output_path.name}  ({after} sentences, {removed} duplicates removed)")

    print(f"\nDone. Processed {len(paths)} file(s).")


if __name__ == "__main__":
    main()
