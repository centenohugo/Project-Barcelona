"""
Vocabulary progress tracker for CEFR-classified ESL lessons.

Computes per-lesson metrics (Tier 1) and cross-lesson comparison (Tier 2)
from contextual classifier outputs. Maintains a cumulative student history
to track vocabulary growth, retention, and CEFR score trends over time.

Usage:
    python vocab_progress.py <Student-X> <lesson-Y>

Reads:  output/Student-X_lesson-Y_*_contextual.json  (all segments)
        progress/Student-X_history.json               (if exists)
Writes: progress/Student-X_lesson-Y_progress.json
        progress/Student-X_history.json                (updated)
"""

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CEFR_NUM = {"A1": 1.0, "A2": 2.0, "B1": 3.0, "B2": 4.0, "C1": 5.0, "C2": 6.0}
NUM_CEFR = {v: k for k, v in CEFR_NUM.items()}
LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2", "UNKNOWN"]

CONFIDENCE_THRESHOLD = 0.60
INTERESTING_CONFIDENCE = 0.70

# Closed set of English function words — determiners, pronouns, prepositions,
# auxiliary verbs, conjunctions, copulas, basic adverbs.
FUNCTION_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "am",
    "be", "been", "being", "have", "has", "had", "do",
    "does", "did", "will", "would", "shall", "should",
    "may", "might", "can", "could", "must",
    "i", "you", "he", "she", "it", "we", "they",
    "me", "him", "her", "us", "them",
    "my", "your", "his", "its", "our", "their",
    "mine", "yours", "hers", "ours", "theirs",
    "myself", "yourself", "himself", "herself", "itself",
    "ourselves", "themselves",
    "this", "that", "these", "those",
    "and", "but", "or", "nor", "for", "yet", "so",
    "in", "on", "at", "to", "from", "by", "with", "of",
    "about", "up", "out", "off", "over", "under",
    "into", "onto", "upon", "through", "between", "among",
    "before", "after", "during", "since", "until",
    "not", "no", "if", "then", "than",
    "when", "where", "who", "what", "which", "how",
    "there", "here", "very", "just", "also", "too",
    "as", "all", "each", "every", "both", "some", "any",
    "much", "many", "more", "most", "such",
})

OUTPUT_DIR = Path("output")
PROGRESS_DIR = Path("progress")

# ---------------------------------------------------------------------------
# Loading and aggregation
# ---------------------------------------------------------------------------


def load_lesson_outputs(student: str, lesson: str) -> list[dict]:
    """Find and load all contextual output JSONs for a student/lesson, ordered."""
    # Try segment-based outputs first (Deepgram: Student-1_lesson-1_01_contextual.json)
    pattern = f"{student}_{lesson}_*_contextual.json"
    files = sorted(OUTPUT_DIR.glob(pattern))
    # Also check for single paragraphs-format output (Student-1_lesson-1_contextual.json)
    single = OUTPUT_DIR / f"{student}_{lesson}_contextual.json"
    if single.exists() and single not in files:
        files.append(single)
        files.sort()
    if not files:
        print(f"[error] No contextual outputs found for {student}/{lesson} in {OUTPUT_DIR}/",
              file=sys.stderr)
        sys.exit(1)
    outputs = []
    for f in files:
        with f.open(encoding="utf-8") as fh:
            outputs.append(json.load(fh))
    return outputs


def count_expected_segments(student: str, lesson: str) -> int:
    """Count how many input segments exist for a student/lesson.

    Checks for Deepgram segment files first, then falls back to counting
    paragraph outputs (p*_contextual.json) in the output directory.
    """
    data_dir = Path("Data") / student / lesson
    if data_dir.exists():
        segment_files = list(data_dir.glob("*.json"))
        if segment_files:
            return len(segment_files)
    # Fallback: check for a single paragraphs-format output
    single = OUTPUT_DIR / f"{student}_{lesson}_contextual.json"
    if single.exists():
        with single.open(encoding="utf-8") as f:
            data = json.load(f)
        return len(data.get("paragraphs", [1]))
    return 0


def merge_segments(segment_outputs: list[dict]) -> list[dict]:
    """Merge word lists from all segments into a single flat list."""
    all_words = []
    for seg in segment_outputs:
        all_words.extend(seg.get("words", []))
    return all_words


