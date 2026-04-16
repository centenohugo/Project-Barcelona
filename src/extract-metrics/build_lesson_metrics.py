"""
src/extract-metrics/build_lesson_metrics.py

Builds a single combined metrics file per lesson:
  data/processed/{student}/{lesson}/metrics/lesson_metrics.json

Contains:
  grammar  — level /40 + variety /20 + error quality /40, per chunk + aggregate
  fluency  — speed/gaps/fillers/duplicates score 0–100, per sentence + aggregate

Grammar formula (per chunk; skip chunks < GRAMMAR_MIN_WORDS):
  level_score   = richness.level   × 40          (0–40)
  variety_score = richness.variety × 20          (0–20)
  error_score   = (error_quality / 100)  × 40    (0–40)
  chunk total   = sum of above

Fluency metric (per sentence; skip sentences < FLUENCY_MIN_WORDS):
  Existing per-sentence fluency score (0–100) from fluency.json.
  Lesson aggregate = mean over included sentences.

If a source file is missing, affected scores are re-weighted to 100 and marked partial=true.

Reads (all optional, at least one required):
  data/processed/{student}/{lesson}/grammar/grammar_richness.json
  data/processed/{student}/{lesson}/errors/errors.json
  data/processed/{student}/{lesson}/fluency.json

Writes:
  data/processed/{student}/{lesson}/metrics/lesson_metrics.json

Usage:
  python src/extract-metrics/build_lesson_metrics.py                    # all lessons
  python src/extract-metrics/build_lesson_metrics.py Student-1 lesson-1
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
PROC = ROOT / "data" / "processed"
PREP = ROOT / "data" / "preprocessed"

# ── Constants ─────────────────────────────────────────────────────────────────
LEVEL_MAX   = 40
VARIETY_MAX = 20
ERROR_MAX   = 40

GRAMMAR_MIN_WORDS = 10   # skip grammar chunks shorter than this
FLUENCY_MIN_WORDS = 5    # skip fluency sentences shorter than this

SCORE_LABELS = [
    (70, "Rich",     "#15803d"),
    (50, "Moderate", "#d97706"),
    (30, "Basic",    "#ea580c"),
    ( 0, "Sparse",   "#dc2626"),
]

FLUENCY_LABELS = [
    (80, "Fluent",     "#15803d"),
    (60, "Moderate",   "#d97706"),
    (40, "Struggling", "#ea580c"),
    ( 0, "Weak",       "#dc2626"),
]


def _label(score: float | None, table=SCORE_LABELS) -> tuple[str, str]:
    if score is None:
        return "N/A", "#9CA3AF"
    for threshold, label, color in table:
        if round(score) >= threshold:
            return label, color
    return table[-1][1], table[-1][2]


def _mean(vals: list[float]) -> float | None:
    clean = [v for v in vals if v is not None]
    return round(sum(clean) / len(clean), 2) if clean else None


# ── Conversation filter ────────────────────────────────────────────────────────

def _conversation_ranges(student: str, lesson: str) -> list[tuple[int, int]] | None:
    """Returns [(word_start, word_end), ...] for conversation=True paragraphs.
    Uses cumulative word counts from sentences.json.
    Returns None if sentences.json is not found (no filtering applied)."""
    path = PREP / student / lesson / "sentences.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text("utf-8"))
    ranges: list[tuple[int, int]] = []
    cum = 0
    for para in data["paragraphs"]:
        wc = sum(len(s["text"].split()) for s in para["sentences"])
        start, end = cum + 1, cum + wc
        if para.get("conversation_boolean", True):
            ranges.append((start, end))
        cum += wc
    return ranges


def _in_conversation(word_start: int, conv_ranges: list[tuple[int, int]]) -> bool:
    return any(ws <= word_start <= we for ws, we in conv_ranges)


# ═══════════════════════════════════════════════════════════════════════════════
#  GRAMMAR SECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _word_count_from_sentences(para: dict) -> int:
    return sum(len(s["text"].split()) for s in para.get("sentences", []))


def _grammar_chunk_score(richness: dict | None, error_para: dict | None) -> dict:
    has_grammar = richness is not None
    has_errors  = error_para is not None
    partial     = not (has_grammar and has_errors)

    level_raw   = round(richness["level"]   * LEVEL_MAX,   2) if has_grammar else None
    variety_raw = round(richness["variety"] * VARIETY_MAX, 2) if has_grammar else None
    error_raw   = round((error_para["quality_score"] / 100) * ERROR_MAX, 2) if has_errors else None

    if has_grammar and has_errors:
        total = round(level_raw + variety_raw + error_raw, 1)
    elif has_grammar:
        scale       = 100 / (LEVEL_MAX + VARIETY_MAX)
        level_raw   = round(level_raw   * scale, 2)
        variety_raw = round(variety_raw * scale, 2)
        total       = round(level_raw + variety_raw, 1)
    elif has_errors:
        scale     = 100 / ERROR_MAX
        error_raw = round(error_raw * scale, 2)
        total     = round(error_raw, 1)
    else:
        total = None

    score_label, color = _label(total)

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
        "has_grammar":   has_grammar,
        "has_errors":    has_errors,
        "partial":       partial,
        "score":         total,
        "score_label":   score_label,
        "color":         color,
        "level_score":   level_raw,
        "variety_score": variety_raw,
        "error_score":   error_raw,
        "grammar":       grammar_block,
        "errors":        errors_block,
    }


def _build_grammar_section(lesson_dir: Path) -> dict | None:
    grammar_path = lesson_dir / "grammar" / "grammar_richness.json"
    errors_path  = lesson_dir / "errors"  / "errors.json"

    has_grammar = grammar_path.exists()
    has_errors  = errors_path.exists()

    if not has_grammar and not has_errors:
        return None

    grammar_data = json.loads(grammar_path.read_text("utf-8")) if has_grammar else None
    errors_data  = json.loads(errors_path.read_text("utf-8"))  if has_errors  else None

    grammar_paras: dict[int, dict] = {}
    if grammar_data:
        for p in grammar_data["paragraphs"]:
            grammar_paras[p["paragraph_id"]] = p

    error_paras: dict[int, dict] = {}
    if errors_data:
        for p in errors_data["paragraphs"]:
            error_paras[p["paragraph_id"]] = p

    all_ids = sorted(set(grammar_paras) | set(error_paras))
    chunks  = []

    for pid in all_ids:
        gp = grammar_paras.get(pid)
        ep = error_paras.get(pid)

        word_count = ep["word_count"] if ep else _word_count_from_sentences(gp) if gp else 0
        sentence_count = (ep or gp or {}).get("sentence_count", 0)
        label_text     = (gp or ep or {}).get("label", "")

        if word_count < GRAMMAR_MIN_WORDS:
            chunks.append({
                "chunk_id":       pid,
                "label":          label_text,
                "word_count":     word_count,
                "sentence_count": sentence_count,
                "skipped":        True,
                "skip_reason":    f"too short ({word_count}w < {GRAMMAR_MIN_WORDS})",
                "score": None, "score_label": None, "color": None,
                "level_score": None, "variety_score": None, "error_score": None,
                "grammar": None, "errors": None,
                "has_grammar": gp is not None,
                "has_errors":  ep is not None,
                "partial":     True,
            })
            continue

        scored = _grammar_chunk_score(
            richness   = gp["richness"] if gp else None,
            error_para = ep,
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

    included = [c for c in chunks if not c["skipped"]]
    agg_score       = _mean([c["score"] for c in included])
    agg_label, agg_color = _label(agg_score)

    return {
        "has_grammar":    has_grammar,
        "has_errors":     has_errors,
        "partial":        not (has_grammar and has_errors),
        "formula": {
            "level_weight":    LEVEL_MAX,
            "variety_weight":  VARIETY_MAX,
            "error_weight":    ERROR_MAX,
            "min_chunk_words": GRAMMAR_MIN_WORDS,
        },
        "aggregate": {
            "score":           agg_score,
            "score_label":     agg_label,
            "color":           agg_color,
            "level_score":     _mean([c["level_score"]   for c in included]),
            "variety_score":   _mean([c["variety_score"] for c in included]),
            "error_score":     _mean([c["error_score"]   for c in included]),
            "chunks_total":    len(chunks),
            "chunks_included": len(included),
            "chunks_skipped":  len(chunks) - len(included),
            "partial":         not (has_grammar and has_errors),
        },
        "chunks": chunks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  FLUENCY SECTION
# ═══════════════════════════════════════════════════════════════════════════════

def _build_fluency_section(
    lesson_dir: Path,
    conv_ranges: list[tuple[int, int]] | None,
) -> dict | None:
    fluency_path = lesson_dir / "fluency.json"
    if not fluency_path.exists():
        return None

    data = json.loads(fluency_path.read_text("utf-8"))
    all_sents = data["sentences"]

    # Walk sentences tracking cumulative word position; keep only conversation ones
    cum = 0
    conv_sents: list[dict] = []
    for s in all_sents:
        start_word = cum + 1
        cum += s["word_count"]
        if conv_ranges is None or _in_conversation(start_word, conv_ranges):
            conv_sents.append(s)

    # Stats words restricted to conversation paragraphs
    conv_words = [w for s in conv_sents for w in s["words"]]

    # Filter sentences for metric computation (conversation + min length)
    included = [s for s in conv_sents if s["word_count"] >= FLUENCY_MIN_WORDS
                and s["fluency"]["score"] is not None]
    n_skipped = len(all_sents) - len(included)

    # Aggregate scores
    scores  = [s["fluency"]["score"] for s in included]
    agg     = _mean(scores)
    agg_lbl, agg_col = _label(agg, FLUENCY_LABELS)

    # Component means
    components = {}
    for comp in ("speed", "gaps", "fillers", "dups"):
        components[comp] = _mean([s["fluency"]["components"].get(comp) for s in included])

    # Distribution
    dist = {
        "fluent":     sum(1 for s in scores if s >= 80),
        "moderate":   sum(1 for s in scores if 60 <= s < 80),
        "struggling": sum(1 for s in scores if 40 <= s < 60),
        "weak":       sum(1 for s in scores if s < 40),
    }

    # Global stats restricted to conversation words
    n_words   = len(conv_words)
    n_fillers = sum(1 for w in conv_words if w.get("is_filler"))
    filler_types = dict(Counter(
        w["filler_type"] for w in conv_words
        if w.get("is_filler") and w.get("filler_type")
    ).most_common())
    content_speeds = [w["speed"] for w in conv_words
                      if w.get("speed") is not None and not w.get("is_filler")]
    avg_speed_ms = round(sum(content_speeds) / len(content_speeds) * 1000) if content_speeds else None

    gap_means = [s["gaps"]["mean"] for s in conv_sents if s["gaps"].get("mean") is not None]
    avg_gap_ms = round(sum(gap_means) / len(gap_means) * 1000) if gap_means else None

    # Sentence-level rows (only included ones, compact)
    sentence_rows = []
    for s in included:
        fl = s["fluency"]
        sl, sc = _label(fl["score"], FLUENCY_LABELS)
        row = {
            "sentence_id":    s["sentence_id"],
            "text":           s["text"],
            "word_count":     s["word_count"],
            "score":          fl["score"],
            "score_label":    sl,
            "color":          sc,
            "components":     fl["components"],
            "filler_count":   s["fillers"]["count"],
            "filler_rate":    s["fillers"]["rate"],
            "gap_mean_ms":    round(s["gaps"]["mean"] * 1000, 1) if s["gaps"].get("mean") is not None else None,
            "duplicate_count": sum(d["occurrences"] - 1 for d in s.get("duplicates", [])),
            "accuracy_mean":  s["accuracy"].get("mean"),
        }
        sentence_rows.append(row)

    return {
        "formula": {
            "min_sentence_words": FLUENCY_MIN_WORDS,
            "components": {
                "speed":   {"weight": 35, "desc": "articulation speed (sec/letter)"},
                "gaps":    {"weight": 35, "desc": "inter-word pauses"},
                "fillers": {"weight": 15, "desc": "filler / hesitation rate"},
                "dups":    {"weight": 15, "desc": "word / phrase repetitions"},
            },
        },
        "aggregate": {
            "score":               agg,
            "score_label":         agg_lbl,
            "color":               agg_col,
            "components":          components,
            "distribution":        dist,
            "sentences_included":  len(included),
            "sentences_skipped":   n_skipped,
            "sentences_total":     len(all_sents),
            "stats": {
                "total_words":    n_words,
                "filler_count":   n_fillers,
                "filler_rate":    round(n_fillers / n_words, 4) if n_words else 0,
                "filler_types":   filler_types,
                "avg_speed_ms":   avg_speed_ms,
                "avg_gap_ms":     avg_gap_ms,
            },
        },
        "sentences": sentence_rows,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Main processor
# ═══════════════════════════════════════════════════════════════════════════════

def process_lesson(student: str, lesson: str) -> Path | None:
    lesson_dir = PROC / student / lesson
    out_path   = lesson_dir / "metrics" / "lesson_metrics.json"

    conv_ranges = _conversation_ranges(student, lesson)

    grammar_section = _build_grammar_section(lesson_dir)
    fluency_section = _build_fluency_section(lesson_dir, conv_ranges)

    if grammar_section is None and fluency_section is None:
        print(f"  SKIP {student}/{lesson}: no data found")
        return None

    print(f"  {student}/{lesson}  "
          f"grammar={'yes' if grammar_section else 'no'}  "
          f"fluency={'yes' if fluency_section else 'no'}")

    if grammar_section:
        ga = grammar_section["aggregate"]
        print(f"    grammar  score={ga['score']} ({ga['score_label']})  "
              f"chunks={ga['chunks_included']}/{ga['chunks_total']}")
    if fluency_section:
        fa = fluency_section["aggregate"]
        print(f"    fluency  score={fa['score']} ({fa['score_label']})  "
              f"sentences={fa['sentences_included']}/{fa['sentences_total']}")

    output = {
        "student":      student,
        "lesson":       lesson,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "grammar":      grammar_section,
        "fluency":      fluency_section,
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), "utf-8")
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


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        process_all()
    else:
        print("Usage: python src/extract-metrics/build_lesson_metrics.py [student lesson]")
        sys.exit(1)
    print("\nDone.")
