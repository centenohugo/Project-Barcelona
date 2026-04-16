"""
src/extract-metrics/build_overall_metrics.py

Builds a per-chunk overall score for each lesson:
  data/processed/{student}/{lesson}/metrics/overall_metrics.json

Formula (per chunk):
  overall_score = content_score * (fluency_score / 100)

Where:
  content_score = grammar_score (0–100)    [future: mean(grammar, vocab)]
  fluency_score = mean of per-chunk sentence fluency scores (0–100)

Per-chunk fluency is derived by mapping fluency.json sentences to grammar
chunks using cumulative word-count alignment (grammar_richness word_start/end ids).

Chunks with < GRAMMAR_MIN_WORDS words are skipped.
Fluency sentences with < FLUENCY_MIN_WORDS words are excluded from the per-chunk mean.

Lesson aggregate = mean(chunk_overall_scores) over non-skipped chunks → 0–100.

Reads (from data/processed/{student}/{lesson}/):
  grammar/grammar_richness.json  (required for chunk definitions)
  errors/errors.json             (optional, for grammar error component)
  fluency.json                   (optional, for fluency component)

Writes:
  data/processed/{student}/{lesson}/metrics/overall_metrics.json

Usage:
  python src/extract-metrics/build_overall_metrics.py                    # all lessons
  python src/extract-metrics/build_overall_metrics.py Student-1 lesson-1
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
PROC = ROOT / "data" / "processed"

# ── Constants ─────────────────────────────────────────────────────────────────
LEVEL_MAX         = 40
VARIETY_MAX       = 20
ERROR_MAX         = 40
GRAMMAR_MIN_WORDS = 10
FLUENCY_MIN_WORDS = 5

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


def _mean(vals: list) -> float | None:
    clean = [v for v in vals if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


# ── Grammar score per chunk (same formula as build_lesson_metrics) ────────────

def _grammar_chunk_score(richness: dict | None, error_para: dict | None) -> tuple[float | None, bool]:
    """Returns (score_0_100, is_partial)."""
    has_g = richness is not None
    has_e = error_para is not None

    level_raw   = richness["level"]   * LEVEL_MAX   if has_g else None
    variety_raw = richness["variety"] * VARIETY_MAX if has_g else None
    error_raw   = (error_para["quality_score"] / 100) * ERROR_MAX if has_e else None

    if has_g and has_e:
        return round(level_raw + variety_raw + error_raw, 1), False
    elif has_g:
        scale = 100 / (LEVEL_MAX + VARIETY_MAX)
        return round((level_raw + variety_raw) * scale, 1), True
    elif has_e:
        scale = 100 / ERROR_MAX
        return round(error_raw * scale, 1), True
    return None, True


# ── Fluency alignment: map sentences → chunks by cumulative word count ────────

def _assign_sentences_to_chunks(
    fluency_sentences: list[dict],
    chunk_ranges: list[tuple[int, int, int]],  # (pid, word_start, word_end)
) -> dict[int, list[dict]]:
    """Assigns each fluency sentence to a chunk using cumulative word position."""
    chunk_sentences: dict[int, list[dict]] = {pid: [] for pid, _, _ in chunk_ranges}
    cum = 0
    for s in fluency_sentences:
        start_word = cum + 1
        cum += s["word_count"]
        assigned = None
        for pid, ws, we in chunk_ranges:
            if ws <= start_word <= we:
                assigned = pid
                break
        if assigned is None:
            assigned = chunk_ranges[-1][0]   # trailing words → last chunk
        chunk_sentences[assigned].append(s)
    return chunk_sentences


def _chunk_fluency_score(sentences: list[dict]) -> tuple[float | None, int]:
    """Mean fluency score for a chunk's sentences (filtered by FLUENCY_MIN_WORDS)."""
    valid = [s for s in sentences
             if s["word_count"] >= FLUENCY_MIN_WORDS and s["fluency"]["score"] is not None]
    score = _mean([s["fluency"]["score"] for s in valid])
    return score, len(valid)


# ── Main processor ─────────────────────────────────────────────────────────────

