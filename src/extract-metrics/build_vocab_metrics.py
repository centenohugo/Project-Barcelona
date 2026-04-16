"""
src/extract-metrics/build_vocab_metrics.py

Builds per-chunk vocabulary metrics for each lesson.

Formula (per chunk):
  vocab_score = (vocab_level.score - 1) / 5 * 100   → 0–100
  where vocab_level.score is on a 1.0–6.0 CEFR numeric scale (A1=1 … C2=6)

Chunks with conversation_boolean=False are skipped (teacher speech).
Chunks with < MIN_WORDS total words are skipped.
Chunks with < MIN_CONTENT_WORDS content words scored are skipped (unreliable).

Lesson aggregate = mean(chunk_vocab_scores) over non-skipped chunks → 0–100.

Reads:
  src/vocabulary/progress/{student}_{lesson}_progress.json  (required)
  data/preprocessed/{student}/{lesson}/sentences.json        (required for conversation filter + word counts)

Writes:
  data/processed/{student}/{lesson}/vocabulary/vocab_metrics.json

Usage:
  python src/extract-metrics/build_vocab_metrics.py                    # all lessons
  python src/extract-metrics/build_vocab_metrics.py Student-1 lesson-1
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT   = Path(__file__).parent.parent.parent
PROC   = ROOT / "data" / "processed"
PREP   = ROOT / "data" / "preprocessed"
VOCAB  = ROOT / "src" / "vocabulary" / "progress"

# ── Constants ─────────────────────────────────────────────────────────────────
CEFR_MIN         = 1.0   # A1
CEFR_MAX         = 6.0   # C2
MIN_WORDS        = 10    # skip chunks below this word count
MIN_CONTENT_WORDS = 3    # skip chunks with fewer content words scored

SCORE_LABELS = [
    (70, "Rich",     "#15803d"),
    (50, "Moderate", "#d97706"),
    (30, "Basic",    "#ea580c"),
    ( 0, "Sparse",   "#dc2626"),
]


def _label(score: float | None) -> tuple[str, str]:
    if score is None:
        return "N/A", "#9CA3AF"
    for threshold, lbl, color in SCORE_LABELS:
        if round(score) >= threshold:
            return lbl, color
    return "Sparse", "#dc2626"


def _normalize(cefr_score: float) -> float:
    """Convert 1.0–6.0 CEFR numeric score to 0–100."""
    return round((cefr_score - CEFR_MIN) / (CEFR_MAX - CEFR_MIN) * 100, 1)


def _mean(vals: list) -> float | None:
    clean = [v for v in vals if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


# ── Load sentences.json helpers ───────────────────────────────────────────────

def _load_sentences_meta(student: str, lesson: str) -> dict[int, dict] | None:
    """Returns {paragraph_id: {word_count, conversation}} or None if file missing."""
    path = PREP / student / lesson / "sentences.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text("utf-8"))
    result: dict[int, dict] = {}
    for para in data["paragraphs"]:
        pid = para["paragraph_id"]
        wc  = sum(len(s["text"].split()) for s in para["sentences"])
        result[pid] = {
            "word_count":   wc,
            "conversation": para.get("conversation_boolean", True),
        }
    return result


# ── Main processor ─────────────────────────────────────────────────────────────

def process_lesson(student: str, lesson: str) -> Path | None:
    vocab_path = VOCAB / f"{student}_{lesson}_progress.json"
    prep_path  = PREP  / student / lesson / "sentences.json"
    out_path   = PROC  / student / lesson / "vocabulary" / "vocab_metrics.json"

    if not vocab_path.exists():
        print(f"  SKIP {student}/{lesson}: no vocab progress file at {vocab_path.relative_to(ROOT)}")
        return None
    if not prep_path.exists():
        print(f"  SKIP {student}/{lesson}: no sentences.json at {prep_path.relative_to(ROOT)}")
        return None

    vocab_data = json.loads(vocab_path.read_text("utf-8"))
    sent_meta  = _load_sentences_meta(student, lesson)

    tier1  = vocab_data["tier1"]
    chunks_raw = tier1.get("chunks", [])

    print(f"  {student}/{lesson}  chunks={len(chunks_raw)}")

    chunks = []
    for c in chunks_raw:
        pid   = c["paragraph_id"]
        label = c.get("label", "")
        vl    = c["vocab_level"]
        raw_score        = vl["score"]
        cefr_label       = vl.get("cefr_label", "")
        content_words    = vl.get("content_words_scored", 0)

        # Word count and conversation flag from sentences.json
        meta       = (sent_meta or {}).get(pid, {})
        word_count = meta.get("word_count", 0)
        is_conv    = meta.get("conversation", True)

        # Skip teacher speech
        if not is_conv:
            chunks.append({
                "chunk_id":             pid,
                "label":                label,
                "word_count":           word_count,
                "content_words_scored": content_words,
                "skipped":              True,
                "skip_reason":          "teacher speech (conversation_boolean=False)",
                "score":                None,
                "score_label":          None,
                "color":                None,
                "cefr_raw":             raw_score,
                "cefr_label":           cefr_label,
            })
            continue

        # Skip too-short chunks
        if word_count < MIN_WORDS:
            chunks.append({
                "chunk_id":             pid,
                "label":                label,
                "word_count":           word_count,
                "content_words_scored": content_words,
                "skipped":              True,
                "skip_reason":          f"too short ({word_count}w < {MIN_WORDS})",
                "score":                None,
                "score_label":          None,
                "color":                None,
                "cefr_raw":             raw_score,
                "cefr_label":           cefr_label,
            })
            continue

        # Skip unreliable scores (too few content words)
        if content_words < MIN_CONTENT_WORDS:
            chunks.append({
                "chunk_id":             pid,
                "label":                label,
                "word_count":           word_count,
                "content_words_scored": content_words,
                "skipped":              True,
                "skip_reason":          f"too few content words ({content_words} < {MIN_CONTENT_WORDS})",
                "score":                None,
                "score_label":          None,
                "color":                None,
                "cefr_raw":             raw_score,
                "cefr_label":           cefr_label,
            })
            continue

        score = _normalize(raw_score)
        sl, color = _label(score)

        chunks.append({
            "chunk_id":             pid,
            "label":                label,
            "word_count":           word_count,
            "content_words_scored": content_words,
            "skipped":              False,
            "skip_reason":          None,
            "score":                score,
            "score_label":          sl,
            "color":                color,
            "cefr_raw":             raw_score,
            "cefr_label":           cefr_label,
        })

        print(f"    chunk {pid:2d}: cefr_raw={raw_score}  score={score:5.1f}  ({sl})")

    # ── Aggregate ──────────────────────────────────────────────────────────────
    included = [c for c in chunks if not c["skipped"]]
    agg_score = _mean([c["score"] for c in included])
    agg_label, agg_color = _label(agg_score)

    # Lesson-level vocab metrics from tier1
    lesson_vocab_level = tier1["vocab_level"]
    lsi                = tier1.get("lexical_sophistication", {}).get("lsi")
    root_ttr           = tier1.get("lexical_diversity", {}).get("root_ttr")

    aggregate = {
        "score":                agg_score,
        "score_label":          agg_label,
        "color":                agg_color,
        "cefr_raw":             lesson_vocab_level["score"],
        "cefr_label":           lesson_vocab_level.get("cefr_label", ""),
        "content_words_scored": lesson_vocab_level.get("content_words_scored", 0),
        "lexical_sophistication_lsi": lsi,
        "lexical_diversity_root_ttr": root_ttr,
        "chunks_included":      len(included),
        "chunks_skipped":       len(chunks) - len(included),
        "chunks_total":         len(chunks),
    }

    output = {
        "student":      student,
        "lesson":       lesson,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "formula": {
            "normalization":     "vocab_score = (cefr_raw - 1) / 5 * 100",
            "cefr_scale":        "A1=1.0 … C2=6.0",
            "score_range":       "0–100",
            "aggregation":       "mean of chunk vocab_scores (non-skipped)",
            "min_chunk_words":   MIN_WORDS,
            "min_content_words": MIN_CONTENT_WORDS,
            "note": (
                "Chunks with conversation_boolean=False (teacher speech) are excluded. "
                "cefr_raw is the mean CEFR numeric level of content words in the chunk."
            ),
        },
        "aggregate": aggregate,
        "chunks":    chunks,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), "utf-8")
    print(f"    Aggregate: score={agg_score} ({agg_label})  cefr={lesson_vocab_level['score']} ({lesson_vocab_level.get('cefr_label','')})")
    print(f"    -> {out_path.relative_to(ROOT)}")
    return out_path


def process_all() -> None:
    # Discover from vocab progress files (they cover all lessons)
    progress_files = sorted(VOCAB.glob("*_lesson-*_progress.json"))
    if not progress_files:
        print(f"No vocab progress files found under {VOCAB}", file=sys.stderr)
        sys.exit(1)
    for pf in progress_files:
        name = pf.stem  # e.g. Student-1_lesson-1_progress
        # Split on first and last underscore groups
        parts = name.replace("_progress", "").split("_lesson-")
        if len(parts) != 2:
            continue
        student = parts[0]
        lesson  = "lesson-" + parts[1]
        process_lesson(student, lesson)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        process_all()
    else:
        print("Usage: python src/extract-metrics/build_vocab_metrics.py [student lesson]")
        sys.exit(1)
    print("\nDone.")
