"""
src/build_fluency.py — Unified fluency pipeline (single file per lesson).

Reads :  data/raw/{student}/{lesson}/*.json
Writes:  data/processed/{student}/{lesson}/fluency.json

Pipeline (no intermediate files):
  1. Load raw ASR words → spaCy sentence segmentation → sentence_id per word
  2. Add speed (seconds per letter) to every word
  3. Flag fillers (lexicon method by default, --method llm for Anthropic API)
  4. Compute sentence-level analysis: gaps, fillers, duplicates, accuracy, fluency score

Output schema:
  {
    "student": str,  "lesson": str,  "generated_at": str,
    "total_words": int,  "total_sentences": int,
    "sentences": [
      {
        "sentence_id": int,  "text": str,  "word_count": int,
        "gaps":       {mean, min, max, std, count},
        "fillers":    {count, rate, types: {type: count}},
        "duplicates": [{phrase, occurrences, start_indices, match_type}],
        "accuracy":   {mean, min},
        "fluency":    {score, components: {speed, gaps, fillers, dups}},
        "words": [
          {word, punctuated_word, start, end, confidence,
           sentence_id, speed, is_filler, filler_type, filler_pattern}
        ]
      }, ...
    ]
  }

Usage:
  python src/build_fluency.py                        # all lessons
  python src/build_fluency.py Student-1 lesson-1     # single lesson
  python src/build_fluency.py --method llm           # all lessons, LLM filler detection
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import spacy

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT     = Path(__file__).parent.parent          # repo root
RAW_ROOT = ROOT / "data" / "raw"
OUT_ROOT = ROOT / "data" / "processed"


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — Load raw words + sentence segmentation
# ═══════════════════════════════════════════════════════════════════════════════

def _collect_raw_words(lesson_dir: Path) -> list[dict]:
    """Load ch0 words from all *.json files in lesson_dir (sorted by filename)."""
    words: list[dict] = []
    for f in sorted(lesson_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        file_words = data["results"]["channels"][0]["alternatives"][0]["words"]
        for w in sorted(file_words, key=lambda x: x["start"]):
            words.append({
                "word":           w.get("word", "").lower(),
                "punctuated_word": w.get("punctuated_word", w.get("word", "")),
                "start":          w["start"],
                "end":            w["end"],
                "confidence":     w.get("confidence", 1.0),
            })
    return words


def _assign_sentence_ids(
    words: list[dict], nlp: spacy.Language
) -> tuple[list[dict], list[dict]]:
    """
    Join all punctuated_word values, run spaCy sentence segmentation,
    assign sentence_id (1-based) to each word by character offset.

    Returns (sentences_meta, words_with_sid).
    """
    text_parts = [w["punctuated_word"] for w in words]
    full_text  = " ".join(text_parts)

    # Character offset of each word in full_text
    offsets: list[int] = []
    pos = 0
    for part in text_parts:
        offsets.append(pos)
        pos += len(part) + 1   # +1 for the joining space

    doc   = nlp(full_text)
    sents = list(doc.sents)

    sentences_meta = [
        {"sentence_id": i + 1, "text": s.text.strip()}
        for i, s in enumerate(sents)
    ]

    # Map each word to the sentence whose char range contains its offset
    ranges = [(s.start_char, s.end_char) for s in sents]

    def _find_sid(char_offset: int) -> int:
        for j, (sc, ec) in enumerate(ranges):
            if sc <= char_offset < ec:
                return j + 1
        return len(ranges)   # trailing-space fallback

    words_out = [
        {**w, "sentence_id": _find_sid(offsets[i])}
        for i, w in enumerate(words)
    ]
    return sentences_meta, words_out


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — Speed
# ═══════════════════════════════════════════════════════════════════════════════

def _add_speed(words: list[dict]) -> None:
    """Add 'speed' (seconds per letter) in-place. None for words with no letters."""
    for w in words:
        n_letters = len(re.sub(r"[^a-zA-Z]", "", w["word"]))
        w["speed"] = round((w["end"] - w["start"]) / n_letters, 4) if n_letters else None


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — Filler detection
# ═══════════════════════════════════════════════════════════════════════════════

ALWAYS_FILLERS: dict[str, str] = {
    "yeah": "backchannel", "yep": "backchannel", "yup": "backchannel",
    "okay": "backchannel", "ok": "backchannel", "k": "backchannel",
    "mhmm": "backchannel", "mmm": "backchannel", "uh-huh": "backchannel",
    "uh":   "hesitation",  "um": "hesitation",   "hmm": "hesitation",
    "ah":   "hesitation",  "er": "hesitation",   "erm": "hesitation",
    "x":    "placeholder",
}

MULTI_WORD_FILLERS: list[tuple[list[str], str]] = [
    (["you", "know", "what", "i", "mean"], "discourse_marker"),
    (["you", "know", "what"],              "discourse_marker"),
    (["let's", "say"],                     "discourse_marker"),
    (["lets",  "say"],                     "discourse_marker"),
    (["you",   "know"],                    "discourse_marker"),
    (["i",     "mean"],                    "discourse_marker"),
    (["i",     "guess"],                   "discourse_marker"),
    (["kind",  "of"],                      "discourse_marker"),
    (["sort",  "of"],                      "discourse_marker"),
]

POSITIONAL_FILLERS: dict[str, tuple[str, str]] = {
    "so":        ("discourse_marker", "initial"),
    "well":      ("discourse_marker", "initial"),
    "right":     ("backchannel",      "final"),
    "actually":  ("discourse_marker", "initial"),
    "basically": ("discourse_marker", "initial"),
    "anyway":    ("discourse_marker", "any"),
    "like":      ("discourse_marker", "any"),
}

_LIKE_CONTENT_PREV: set[str] = {
    "would", "could", "looks", "look", "sounds", "feel", "feels",
    "seemed", "seems", "taste", "tastes", "just", "nothing", "something", "anything",
}


def _sentence_positions(words: list[dict]) -> list[str]:
    n = len(words)
    positions = ["middle"] * n
    for i, w in enumerate(words):
        sid      = w["sentence_id"]
        is_first = (i == 0) or (words[i - 1]["sentence_id"] != sid)
        is_last  = (i == n - 1) or (words[i + 1]["sentence_id"] != sid)
        if is_first:
            positions[i] = "initial"
        elif is_last:
            positions[i] = "final"
    return positions


def _flag_fillers_lexicon(words: list[dict]) -> None:
    """Detect fillers using the rule-based lexicon. Modifies words in-place."""
    n = len(words)
    positions = _sentence_positions(words)

    # Initialise
    for w in words:
        w["is_filler"] = False
        w["filler_type"] = None
        w["filler_pattern"] = None

    matched: set[int] = set()

    # Multi-word patterns (longest first)
    for pattern, ftype in MULTI_WORD_FILLERS:
        k = len(pattern)
        for i in range(n - k + 1):
            if i in matched:
                continue
            if [words[i + j]["word"].lower() for j in range(k)] == pattern:
                pname = " ".join(pattern)
                for j in range(k):
                    words[i + j]["is_filler"]      = True
                    words[i + j]["filler_type"]    = ftype
                    words[i + j]["filler_pattern"] = pname
                    matched.add(i + j)

    # Always-fillers
    for i, w in enumerate(words):
        if i in matched:
            continue
        token = w["word"].lower()
        if token in ALWAYS_FILLERS:
            w["is_filler"]      = True
            w["filler_type"]    = ALWAYS_FILLERS[token]
            w["filler_pattern"] = token
            matched.add(i)

    # Positional fillers
    for i, w in enumerate(words):
        if i in matched:
            continue
        token = w["word"].lower()
        if token not in POSITIONAL_FILLERS:
            continue
        ftype, allowed_pos = POSITIONAL_FILLERS[token]
        if token == "like":
            prev = words[i - 1]["word"].lower() if i > 0 else ""
            if prev in _LIKE_CONTENT_PREV:
                continue
        if allowed_pos == "any" or positions[i] == allowed_pos:
            w["is_filler"]      = True
            w["filler_type"]    = ftype
            w["filler_pattern"] = token
            matched.add(i)


_LLM_SYSTEM = """\
You are analysing filler words in transcribed English learner speech.