def process_lesson(student: str, lesson: str) -> Path | None:
    lesson_dir    = PROC / student / lesson
    grammar_path  = lesson_dir / "grammar" / "grammar_richness.json"
    errors_path   = lesson_dir / "errors"  / "errors.json"
    fluency_path  = lesson_dir / "fluency.json"
    out_path      = lesson_dir / "metrics" / "overall_metrics.json"

    if not grammar_path.exists():
        print(f"  SKIP {student}/{lesson}: no grammar_richness.json (needed for chunk boundaries)")
        return None

    grammar_data = json.loads(grammar_path.read_text("utf-8"))
    errors_data  = json.loads(errors_path.read_text("utf-8"))  if errors_path.exists()  else None
    fluency_data = json.loads(fluency_path.read_text("utf-8")) if fluency_path.exists() else None

    has_errors  = errors_data  is not None
    has_fluency = fluency_data is not None

    print(f"  {student}/{lesson}  errors={has_errors}  fluency={has_fluency}")

    # Index error paragraphs
    error_paras: dict[int, dict] = {}
    if errors_data:
        for p in errors_data["paragraphs"]:
            error_paras[p["paragraph_id"]] = p

    # Chunk ranges for fluency alignment
    chunk_ranges = [
        (p["paragraph_id"], p["word_start_id"], p["word_end_id"])
        for p in grammar_data["paragraphs"]
    ]

    # Map fluency sentences to chunks
    chunk_fluency_sents: dict[int, list[dict]] = {}
    lesson_fluency_score: float | None = None
    if fluency_data:
        chunk_fluency_sents = _assign_sentences_to_chunks(
            fluency_data["sentences"], chunk_ranges
        )
        # Lesson-level fallback (for chunks with too few sentences)
        all_valid = [s for s in fluency_data["sentences"]
                     if s["word_count"] >= FLUENCY_MIN_WORDS and s["fluency"]["score"] is not None]
        lesson_fluency_score = _mean([s["fluency"]["score"] for s in all_valid])

    # ── Build per-chunk records ────────────────────────────────────────────────
    chunks = []
    for para in grammar_data["paragraphs"]:
        pid  = para["paragraph_id"]
        gp   = para
        ep   = error_paras.get(pid)
        wc   = sum(len(s["text"].split()) for s in gp.get("sentences", []))
        sc   = gp.get("sentence_count", 0)
        lbl  = gp.get("label", "")

        if wc < GRAMMAR_MIN_WORDS:
            chunks.append({
                "chunk_id":       pid,
                "label":          lbl,
                "word_count":     wc,
                "sentence_count": sc,
                "skipped":        True,
                "skip_reason":    f"too short ({wc}w < {GRAMMAR_MIN_WORDS})",
                "grammar_score":  None,
                "fluency_score":  None,
                "fluency_sentences_included": 0,
                "overall_score":  None,
                "score_label":    None,
                "color":          None,
                "partial":        True,
            })
            continue

        grammar_score, grammar_partial = _grammar_chunk_score(gp["richness"], ep)

        # Per-chunk fluency score (fall back to lesson-level if < 3 valid sentences)
        fluency_score: float | None = None
        fluency_sents_n = 0
        fluency_fallback = False
        if has_fluency:
            chunk_sents   = chunk_fluency_sents.get(pid, [])
            fluency_score, fluency_sents_n = _chunk_fluency_score(chunk_sents)
            if fluency_score is None or fluency_sents_n < 3:
                fluency_score   = lesson_fluency_score
                fluency_fallback = True

        # Overall
        if grammar_score is not None and fluency_score is not None:
            overall = round(grammar_score * (fluency_score / 100), 1)
        else:
            overall = None

        sl, color = _label(overall)

        chunks.append({
            "chunk_id":       pid,
            "label":          lbl,
            "word_count":     wc,
            "sentence_count": sc,
            "skipped":        False,
            "skip_reason":    None,
            "grammar_score":  grammar_score,
            "grammar_partial": grammar_partial,
            "fluency_score":  fluency_score,
            "fluency_sentences_included": fluency_sents_n,
            "fluency_fallback": fluency_fallback,  # True if lesson-level score was used
            "overall_score":  overall,
            "score_label":    sl,
            "color":          color,
            "partial":        grammar_partial or not has_fluency,
        })

        print(f"    chunk {pid:2d}: grammar={str(grammar_score):>5}  "
              f"fluency={str(round(fluency_score, 1) if fluency_score else None):>5}  "
              f"overall={str(overall):>5}"
              + (" [fluency=lesson avg]" if fluency_fallback else ""))

    # ── Aggregate ──────────────────────────────────────────────────────────────
    included = [c for c in chunks if not c["skipped"]]
    overall_scores = [c["overall_score"] for c in included]
    agg_score = _mean(overall_scores)
    agg_label, agg_color = _label(agg_score)

    # Component aggregates (for context)
    agg_grammar_score  = _mean([c["grammar_score"] for c in included])
    agg_fluency_score  = _mean([c["fluency_score"] for c in included]) if has_fluency else None

    aggregate = {
        "score":           agg_score,
        "score_label":     agg_label,
        "color":           agg_color,
        "grammar_score":   agg_grammar_score,
        "fluency_score":   agg_fluency_score,
        "chunks_included": len(included),
        "chunks_skipped":  len(chunks) - len(included),
        "chunks_total":    len(chunks),
        "grammar_partial": not has_errors,
        "fluency_partial": not has_fluency,
        "partial":         not has_errors or not has_fluency,
    }

    output = {
        "student":      student,
        "lesson":       lesson,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "overall_score = grammar_score × (fluency_score / 100). "
            "Future: grammar_score will be mean(grammar, vocab)."
        ),
        "formula": {
            "content_score":    "grammar_score (future: mean of grammar + vocab)",
            "fluency_weight":   "content_score × fluency_score / 100",
            "aggregation":      "mean of chunk overall_scores",
            "grammar_weights":  {
                "level":   LEVEL_MAX,
                "variety": VARIETY_MAX,
                "errors":  ERROR_MAX,
            },
            "min_chunk_words":    GRAMMAR_MIN_WORDS,
            "min_sentence_words": FLUENCY_MIN_WORDS,
        },
        "aggregate": aggregate,
        "chunks":    chunks,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), "utf-8")
    print(f"    Aggregate: overall={agg_score} ({agg_label})  "
          f"[grammar={agg_grammar_score}, fluency={agg_fluency_score}]")
    print(f"    -> {out_path.relative_to(ROOT)}")
    return out_path


def process_all() -> None:
    lessons = sorted(
        (s.name, l.name)
        for s in PROC.iterdir() if s.is_dir()
        for l in s.iterdir()    if l.is_dir()
    )
    if not lessons:
        print(f"No lessons found under {PROC}", file=sys.stderr)
        sys.exit(1)
    for student, lesson in lessons:
        process_lesson(student, lesson)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        process_all()
    else:
        print("Usage: python src/extract-metrics/build_overall_metrics.py [student lesson]")
        sys.exit(1)
    print("\nDone.")