# ---------------------------------------------------------------------------
# Filtering and representative levels
# ---------------------------------------------------------------------------


def is_proper_noun(word_entry: dict) -> bool:
    """Heuristic: a word is likely a proper noun if classified via no_synset/none.

    Only applies when the source field is present — without it we cannot
    distinguish proper nouns from legitimate high-level words.
    """
    source = word_entry.get("source")
    if source is None:
        return False  # no source info → can't determine, assume not proper noun
    if source in ("no_synset", "none"):
        level = word_entry.get("cefr_level", "UNKNOWN")
        if level in ("C1", "C2", "UNKNOWN"):
            return True
    return False


def compute_representative_levels(words: list[dict]) -> dict:
    """
    For each unique word, compute the representative CEFR level as the mode
    of its occurrences (filtered by confidence and proper noun status).

    Returns {word: numeric_level} for words that pass filtering.
    """
    # Group occurrences by lowercased word
    word_occurrences: dict[str, list[float]] = {}
    proper_noun_words: set[str] = set()

    for w in words:
        token = w["word"].lower()
        level_str = w.get("cefr_level", "UNKNOWN")
        confidence = w.get("confidence", 0.0)

        if level_str == "UNKNOWN" or confidence < CONFIDENCE_THRESHOLD:
            continue

        if is_proper_noun(w):
            proper_noun_words.add(token)
            continue

        level_num = CEFR_NUM.get(level_str)
        if level_num is None:
            continue

        word_occurrences.setdefault(token, []).append(level_num)

    # Remove words flagged as proper nouns in ANY occurrence
    for pn in proper_noun_words:
        word_occurrences.pop(pn, None)

    # Compute mode per word; tie-break: lower level
    representative = {}
    for word, levels in word_occurrences.items():
        counter = Counter(levels)
        max_count = max(counter.values())
        # Among levels with max count, pick the lowest (conservative)
        candidates = [lvl for lvl, cnt in counter.items() if cnt == max_count]
        representative[word] = min(candidates)

    return representative


def get_word_level_str(level_num: float) -> str:
    """Convert numeric level back to CEFR string."""
    return NUM_CEFR.get(level_num, "UNKNOWN")


# ---------------------------------------------------------------------------
# Tier 1: Per-lesson metrics
# ---------------------------------------------------------------------------


def compute_vocab_level(representative_levels: dict) -> dict:
    """
    Compute the numerical vocabulary level score from content words only.
    Score = mean of representative levels of unique content words.
    """
    content_levels = [
        lvl for word, lvl in representative_levels.items()
        if word not in FUNCTION_WORDS
    ]

    if not content_levels:
        return {"score": 1.0, "cefr_label": "A1", "content_words_scored": 0}

    score = round(sum(content_levels) / len(content_levels), 1)

    # Map score to CEFR label
    if score < 1.5:
        label = "A1"
    elif score < 2.5:
        label = "A2"
    elif score < 3.5:
        label = "B1"
    elif score < 4.5:
        label = "B2"
    elif score < 5.5:
        label = "C1"
    else:
        label = "C2"

    return {
        "score": score,
        "cefr_label": label,
        "content_words_scored": len(content_levels),
    }


def compute_lexical_sophistication(representative_levels: dict) -> dict:
    """
    Lexical Sophistication Index = proportion of unique content words at B2+.
    """
    content_words = {
        word: lvl for word, lvl in representative_levels.items()
        if word not in FUNCTION_WORDS
    }
    if not content_words:
        return {"lsi": 0.0, "b2_plus_count": 0, "content_word_count": 0}

    b2_plus = sum(1 for lvl in content_words.values() if lvl >= 4.0)
    return {
        "lsi": round(b2_plus / len(content_words), 4),
        "b2_plus_count": b2_plus,
        "content_word_count": len(content_words),
    }


def compute_lexical_diversity(words: list[dict]) -> dict:
    """TTR and Root TTR (Guiraud's Index)."""
    tokens = [w["word"].lower() for w in words]
    total = len(tokens)
    unique = len(set(tokens))

    if total == 0:
        return {"ttr": 0.0, "root_ttr": 0.0}

    return {
        "ttr": round(unique / total, 4),
        "root_ttr": round(unique / math.sqrt(total), 2),
    }


