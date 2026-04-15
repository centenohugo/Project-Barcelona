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
import sys
from pathlib import Path

import spacy

PROCESSED_ROOT = Path(__file__).parent / "processed_data" / "sentences"
OUTPUT_NAME = "validated-sentence-separation.txt"


def segment_file(merged_path: Path, nlp: spacy.Language) -> tuple[Path, int]:
    """
    Read merged_path, join all lines into one text, run sentence segmentation,
    write one sentence per line to OUTPUT_NAME in the same directory.

    Returns (output_path, sentence_count).
    """
    raw_lines = merged_path.read_text(encoding="utf-8").splitlines()
    # Join all non-empty lines with a space — treats the file as one speech block.
    joined = " ".join(line.strip() for line in raw_lines if line.strip())

    doc = nlp(joined)

    sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]

    output_path = merged_path.parent / OUTPUT_NAME
    output_path.write_text("\n".join(sentences) + "\n", encoding="utf-8")

    return output_path, len(sentences)


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
        output_path, n_sentences = segment_file(path, nlp)
        rel = path.relative_to(Path(__file__).parent)
        print(f"  {rel}  ->  {output_path.name}  ({n_sentences} sentences)")

    print(f"\nDone. Processed {len(paths)} file(s).")


if __name__ == "__main__":
    main()
