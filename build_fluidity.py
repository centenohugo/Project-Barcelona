"""
build_fluidity.py — Build a per-lesson fluidity JSON from raw channel-0 words.

For each Student-N/lesson-N:
  1. Load all raw JSON files in file order (01, 02, ...).
  2. Collect channel-0 words from each file (sorted by start time within file).
  3. Join all punctuated_word values into one continuous text.
  4. Run spaCy sentence segmentation on that text (ignoring original line breaks).
  5. Assign a sentence_id (1-based) to every word based on which sentence
     its character offset falls in.
  6. Save to processed_data/fluidity/Student-N/lesson-N/fluidity.json.

Output JSON shape:
  {
    "student": "Student-1",
    "lesson":  "lesson-1",
    "sentences": [
      {"sentence_id": 1, "text": "Hello how are you?"},
      ...
    ],
    "words": [
      {"word": "hello", "start": 2.32, "end": 2.8,
       "confidence": 0.94, "punctuated_word": "Hello?", "sentence_id": 1},
      ...
    ]
  }
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import spacy

RAW_ROOT  = Path(__file__).parent / "raw_data" / "TheEuropaHack_PublicDataSample"
OUT_ROOT  = Path(__file__).parent / "processed_data" / "fluidity"


def collect_words(lesson_dir: Path) -> list[dict]:
    """
    Return channel-0 words from all JSON files in lesson_dir, in file order.
    Within each file words are sorted by start time.
    """
    words: list[dict] = []
    for f in sorted(lesson_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        file_words = data["results"]["channels"][0]["alternatives"][0]["words"]
        file_words = sorted(file_words, key=lambda w: w["start"])
        words.extend(file_words)
    return words


def assign_sentence_ids(words: list[dict], nlp: spacy.Language) -> tuple[list[dict], list[dict]]:
    """
    Build a full text from punctuated_word values, run sentence segmentation,
    and return (sentences_meta, words_with_sentence_id).
    """
    # Build text and precompute each word's start character offset in that text.
    # Words are joined by a single space.
    text_parts: list[str] = [w["punctuated_word"] for w in words]
    full_text = " ".join(text_parts)

    # Cumulative offsets: word i starts at offsets[i]
    offsets: list[int] = []
    pos = 0
    for part in text_parts:
        offsets.append(pos)
        pos += len(part) + 1  # +1 for the space separator

    # Sentence segmentation
    doc = nlp(full_text)
    sents = list(doc.sents)

    # Build sentence metadata (1-based ids)
    sentences_meta = [
        {"sentence_id": i + 1, "text": sent.text.strip()}
        for i, sent in enumerate(sents)
    ]

    # For each word find its sentence by character offset
    # sents[j] covers [sents[j].start_char, sents[j].end_char)
    sent_ranges = [(s.start_char, s.end_char) for s in sents]

    def find_sentence(char_offset: int) -> int:
        """Return 1-based sentence index for a given character offset."""
        for j, (sc, ec) in enumerate(sent_ranges):
            if sc <= char_offset < ec:
                return j + 1
        # Fallback: assign to last sentence (handles trailing space edge cases)
        return len(sent_ranges)

    words_out: list[dict] = []
    for i, word in enumerate(words):
        sid = find_sentence(offsets[i])
        words_out.append({**word, "sentence_id": sid})

    return sentences_meta, words_out


def process_lesson(student: str, lesson: str, nlp: spacy.Language) -> Path:
    lesson_dir = RAW_ROOT / student / lesson
    out_path   = OUT_ROOT / student / lesson / "fluidity.json"

    words = collect_words(lesson_dir)
    sentences_meta, words_out = assign_sentence_ids(words, nlp)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {"student": student, "lesson": lesson,
             "sentences": sentences_meta, "words": words_out},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    return out_path


def main() -> None:
    print("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")
    print(f"Model ready: {nlp.meta['name']} v{nlp.meta['version']}\n")

    lessons = sorted(
        (student.name, lesson.name)
        for student in RAW_ROOT.iterdir() if student.is_dir()
        for lesson  in student.iterdir()  if lesson.is_dir()
    )

    for student, lesson in lessons:
        out = process_lesson(student, lesson, nlp)
        words_total = json.loads(out.read_text(encoding="utf-8"))
        n_words = len(words_total["words"])
        n_sents = len(words_total["sentences"])
        print(f"  {student}/{lesson}: {n_words} words, {n_sents} sentences  ->  {out}")

    print(f"\nDone. Processed {len(lessons)} lesson(s).")


if __name__ == "__main__":
    main()