def find_interesting_words(
    words: list[dict], representative_levels: dict
) -> list[dict]:
    """
    Find B2+ content words with high confidence — the words worth highlighting.
    """
    # Gather per-word stats from occurrences
    word_stats: dict[str, dict] = {}
    for w in words:
        token = w["word"].lower()
        if token not in representative_levels:
            continue
        if representative_levels[token] < 4.0:  # B2 = 4.0
            continue
        if token in FUNCTION_WORDS:
            continue
        if len(token) <= 1:
            continue

        if token not in word_stats:
            word_stats[token] = {
                "confidences": [],
                "sources": [],
            }
        word_stats[token]["confidences"].append(w.get("confidence", 0.0))
        if "source" in w:
            word_stats[token]["sources"].append(w["source"])

    interesting = []
    for word, stats in sorted(word_stats.items()):
        avg_conf = sum(stats["confidences"]) / len(stats["confidences"])
        if avg_conf < INTERESTING_CONFIDENCE:
            continue

        entry = {
            "word": word,
            "cefr_level": get_word_level_str(representative_levels[word]),
            "occurrence_count": len(stats["confidences"]),
            "avg_confidence": round(avg_conf, 4),
        }

        # Context quality from source field (if available)
        if stats["sources"]:
            # Use the most common source
            source_counter = Counter(stats["sources"])
            primary_source = source_counter.most_common(1)[0][0]
            if primary_source.startswith("wsd:"):
                entry["context_quality"] = "strong"
            elif primary_source == "cefrpy":
                entry["context_quality"] = "moderate"
            else:
                entry["context_quality"] = "weak"

        interesting.append(entry)

    # Sort by CEFR level descending, then alphabetically
    interesting.sort(key=lambda x: (-CEFR_NUM.get(x["cefr_level"], 0), x["word"]))
    return interesting


def compute_source_distribution(words: list[dict]) -> dict | None:
    """Breakdown of classification sources. Returns None if source field is absent."""
    sources = [w.get("source") for w in words]
    if all(s is None for s in sources):
        return None

    total = len(words)
    if total == 0:
        return None

    categories = {"wsd": 0, "cefrpy": 0, "whitelist": 0, "lemma_fallback": 0,
                  "digit": 0, "other": 0}
    for s in sources:
        if s is None:
            categories["other"] += 1
        elif s.startswith("wsd:"):
            categories["wsd"] += 1
        elif s == "cefrpy":
            categories["cefrpy"] += 1
        elif s == "whitelist":
            categories["whitelist"] += 1
        elif s == "lemma_fallback":
            categories["lemma_fallback"] += 1
        elif s == "digit":
            categories["digit"] += 1
        else:
            categories["other"] += 1

    return {k: round(100 * v / total, 1) for k, v in categories.items()}


def compute_cefr_distribution(words: list[dict]) -> dict:
    """CEFR level distribution across all tokens."""
    counts = Counter(w.get("cefr_level", "UNKNOWN") for w in words)
    total = len(words)
    return {
        lvl: {
            "count": counts.get(lvl, 0),
            "percent": round(100 * counts.get(lvl, 0) / total, 2) if total else 0.0,
        }
        for lvl in LEVELS
    }


def build_vocabulary_snapshot(
    words: list[dict], representative_levels: dict
) -> dict:
    """
    Build a per-unique-word snapshot for history tracking.
    {word: {level, count, source}}
    """
    word_counts: dict[str, int] = Counter()
    word_sources: dict[str, list[str]] = {}

    for w in words:
        token = w["word"].lower()
        word_counts[token] += 1
        if "source" in w:
            word_sources.setdefault(token, []).append(w["source"])

    snapshot = {}
    for word, level_num in representative_levels.items():
        entry = {
            "level": get_word_level_str(level_num),
            "count": word_counts.get(word, 0),
        }
        if word in word_sources:
            source_counter = Counter(word_sources[word])
            entry["source"] = source_counter.most_common(1)[0][0]
        snapshot[word] = entry

    return snapshot