Filler types:
  backchannel     — yeah, okay, mhmm, uh-huh, right (sentence-final acknowledgement)
  hesitation      — uh, um, hmm, ah, er (filled pauses)
  discourse_marker— so (sentence-initial), well (sentence-initial), like (discourse),
                    you know, I mean, let's say, actually (reframing), anyway, kind of
  placeholder     — x (used when the student cannot recall a word)

Return ONLY a JSON array. Each element: {"idx": <int>, "filler_type": "<type>", "filler_pattern": "<matched text>"}.
If no fillers, return [].
Do not explain. Do not include markdown fences."""


def _flag_fillers_llm(words: list[dict]) -> None:
    """Detect fillers using Anthropic claude-haiku. Falls back to lexicon on error."""
    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed — falling back to lexicon.", file=sys.stderr)
        _flag_fillers_lexicon(words)
        return

    client = anthropic.Anthropic()
    for w in words:
        w["is_filler"] = False
        w["filler_type"] = None
        w["filler_pattern"] = None

    sent_map: dict[int, list[tuple[int, dict]]] = defaultdict(list)
    for i, w in enumerate(words):
        sent_map[w["sentence_id"]].append((i, w))

    sentence_ids = sorted(sent_map.keys())
    BATCH = 25

    for batch_start in range(0, len(sentence_ids), BATCH):
        batch_sids = sentence_ids[batch_start: batch_start + BATCH]
        lines = [
            f"{idx} | s{sid} | {w['punctuated_word']}"
            for sid in batch_sids
            for idx, w in sent_map[sid]
        ]
        try:
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=_LLM_SYSTEM,
                messages=[{"role": "user", "content": "\n".join(lines)}],
            )
            raw = re.sub(r"^```[a-z]*\n?", "", resp.content[0].text.strip())
            raw = re.sub(r"\n?```$", "", raw)
            for hit in json.loads(raw):
                idx = hit.get("idx")
                if idx is not None and 0 <= idx < len(words):
                    words[idx]["is_filler"]      = True
                    words[idx]["filler_type"]    = hit.get("filler_type", "discourse_marker")
                    words[idx]["filler_pattern"] = hit.get("filler_pattern", words[idx]["word"])
        except Exception as exc:
            print(f"LLM batch error (sids {batch_sids[0]}–{batch_sids[-1]}): {exc}", file=sys.stderr)
            batch_words = [w for sid in batch_sids for _, w in sent_map[sid]]
            _flag_fillers_lexicon(batch_words)


def _flag_fillers(words: list[dict], method: str = "lexicon") -> None:
    if method == "llm":
        _flag_fillers_llm(words)
    else:
        _flag_fillers_lexicon(words)


# ═══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — Sentence-level analysis
# ═══════════════════════════════════════════════════════════════════════════════

FUZZY_MIN_LEN = 3
SPEED_BEST    = 0.04
SPEED_WORST   = 0.20
GAP_CLIP      = 5.0
THINKING_MAX  = 0.60
FILLER_MAX    = 0.40
DUP_MAX       = 0.40
W_SPEED, W_GAPS, W_FILLERS, W_DUPS = 0.35, 0.35, 0.15, 0.15


def _key(word: str) -> str:
    return re.sub(r"[^\w]", "", word).lower()


def _words_match(a: str, b: str) -> tuple[bool, bool]:
    ka, kb = _key(a), _key(b)
    if not ka or not kb:
        return False, False
    if ka == kb:
        return True, False
    short, long = (ka, kb) if len(ka) <= len(kb) else (kb, ka)
    if len(short) >= FUZZY_MIN_LEN and long.startswith(short):
        return True, True
    return False, False


def _phrases_match(ws_a: list[dict], ws_b: list[dict]) -> tuple[bool, bool]:
    any_fuzzy = False
    for a, b in zip(ws_a, ws_b):
        ok, fuzzy = _words_match(a["word"], b["word"])
        if not ok:
            return False, False
        if fuzzy:
            any_fuzzy = True
    return True, any_fuzzy


def _find_duplicates(ws: list[dict]) -> list[dict]:
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
            if any((i + p) in matched for p in range(k)):
                continue
            ok, fuzzy = _phrases_match(ws[i:i + k], ws[i + k:i + 2 * k])
            if not ok:
                continue
            starts = [i, i + k]
            j = i + 2 * k
            while j + k <= n:
                ok2, fz2 = _phrases_match(ws[i:i + k], ws[j:j + k])
                if ok2:
                    starts.append(j)
                    if fz2:
                        fuzzy = True
                    j += k
                else:
                    break
            results.append({
                "phrase":        [ws[i + p]["word"].lower() for p in range(k)],
                "occurrences":   len(starts),
                "start_indices": starts,
                "match_type":    "fuzzy" if fuzzy else "exact",
            })
            for s in starts:
                for p in range(k):
                    matched.add(s + p)
            found = True
            i += k
            break
        if not found:
            i += 1
    return results


def _gap_stats(ws: list[dict]) -> dict:
    if len(ws) < 2:
        return {"mean": None, "min": None, "max": None, "std": None, "count": 0}
    gaps = [ws[i + 1]["start"] - ws[i]["end"] for i in range(len(ws) - 1)]
    mean = sum(gaps) / len(gaps)
    std  = math.sqrt(sum((g - mean) ** 2 for g in gaps) / len(gaps))
    return {
        "mean": round(mean, 4), "min": round(min(gaps), 4),
        "max":  round(max(gaps), 4), "std": round(std, 4), "count": len(gaps),
    }


def _filler_stats(ws: list[dict]) -> dict:
    fillers = [w for w in ws if w.get("is_filler")]
    types: dict[str, int] = {}
    for w in fillers:
        ft = w.get("filler_type") or "unknown"
        types[ft] = types.get(ft, 0) + 1
    return {"count": len(fillers), "rate": round(len(fillers) / len(ws), 4) if ws else 0.0, "types": types}


def _accuracy_stats(ws: list[dict]) -> dict:
    confs = [w["confidence"] for w in ws if w.get("confidence") is not None]
    if not confs:
        return {"mean": None, "min": None}
    return {"mean": round(sum(confs) / len(confs), 4), "min": round(min(confs), 4)}


def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _fluency_score(ws: list[dict], dups: list[dict]) -> dict:
    n = len(ws)
    if n == 0:
        return {"score": None, "components": {}}

    content_speeds = [w["speed"] for w in ws if not w.get("is_filler") and w.get("speed") is not None]
    s_speed = _clip((SPEED_WORST - sum(content_speeds) / len(content_speeds)) / (SPEED_WORST - SPEED_BEST), 0.0, 1.0) \
              if content_speeds else 0.0

    clipped_gaps = [_clip(ws[i + 1]["start"] - ws[i]["end"], 0.0, GAP_CLIP) for i in range(n - 1)]
    total_pause  = sum(clipped_gaps)
    total_speech = sum(w["end"] - w["start"] for w in ws)
    total_time   = total_speech + total_pause
    s_gaps = _clip(1.0 - (total_pause / total_time) / THINKING_MAX, 0.0, 1.0) if total_time > 0 else 1.0

    filler_rate = sum(1 for w in ws if w.get("is_filler")) / n
    s_fillers   = _clip(1.0 - filler_rate / FILLER_MAX, 0.0, 1.0)

    n_extra = sum(len(d["phrase"]) * (d["occurrences"] - 1) for d in dups)
    s_dups  = _clip(1.0 - (n_extra / n) / DUP_MAX, 0.0, 1.0)

    score = round(100.0 * (W_SPEED * s_speed + W_GAPS * s_gaps + W_FILLERS * s_fillers + W_DUPS * s_dups), 1)
    return {
        "score": score,
        "components": {
            "speed":   round(s_speed * 100, 1), "gaps":    round(s_gaps * 100, 1),
            "fillers": round(s_fillers * 100, 1), "dups":  round(s_dups * 100, 1),
        },
    }


def _analyse_sentences(sentences_meta: list[dict], words: list[dict]) -> list[dict]:
    """Group words by sentence_id and compute all sentence-level metrics."""
    sent_words: dict[int, list[dict]] = defaultdict(list)
    for w in words:
        sent_words[w["sentence_id"]].append(w)

    sent_text = {s["sentence_id"]: s["text"] for s in sentences_meta}

    records = []
    for sid in sorted(sent_words.keys()):
        ws   = sent_words[sid]
        dups = _find_duplicates(ws)
        records.append({
            "sentence_id": sid,
            "text":        sent_text.get(sid, ""),
            "word_count":  len(ws),
            "gaps":        _gap_stats(ws),
            "fillers":     _filler_stats(ws),
            "duplicates":  dups,
            "accuracy":    _accuracy_stats(ws),
            "fluency":     _fluency_score(ws, dups),
            "words":       ws,
        })
    return records


# ═══════════════════════════════════════════════════════════════════════════════
#  Main processor
# ═══════════════════════════════════════════════════════════════════════════════

def process_lesson(student: str, lesson: str, nlp: spacy.Language, method: str = "lexicon") -> Path:
    lesson_dir = RAW_ROOT / student / lesson
    if not lesson_dir.exists():
        raise FileNotFoundError(f"Raw data not found: {lesson_dir}")

    print(f"  {student}/{lesson} ...")

    words = _collect_raw_words(lesson_dir)
    sentences_meta, words = _assign_sentence_ids(words, nlp)
    _add_speed(words)
    _flag_fillers(words, method=method)
    sentences = _analyse_sentences(sentences_meta, words)

    n_fillers = sum(s["fillers"]["count"] for s in sentences)
    n_dups    = sum(1 for s in sentences if s["duplicates"])
    avg_fluency = round(
        sum(s["fluency"]["score"] for s in sentences if s["fluency"]["score"] is not None)
        / max(1, sum(1 for s in sentences if s["fluency"]["score"] is not None)), 1
    )
    print(f"    {len(sentences)} sentences, {len(words)} words, "
          f"{n_fillers} fillers, {n_dups} sents with duplicates, avg fluency={avg_fluency}")

    output = {
        "student":          student,
        "lesson":           lesson,
        "generated_at":     datetime.now(timezone.utc).isoformat(),
        "total_words":      len(words),
        "total_sentences":  len(sentences),
        "sentences":        sentences,
    }

    out_path = OUT_ROOT / student / lesson / "fluency.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"    -> {out_path}")
    return out_path


def process_all(nlp: spacy.Language, method: str = "lexicon") -> list[Path]:
    lessons = sorted(
        (s.name, l.name)
        for s in RAW_ROOT.iterdir() if s.is_dir()
        for l in s.iterdir()        if l.is_dir()
    )
    if not lessons:
        print(f"No lessons found under {RAW_ROOT}", file=sys.stderr)
        sys.exit(1)
    return [process_lesson(s, l, nlp, method=method) for s, l in lessons]


# ═══════════════════════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("student", nargs="?", help="e.g. Student-1")
    parser.add_argument("lesson",  nargs="?", help="e.g. lesson-1")
    parser.add_argument("--method", choices=["lexicon", "llm"], default="lexicon",
                        help="Filler detection method (default: lexicon)")
    args = parser.parse_args()

    print("Loading spaCy model...")
    nlp = spacy.load("en_core_web_sm")
    print(f"Model ready: {nlp.meta['name']} v{nlp.meta['version']}\n")

    if args.student and args.lesson:
        process_lesson(args.student, args.lesson, nlp, method=args.method)
    else:
        process_all(nlp, method=args.method)

    print("\nDone.")


if __name__ == "__main__":
    main()
