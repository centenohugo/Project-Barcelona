"""
src/extract-metrics/build_grammar_metrics.py

Combines grammar richness + error quality into a single per-chunk grammar score.

Formula (per chunk; chunks with < MIN_WORDS words are skipped):
  level_score   = richness.level   × 40          (0–40)
  variety_score = richness.variety × 20          (0–20)
  error_score   = (error_quality_score/100) × 40 (0–40)
  total         = level_score + variety_score + error_score   → 0–100

When one source is missing the weights are re-scaled so the total still reaches 100
and the chunk is flagged partial=True.

Reads (both optional):
  data/processed/{student}/{lesson}/grammar/grammar_richness.json
  data/processed/{student}/{lesson}/errors/errors.json

Writes:
  data/processed/{student}/{lesson}/metrics/grammar_metrics.json

Usage:
  python src/extract-metrics/build_grammar_metrics.py                    # all lessons
  python src/extract-metrics/build_grammar_metrics.py Student-1 lesson-2
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
PROC = ROOT / "data" / "processed"

# ── Formula constants ─────────────────────────────────────────────────────────
LEVEL_MAX   = 40
VARIETY_MAX = 20
ERROR_MAX   = 40
MIN_WORDS   = 10          # chunks below this are skipped

SCORE_LABELS = [
    (70, "Rich",     "#15803d"),
    (50, "Moderate", "#d97706"),
    (30, "Basic",    "#ea580c"),
    ( 0, "Sparse",   "#dc2626"),
]


def _score_label(score: float | None) -> tuple[str, str]:
    if score is None:
        return "N/A", "#9CA3AF"
    for threshold, label, color in SCORE_LABELS:
        if round(score) >= threshold:
            return label, color
    return "Sparse", "#dc2626"


def _word_count_from_sentences(para: dict) -> int:
    """Count words by summing tokens in sentence texts (grammar_richness paragraphs)."""
    return sum(len(s["text"].split()) for s in para.get("sentences", []))


# ── Per-chunk score computation ───────────────────────────────────────────────

def _chunk_score(
    richness: dict | None,
    error_para: dict | None,
    word_count: int,
) -> dict:
    """
    Returns the scored dict for one chunk.
    richness   — richness sub-dict from grammar_richness paragraph (or None)
    error_para — paragraph entry from errors.json (or None)
    """
    has_grammar = richness is not None
    has_errors  = error_para is not None
    partial     = not (has_grammar and has_errors)

    # Raw component scores (None when source missing)
    level_raw   = round(richness["level"]   * LEVEL_MAX,   2) if has_grammar else None
    variety_raw = round(richness["variety"] * VARIETY_MAX, 2) if has_grammar else None
    error_raw   = round((error_para["quality_score"] / 100) * ERROR_MAX, 2) if has_errors else None

    # Re-scale if one source is missing so total stays in 0–100
    if has_grammar and has_errors:
        total = round(level_raw + variety_raw + error_raw, 1)
        scale = 1.0
    elif has_grammar:
        # Grammar only (level+variety = 60 max) → scale to 100
        scale     = 100 / (LEVEL_MAX + VARIETY_MAX)
        level_raw   = round(level_raw   * scale, 2)
        variety_raw = round(variety_raw * scale, 2)
        total       = round(level_raw + variety_raw, 1)
    elif has_errors:
        # Errors only (40 max) → scale to 100
        scale    = 100 / ERROR_MAX
        error_raw = round(error_raw * scale, 2)
        total     = round(error_raw, 1)
    else:
        total = None

    score_label, color = _score_label(total)

    grammar_block = None
    if has_grammar:
        grammar_block = {
            "richness_score":      richness["score"],
            "level":               round(richness["level"],   4),
            "level_score":         level_raw,
            "variety":             round(richness["variety"], 4),
            "variety_score":       variety_raw,
            "avg_cefr":            richness.get("avg_level_str", ""),
            "n_assigned":          richness.get("n_assigned", 0),
            "density":             round(richness.get("density", 0), 4),
            "distinct_categories": richness.get("distinct_categories", []),
            "dims_present":        richness.get("dims_present", []),
            "level_distribution":  richness.get("level_distribution", {}),
            "top_match":           richness.get("top_match"),
        }

    errors_block = None
    if has_errors:
        errors_block = {
            "error_count":        error_para["error_count"],
            "weighted_error_sum": error_para["weighted_error_sum"],
            "quality_score":      error_para["quality_score"],
            "quality_level":      error_para["quality_level"],
            "error_score":        error_raw,
            "dimension_counts":   error_para.get("dimension_counts", {}),
        }

    return {
        "has_grammar": has_grammar,
        "has_errors":  has_errors,
        "partial":     partial,
        "score":       total,
        "score_label": score_label,
        "color":       color,
        "level_score":   level_raw,
        "variety_score": variety_raw,
        "error_score":   error_raw,
        "grammar":     grammar_block,
        "errors":      errors_block,
    }


# ── Lesson processor ──────────────────────────────────────────────────────────

def process_lesson(student: str, lesson: str) -> Path | None:
    lesson_dir  = PROC / student / lesson
    grammar_path = lesson_dir / "grammar" / "grammar_richness.json"
    errors_path  = lesson_dir / "errors"  / "errors.json"
    out_path     = lesson_dir / "metrics" / "grammar_metrics.json"

    has_grammar = grammar_path.exists()
    has_errors  = errors_path.exists()

    if not has_grammar and not has_errors:
        print(f"  SKIP {student}/{lesson}: no grammar_richness.json or errors.json")
        return None

    print(f"  {student}/{lesson}  grammar={has_grammar}  errors={has_errors}")

    # Load sources
    grammar_data = json.loads(grammar_path.read_text("utf-8")) if has_grammar else None
    errors_data  = json.loads(errors_path.read_text("utf-8"))  if has_errors  else None

    # Index by paragraph_id
    grammar_paras: dict[int, dict] = {}
    if grammar_data:
        for p in grammar_data["paragraphs"]:
            grammar_paras[p["paragraph_id"]] = p

    error_paras: dict[int, dict] = {}
    if errors_data:
        for p in errors_data["paragraphs"]:
            error_paras[p["paragraph_id"]] = p

    all_ids = sorted(set(grammar_paras) | set(error_paras))

    chunks = []
    for pid in all_ids:
        gp = grammar_paras.get(pid)
        ep = error_paras.get(pid)

        # Word count — prefer errors (has explicit word_count), fall back to grammar sentence texts
        if ep:
            word_count = ep["word_count"]
        elif gp:
            word_count = _word_count_from_sentences(gp)
        else:
            word_count = 0

        sentence_count = (ep or gp or {}).get("sentence_count", 0)
        label_text     = (gp or ep or {}).get("label", "")

        if word_count < MIN_WORDS:
            chunks.append({
                "chunk_id":       pid,
                "label":          label_text,
                "word_count":     word_count,
                "sentence_count": sentence_count,
                "skipped":        True,
                "skip_reason":    f"too short ({word_count} words < {MIN_WORDS})",
                "score":          None,
                "score_label":    None,
                "color":          None,
                "level_score":    None,
                "variety_score":  None,
                "error_score":    None,
                "grammar":        None,
                "errors":         None,
                "has_grammar":    gp is not None,
                "has_errors":     ep is not None,
                "partial":        True,
            })
            continue

        scored = _chunk_score(
            richness   = gp["richness"] if gp else None,
            error_para = ep,
            word_count = word_count,
        )

        chunks.append({
            "chunk_id":       pid,
            "label":          label_text,
            "word_count":     word_count,
            "sentence_count": sentence_count,
            "skipped":        False,
            "skip_reason":    None,
            **scored,
        })

        print(f"    chunk {pid:2d}: {word_count:4d}w  "
              f"score={str(scored['score']):>5}  "
              f"level={str(scored['level_score']):>5}  "
              f"variety={str(scored['variety_score']):>5}  "
              f"error={str(scored['error_score']):>5}  "
              + ("(partial)" if scored["partial"] else ""))

    # ── Aggregate (mean over non-skipped chunks) ──────────────────────────────
    included = [c for c in chunks if not c["skipped"]]
    skipped  = [c for c in chunks if c["skipped"]]
    n = len(included)

    def _mean(key: str) -> float | None:
        vals = [c[key] for c in included if c[key] is not None]
        return round(sum(vals) / len(vals), 2) if vals else None

    agg_score        = _mean("score")
    agg_score_label, agg_color = _score_label(agg_score)

    aggregate = {
        "score":       agg_score,
        "score_label": agg_score_label,
        "color":       agg_color,
        "level_score":    _mean("level_score"),
        "variety_score":  _mean("variety_score"),
        "error_score":    _mean("error_score"),
        "chunks_total":   len(chunks),
        "chunks_included": n,
        "chunks_skipped": len(skipped),
        "has_grammar":    has_grammar,
        "has_errors":     has_errors,
        "partial":        not (has_grammar and has_errors),
    }

    output = {
        "student":      student,
        "lesson":       lesson,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "formula": {
            "level_weight":   LEVEL_MAX,
            "variety_weight": VARIETY_MAX,
            "error_weight":   ERROR_MAX,
            "min_chunk_words": MIN_WORDS,
            "note": (
                "When only grammar or only errors data is available, "
                "weights are re-scaled to 100 and chunk is marked partial=true."
            ),
        },
        "aggregate": aggregate,
        "chunks":    chunks,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), "utf-8")
    print(f"    -> {out_path.relative_to(ROOT)}")
    print(f"    Aggregate: score={agg_score} ({agg_score_label}), "
          f"{n}/{len(chunks)} chunks included")
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


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        process_all()
    else:
        print("Usage: python src/extract-metrics/build_grammar_metrics.py [student lesson]")
        sys.exit(1)
    print("\nDone.")