def compute_tier1(student: str, lesson: str) -> dict:
    """Compute all per-lesson metrics."""
    outputs = load_lesson_outputs(student, lesson)
    all_words = merge_segments(outputs)
    segments_analyzed = len(outputs)
    expected_segments = count_expected_segments(student, lesson)

    representative = compute_representative_levels(all_words)
    vocab_level = compute_vocab_level(representative)
    sophistication = compute_lexical_sophistication(representative)
    diversity = compute_lexical_diversity(all_words)
    interesting = find_interesting_words(all_words, representative)
    source_dist = compute_source_distribution(all_words)
    cefr_dist = compute_cefr_distribution(all_words)

    all_tokens = [w["word"].lower() for w in all_words]
    unique_all = set(all_tokens)
    unique_content = {w for w in unique_all if w not in FUNCTION_WORDS}

    # Flags
    flags = {
        "is_baseline": False,  # set later by tier2 logic
        "partial_lesson": (
            expected_segments > 0 and segments_analyzed < expected_segments / 2
        ),
        "low_confidence": len(all_words) < 50,
    }

    snapshot = build_vocabulary_snapshot(all_words, representative)

    tier1 = {
        "vocab_level": vocab_level,
        "lexical_sophistication": sophistication,
        "lexical_diversity": diversity,
        "word_count": {
            "total_tokens": len(all_words),
            "unique_words": len(unique_all),
            "unique_content_words": len(unique_content),
        },
        "cefr_distribution": cefr_dist,
        "source_distribution": source_dist,
        "interesting_words": interesting,
    }

    return {
        "student": student,
        "lesson": lesson,
        "segments_analyzed": segments_analyzed,
        "flags": flags,
        "tier1": tier1,
        "vocabulary_snapshot": snapshot,
    }


# ---------------------------------------------------------------------------
# Tier 2: Cross-lesson comparison
# ---------------------------------------------------------------------------


def load_student_history(student: str) -> dict | None:
    """Load cumulative history file, or None if first lesson."""
    path = PROGRESS_DIR / f"{student}_history.json"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def compute_new_vocabulary(
    snapshot: dict, history: dict, current_level: float
) -> dict:
    """Words in this lesson that never appeared in prior lessons."""
    prior_words = set(history["cumulative_vocabulary"].keys())
    current_words = set(snapshot.keys())
    new_words = current_words - prior_words

    by_level: dict[str, int] = {}
    notable = []
    above_level_count = 0

    for word in sorted(new_words):
        info = snapshot[word]
        level_str = info["level"]
        by_level[level_str] = by_level.get(level_str, 0) + 1

        level_num = CEFR_NUM.get(level_str, 0)
        if level_num >= current_level:
            above_level_count += 1

        # Notable = B2+
        if level_num >= 4.0:
            entry = {"word": word, "level": level_str}
            if "source" in info:
                entry["source"] = info["source"]
            notable.append(entry)

    total_new = len(new_words)
    growth_ratio = round(above_level_count / total_new, 4) if total_new else 0.0

    return {
        "total_new": total_new,
        "by_level": by_level,
        "growth_ratio": growth_ratio,
        "notable_new_words": notable,
    }


def compute_retention(snapshot: dict, history: dict) -> dict:
    """How many words from prior lessons reappear in the current one."""
    prior_words = set(history["cumulative_vocabulary"].keys())
    current_words = set(snapshot.keys())
    retained = prior_words & current_words

    prior_size = len(prior_words)
    rate = round(len(retained) / prior_size, 4) if prior_size else 0.0

    # Highlight retained advanced words (B2+)
    retained_advanced = []
    for word in sorted(retained):
        if word in snapshot:
            level_num = CEFR_NUM.get(snapshot[word]["level"], 0)
            if level_num >= 4.0:
                retained_advanced.append(word)

    return {
        "overall_rate": rate,
        "retained_count": len(retained),
        "prior_vocabulary_size": prior_size,
        "retained_advanced_words": retained_advanced,
    }


