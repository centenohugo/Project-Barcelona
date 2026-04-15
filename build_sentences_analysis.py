"""
build_sentences_analysis.py — Build per-lesson sentences-analysis.json.

For each Student-N/lesson-N fluidity.json produces:
  processed_data/sentences_analysis/Student-N/lesson-N/sentences-analysis.json

Each sentence record:
  sentence_id   int
  text          str
  word_count    int
  gaps          inter-word pauses in seconds {mean, min, max, std, count}
  fillers       {count, rate, types}
  duplicates    [{phrase, occurrences, start_indices, match_type}]
  accuracy      ASR confidence {mean, min}
  fluency       {score, components: {speed, gaps, fillers, dups}}

Duplicate detection handles:
  - exact word repeats        "of of of"
  - exact phrase repeats      "I am I am thinking"
  - fuzzy/truncated repeats   "this lan this language"  (one word is a prefix
                               of the other, min 3 chars)

Fluency score (0–100):
  score = 100 × (0.35·S_speed + 0.35·S_gaps + 0.15·S_fillers + 0.15·S_dups)

  S_speed   = clip((SPEED_WORST − mean_content_speed) / (SPEED_WORST − SPEED_BEST), 0, 1)
  S_gaps    = clip(1 − thinking_ratio / THINKING_MAX, 0, 1)
              thinking_ratio = Σclip(gap,0,GAP_CLIP) / (total_speech + Σclip(gap,0,GAP_CLIP))
  S_fillers = clip(1 − filler_rate / FILLER_MAX, 0, 1)
  S_dups    = clip(1 − dup_rate    / DUP_MAX,    0, 1)
              dup_rate = Σ phrase_len×(occurrences−1) / n_words

Usage:
  python build_sentences_analysis.py            # all lessons
  python build_sentences_analysis.py <path/to/fluidity.json>
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

FLUIDITY_ROOT = Path(__file__).parent / "processed_data" / "fluidity"
OUT_ROOT      = Path(__file__).parent / "processed_data" / "sentences_analysis"

FUZZY_MIN_LEN = 3   # minimum key-length for truncated-word fuzzy matching

# ── Fluency score calibration ─────────────────────────────────────────────────
# Thresholds are anchored to the empirical distribution of this learner corpus.
SPEED_BEST    = 0.04   # s/letter — p05 of content words (near-native) → S_speed = 1.0
SPEED_WORST   = 0.20   # s/letter — p95 of content words (very slow)   → S_speed = 0.0

GAP_CLIP      = 5.0    # seconds  — clip longer gaps (likely transcription gaps)
THINKING_MAX  = 0.60   # ratio    — 60 % of utterance time in pauses   → S_gaps  = 0.0

FILLER_MAX    = 0.40   # ratio    — 40 % filler words                  → S_fillers = 0.0
DUP_MAX       = 0.40   # ratio    — 40 % duplicate-token rate           → S_dups  = 0.0

W_SPEED   = 0.35
W_GAPS    = 0.35
W_FILLERS = 0.15
W_DUPS    = 0.15


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _key(word: str) -> str:
    """Lowercase + strip non-alphanumeric, used for word comparison."""
    return re.sub(r"[^\w]", "", word).lower()


def _words_match(a: str, b: str) -> tuple[bool, bool]:
    """
    Return (matches, is_fuzzy).

    Exact:  same after normalisation.
    Fuzzy:  one key is a strict prefix of the other AND the shorter key
            has at least FUZZY_MIN_LEN chars (avoids matching very short tokens).
    Empty/punctuation-only tokens never match.
    """
    ka, kb = _key(a), _key(b)
    if not ka or not kb:
        return False, False
    if ka == kb:
        return True, False
    short, long = (ka, kb) if len(ka) <= len(kb) else (kb, ka)
    if len(short) >= FUZZY_MIN_LEN and long.startswith(short):
        return True, True
    return False, False


def _phrases_match(
    ws_a: list[dict], ws_b: list[dict]
) -> tuple[bool, bool]:
    """
    Check whether two same-length word-dict lists match pairwise.
    Returns (all_match, any_fuzzy).
    """
    any_fuzzy = False
    for a, b in zip(ws_a, ws_b):
        ok, fuzzy = _words_match(a["word"], b["word"])
        if not ok:
            return False, False
        if fuzzy:
            any_fuzzy = True
    return True, any_fuzzy


# ═══════════════════════════════════════════════════════════════════════════════
#  1.  Duplicate detection
# ═══════════════════════════════════════════════════════════════════════════════

def find_duplicates(ws: list[dict]) -> list[dict]:
    """
    Find all consecutive repeated words or phrases within a sentence.

    Algorithm: at each unconsumed position i, try phrase lengths from longest
    to shortest.  When phrase[i:i+k] matches phrase[i+k:i+2k] (exact or fuzzy),
    extend to count further consecutive repetitions, record the entry, mark all
    involved indices as consumed, and advance i by k.

    Returns a list of records:
      phrase        list[str]   — first-occurrence words (lowercase)
      occurrences   int         — total number of occurrences
      start_indices list[int]   — sentence-local word index of each occurrence
      match_type    str         — "exact" | "fuzzy"
    """
    n = len(ws)
    matched: set[int] = set()
    results: list[dict] = []

    i = 0
    while i < n:
        if i in matched:
            i += 1
            continue

        max_k = (n - i) // 2
        found = False

        for k in range(max_k, 0, -1):
            # Skip if any word in the first phrase is already consumed
            if any((i + p) in matched for p in range(k)):
                continue

            ok, fuzzy = _phrases_match(ws[i:i + k], ws[i + k:i + 2 * k])
            if not ok:
                continue

            # Count additional consecutive repetitions beyond the first pair
            start_indices = [i, i + k]
            j = i + 2 * k
            while j + k <= n:
                ok2, fz2 = _phrases_match(ws[i:i + k], ws[j:j + k])
                if ok2:
                    start_indices.append(j)
                    if fz2:
                        fuzzy = True
                    j += k
                else:
                    break

            phrase_words = [ws[i + p]["word"].lower() for p in range(k)]
            results.append({
                "phrase":        phrase_words,
                "occurrences":   len(start_indices),
                "start_indices": start_indices,
                "match_type":    "fuzzy" if fuzzy else "exact",
            })

            for start in start_indices:
                for p in range(k):
                    matched.add(start + p)

            found = True
            i += k   # advance past first occurrence (already in matched)
            break

        if not found:
            i += 1

    return results


# ═══════════════════════════════════════════════════════════════════════════════
#  2.  Gap stats
# ═══════════════════════════════════════════════════════════════════════════════

def _gap_stats(ws: list[dict]) -> dict:
    """
    Inter-word pause in seconds for consecutive word pairs within a sentence.
    gap = start(word[i+1]) - end(word[i]).  Can be negative (overlap).
    """
    if len(ws) < 2:
        return {"mean": None, "min": None, "max": None, "std": None, "count": 0}

    gaps = [ws[i + 1]["start"] - ws[i]["end"] for i in range(len(ws) - 1)]
    mean = sum(gaps) / len(gaps)
    variance = sum((g - mean) ** 2 for g in gaps) / len(gaps)
    return {
        "mean":  round(mean, 4),
        "min":   round(min(gaps), 4),
        "max":   round(max(gaps), 4),
        "std":   round(math.sqrt(variance), 4),
        "count": len(gaps),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  3.  Filler aggregation
# ═══════════════════════════════════════════════════════════════════════════════

def _filler_stats(ws: list[dict]) -> dict:
    fillers = [w for w in ws if w.get("is_filler")]
    count = len(fillers)
    rate  = round(count / len(ws), 4) if ws else 0.0
    types: dict[str, int] = {}
    for w in fillers:
        ft = w.get("filler_type") or "unknown"
        types[ft] = types.get(ft, 0) + 1
    return {"count": count, "rate": rate, "types": types}


# ═══════════════════════════════════════════════════════════════════════════════
#  4.  Accuracy aggregation
# ═══════════════════════════════════════════════════════════════════════════════

def _accuracy_stats(ws: list[dict]) -> dict:
    confs = [w["confidence"] for w in ws if w.get("confidence") is not None]
    if not confs:
        return {"mean": None, "min": None}
    return {
        "mean": round(sum(confs) / len(confs), 4),
        "min":  round(min(confs), 4),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  5.  Fluency score
# ═══════════════════════════════════════════════════════════════════════════════

def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def compute_fluency_score(ws: list[dict], dups: list[dict]) -> dict:
    """
    Compute a 0–100 fluency score for a single sentence.

    Returns:
        {
          "score":      float,          # final 0–100 score (None for < 2 content words)
          "components": {               # each sub-score also on 0–100 scale
            "speed":   float,
            "gaps":    float,
            "fillers": float,
            "dups":    float,
          }
        }
    """
    n = len(ws)
    if n == 0:
        return {"score": None, "components": {}}

    # ── S_speed ───────────────────────────────────────────────────────────────
    content_speeds = [
        w["speed"] for w in ws
        if not w.get("is_filler") and w.get("speed") is not None
    ]
    if content_speeds:
        mean_speed = sum(content_speeds) / len(content_speeds)
        s_speed = _clip(
            (SPEED_WORST - mean_speed) / (SPEED_WORST - SPEED_BEST),
            0.0, 1.0,
        )
    else:
        s_speed = 0.0   # sentence is all fillers

    # ── S_gaps ────────────────────────────────────────────────────────────────
    # Clip each gap to [0, GAP_CLIP] — negatives (overlaps) treated as 0.
    clipped_gaps = [
        _clip(ws[i + 1]["start"] - ws[i]["end"], 0.0, GAP_CLIP)
        for i in range(n - 1)
    ]
    total_pause  = sum(clipped_gaps)
    total_speech = sum(w["end"] - w["start"] for w in ws)
    total_time   = total_speech + total_pause
    if total_time > 0:
        thinking_ratio = total_pause / total_time
    else:
        thinking_ratio = 0.0

    s_gaps = _clip(1.0 - thinking_ratio / THINKING_MAX, 0.0, 1.0)

    # ── S_fillers ─────────────────────────────────────────────────────────────
    filler_rate = sum(1 for w in ws if w.get("is_filler")) / n
    s_fillers   = _clip(1.0 - filler_rate / FILLER_MAX, 0.0, 1.0)

    # ── S_dups ────────────────────────────────────────────────────────────────
    n_extra_tokens = sum(len(d["phrase"]) * (d["occurrences"] - 1) for d in dups)
    dup_rate = n_extra_tokens / n
    s_dups   = _clip(1.0 - dup_rate / DUP_MAX, 0.0, 1.0)

    # ── Combined ──────────────────────────────────────────────────────────────
    score = round(
        100.0 * (W_SPEED * s_speed + W_GAPS * s_gaps + W_FILLERS * s_fillers + W_DUPS * s_dups),
        1,
    )

    return {
        "score": score,
        "components": {
            "speed":   round(s_speed   * 100, 1),
            "gaps":    round(s_gaps    * 100, 1),
            "fillers": round(s_fillers * 100, 1),
            "dups":    round(s_dups    * 100, 1),
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  6.  File processing
# ═══════════════════════════════════════════════════════════════════════════════

def process_file(fluidity_path: Path) -> Path:
    data    = json.loads(fluidity_path.read_text(encoding="utf-8"))
    student = data["student"]
    lesson  = data["lesson"]
    words   = data["words"]
    sents   = data["sentences"]

    # Group words by sentence_id (already sorted by position from build_fluidity)
    sent_words: dict[int, list[dict]] = defaultdict(list)
    for w in words:
        sent_words[w["sentence_id"]].append(w)

    sent_text = {s["sentence_id"]: s["text"] for s in sents}

    records = []
    for sid in sorted(sent_words.keys()):
        ws   = sent_words[sid]
        dups = find_duplicates(ws)
        records.append({
            "sentence_id": sid,
            "text":        sent_text.get(sid, ""),
            "word_count":  len(ws),
            "gaps":        _gap_stats(ws),
            "fillers":     _filler_stats(ws),
            "duplicates":  dups,
            "accuracy":    _accuracy_stats(ws),
            "fluency":     compute_fluency_score(ws, dups),
        })

    out_path = OUT_ROOT / student / lesson / "sentences-analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(
            {"student": student, "lesson": lesson, "sentences": records},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    return out_path


# ═══════════════════════════════════════════════════════════════════════════════
#  7.  CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "files", nargs="*", metavar="fluidity.json",
        help="Specific fluidity.json files. Default: all lessons.",
    )
    args = parser.parse_args()

    paths = (
        [Path(f) for f in args.files]
        if args.files
        else sorted(FLUIDITY_ROOT.rglob("fluidity.json"))
    )
    if not paths:
        print("No fluidity.json files found.", file=sys.stderr)
        sys.exit(1)

    for p in paths:
        out  = process_file(p)
        data = json.loads(out.read_text(encoding="utf-8"))
        sents = data["sentences"]
        n_dup  = sum(1 for s in sents if s["duplicates"])
        n_fill = sum(s["fillers"]["count"] for s in sents)
        print(
            f"  {data['student']}/{data['lesson']}: {len(sents)} sentences, "
            f"{n_dup} with duplicates, {n_fill} fillers  ->  {out}"
        )

    print(f"\nDone. Processed {len(paths)} file(s).")


if __name__ == "__main__":
    main()