def compute_score_trend(history: dict, current_score: float, current_lesson: str) -> dict:
    """Linear regression on vocab_level scores over lessons."""
    scores = []
    for lesson in history.get("lessons_analyzed", []):
        ls = history["lesson_scores"].get(lesson, {})
        if "vocab_level" in ls:
            scores.append(ls["vocab_level"])
    scores.append(current_score)

    n = len(scores)
    if n < 2:
        return {
            "scores": scores,
            "trend": "neutral",
            "trend_magnitude": 0.0,
            "direction_confidence": "low",
        }

    # Simple linear regression: slope of y on index
    x_mean = (n - 1) / 2
    y_mean = sum(scores) / n
    numerator = sum((i - x_mean) * (s - y_mean) for i, s in enumerate(scores))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    slope = numerator / denominator if denominator else 0.0

    if slope > 0.05:
        trend = "positive"
    elif slope < -0.05:
        trend = "negative"
    else:
        trend = "neutral"

    if n < 4:
        confidence = "low"
    elif n < 8:
        confidence = "medium"
    else:
        confidence = "high"

    # Check for unusual jump
    previous_score = scores[-2]
    change = current_score - previous_score

    result = {
        "scores": scores,
        "trend": trend,
        "trend_magnitude": round(slope, 4),
        "direction_confidence": confidence,
        "previous_lesson": history["lessons_analyzed"][-1],
        "vocab_level_change": round(change, 1),
    }

    if abs(change) > 1.0:
        result["unusual_jump"] = True

    return result


def compute_active_vocabulary_growth(
    history: dict, current_snapshot: dict, current_lesson: str
) -> dict:
    """Cumulative unique words over lessons."""
    cumulative_unique = []
    cumulative_b2_plus = []
    growth_rate = []

    seen_words: set[str] = set()
    seen_b2_plus: set[str] = set()

    for lesson in history.get("lessons_analyzed", []):
        vocab = history["cumulative_vocabulary"]
        lesson_words = {
            w for w, info in vocab.items() if lesson in info.get("lessons_present", [])
        }
        seen_words |= lesson_words
        cumulative_unique.append(len(seen_words))

        lesson_b2 = {
            w for w in lesson_words
            if CEFR_NUM.get(vocab[w].get("levels_by_lesson", {}).get(lesson, ""), 0) >= 4.0
        }
        seen_b2_plus |= lesson_b2
        cumulative_b2_plus.append(len(seen_b2_plus))

    # Add current lesson
    prev_total = len(seen_words)
    seen_words |= set(current_snapshot.keys())
    cumulative_unique.append(len(seen_words))

    current_b2 = {
        w for w, info in current_snapshot.items()
        if CEFR_NUM.get(info["level"], 0) >= 4.0
    }
    seen_b2_plus |= current_b2
    cumulative_b2_plus.append(len(seen_b2_plus))

    # Growth rate per lesson
    for i in range(len(cumulative_unique)):
        if i == 0:
            growth_rate.append(cumulative_unique[0])
        else:
            growth_rate.append(cumulative_unique[i] - cumulative_unique[i - 1])

    return {
        "cumulative_unique": cumulative_unique,
        "cumulative_b2_plus": cumulative_b2_plus,
        "growth_rate": growth_rate,
    }


def compute_level_migrations(
    snapshot: dict, history: dict, current_lesson: str
) -> dict:
    """Words whose representative CEFR level changed between lessons."""
    if not history.get("lessons_analyzed"):
        return {"count": 0, "net_direction": "neutral", "meaningful_migrations": []}

    last_lesson = history["lessons_analyzed"][-1]
    migrations = []
    up = 0
    down = 0

    for word, info in snapshot.items():
        vocab_entry = history["cumulative_vocabulary"].get(word)
        if not vocab_entry:
            continue

        prev_level_str = vocab_entry.get("levels_by_lesson", {}).get(last_lesson)
        if not prev_level_str:
            continue

        curr_level_str = info["level"]
        if prev_level_str == curr_level_str:
            continue

        prev_num = CEFR_NUM.get(prev_level_str, 0)
        curr_num = CEFR_NUM.get(curr_level_str, 0)
        direction = "up" if curr_num > prev_num else "down"

        if direction == "up":
            up += 1
        else:
            down += 1

        # Meaningful if both have WSD source
        prev_source = vocab_entry.get("source_by_lesson", {}).get(last_lesson, "")
        curr_source = info.get("source", "")
        meaningful = (
            prev_source.startswith("wsd:") and curr_source.startswith("wsd:")
        )

        migrations.append({
            "word": word,
            "from_level": prev_level_str,
            "from_lesson": last_lesson,
            "to_level": curr_level_str,
            "to_lesson": current_lesson,
            "direction": direction,
            "likely_meaningful": meaningful,
        })

    if up > down:
        net = "up"
    elif down > up:
        net = "down"
    else:
        net = "neutral"

    return {
        "count": len(migrations),
        "net_direction": net,
        "meaningful_migrations": [m for m in migrations if m["likely_meaningful"]],
    }


def compute_tier2(tier1_result: dict, history: dict | None) -> dict | None:
    """Compute cross-lesson comparison metrics. Returns None for first lesson."""
    if history is None or not history.get("lessons_analyzed"):
        return None

    snapshot = tier1_result["vocabulary_snapshot"]
    current_score = tier1_result["tier1"]["vocab_level"]["score"]
    current_lesson = tier1_result["lesson"]

    trend = compute_score_trend(history, current_score, current_lesson)
    new_vocab = compute_new_vocabulary(snapshot, history, current_score)
    retention = compute_retention(snapshot, history)
    growth = compute_active_vocabulary_growth(history, snapshot, current_lesson)
    migrations = compute_level_migrations(snapshot, history, current_lesson)

    return {
        "comparison": trend,
        "new_vocabulary": new_vocab,
        "retention": retention,
        "active_vocabulary": growth,
        "level_migrations": migrations,
    }


# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------


def update_student_history(
    history: dict | None, tier1_result: dict
) -> dict:
    """Add current lesson data to cumulative history."""
    student = tier1_result["student"]
    lesson = tier1_result["lesson"]
    snapshot = tier1_result["vocabulary_snapshot"]
    tier1 = tier1_result["tier1"]

    if history is None:
        history = {
            "student": student,
            "lessons_analyzed": [],
            "cumulative_vocabulary": {},
            "lesson_scores": {},
        }

    # Avoid re-processing the same lesson
    if lesson in history["lessons_analyzed"]:
        history["lessons_analyzed"].remove(lesson)

    history["lessons_analyzed"].append(lesson)

    # Update cumulative vocabulary
    for word, info in snapshot.items():
        if word not in history["cumulative_vocabulary"]:
            history["cumulative_vocabulary"][word] = {
                "first_seen": lesson,
                "last_seen": lesson,
                "lessons_present": [lesson],
                "levels_by_lesson": {lesson: info["level"]},
                "source_by_lesson": {},
            }
        else:
            entry = history["cumulative_vocabulary"][word]
            entry["last_seen"] = lesson
            if lesson not in entry["lessons_present"]:
                entry["lessons_present"].append(lesson)
            entry["levels_by_lesson"][lesson] = info["level"]

        if "source" in info:
            history["cumulative_vocabulary"][word]["source_by_lesson"][lesson] = info["source"]

    # Store lesson scores
    history["lesson_scores"][lesson] = {
        "vocab_level": tier1["vocab_level"]["score"],
        "lsi": tier1["lexical_sophistication"]["lsi"],
        "root_ttr": tier1["lexical_diversity"]["root_ttr"],
        "unique_words": tier1["word_count"]["unique_words"],
    }

    return history


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    if len(sys.argv) < 3:
        print("Usage: python vocab_progress.py <Student-X> <lesson-Y>", file=sys.stderr)
        sys.exit(1)

    student = sys.argv[1]
    lesson = sys.argv[2]

    PROGRESS_DIR.mkdir(exist_ok=True)

    # Tier 1
    tier1_result = compute_tier1(student, lesson)

    # Tier 2
    history = load_student_history(student)
    tier2 = compute_tier2(tier1_result, history)

    # Update flags
    if history is None or not history.get("lessons_analyzed"):
        tier1_result["flags"]["is_baseline"] = True

    # Assemble final output
    result = {
        "student": student,
        "lesson": lesson,
        "segments_analyzed": tier1_result["segments_analyzed"],
        "flags": tier1_result["flags"],
        "tier1": tier1_result["tier1"],
        "tier2": tier2,
        "vocabulary_snapshot": tier1_result["vocabulary_snapshot"],
    }

    # Write progress JSON
    progress_path = PROGRESS_DIR / f"{student}_{lesson}_progress.json"
    with progress_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[ok] {progress_path}")

    # Update and write history
    history = update_student_history(history, tier1_result)
    history_path = PROGRESS_DIR / f"{student}_history.json"
    with history_path.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
    print(f"[ok] {history_path}")


if __name__ == "__main__":
    main()
