"""
fluidity_analysis.py — Fluency analysis functions for processed_data/fluidity/*.json

Two main enrichment functions:
  add_speed(words)                  — adds 'speed' (seconds per letter) to every word
  flag_if_filler(words, method=...) — adds 'is_filler', 'filler_type', 'filler_pattern'

Filler detection methods:
  'lexicon' (default) — fast rule-based matching, no API needed
  'llm'               — Anthropic claude-haiku-4-5 for contextual disambiguation

CLI:
  python fluidity_analysis.py                          # all lessons, lexicon method
  python fluidity_analysis.py --method llm             # all lessons, LLM method
  python fluidity_analysis.py <path/to/fluidity.json>  # single file
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
FLUIDITY_ROOT = Path(__file__).parent / "processed_data" / "fluidity"


# ═══════════════════════════════════════════════════════════════════════════
#  1.  add_speed
# ═══════════════════════════════════════════════════════════════════════════

def add_speed(words: list[dict]) -> list[dict]:
    """
    Add 'speed' to each word: duration (seconds) divided by number of letters.

    speed = (end - start) / len(word)

    Lower value → faster articulation.
    'speed' is None for words with no letters (e.g. pure symbols).
    Modifies the word dicts in-place and returns the list.
    """
    for w in words:
        duration = w["end"] - w["start"]
        n_letters = len(re.sub(r"[^a-zA-Z]", "", w["word"]))
        w["speed"] = round(duration / n_letters, 4) if n_letters > 0 else None
    return words


# ═══════════════════════════════════════════════════════════════════════════
#  2.  flag_if_filler — shared data
# ═══════════════════════════════════════════════════════════════════════════

# Always fillers regardless of position
ALWAYS_FILLERS: dict[str, str] = {
    # backchannels
    "yeah":  "backchannel",
    "yep":   "backchannel",
    "yup":   "backchannel",
    "okay":  "backchannel",
    "ok":    "backchannel",
    "k":     "backchannel",   # "K" as in "okay"
    "mhmm":  "backchannel",
    "mmm":   "backchannel",
    "uh-huh":"backchannel",
    # hesitations / filled pauses
    "uh":    "hesitation",
    "um":    "hesitation",
    "hmm":   "hesitation",
    "ah":    "hesitation",
    "er":    "hesitation",
    "erm":   "hesitation",
    # placeholder for unknown/forgotten word
    "x":     "placeholder",
}

# Multi-word filler patterns (match against consecutive word['word'] values).
# Listed longest-first so longer patterns win over sub-patterns.
MULTI_WORD_FILLERS: list[tuple[list[str], str]] = [
    (["you", "know", "what", "i", "mean"], "discourse_marker"),
    (["you", "know", "what"],              "discourse_marker"),
    (["let's", "say"],                     "discourse_marker"),
    (["lets",  "say"],                     "discourse_marker"),  # missing apostrophe
    (["you",   "know"],                    "discourse_marker"),
    (["i",     "mean"],                    "discourse_marker"),
    (["i",     "guess"],                   "discourse_marker"),
    (["kind",  "of"],                      "discourse_marker"),
    (["sort",  "of"],                      "discourse_marker"),
]

# Single-word fillers that depend on sentence position
# key → (filler_type, positions_allowed)   positions: 'initial', 'final', 'any'
POSITIONAL_FILLERS: dict[str, tuple[str, str]] = {
    "so":        ("discourse_marker", "initial"),  # sentence-initial pause/restart
    "well":      ("discourse_marker", "initial"),  # sentence-initial discourse marker
    "right":     ("backchannel",      "final"),    # sentence-final tic
    "actually":  ("discourse_marker", "initial"),  # reframing discourse marker
    "basically": ("discourse_marker", "initial"),
    "anyway":    ("discourse_marker", "any"),
    "like":      ("discourse_marker", "any"),      # discourse filler (not "would like to")
}

# Words that immediately precede "like" and indicate it is NOT a filler
_LIKE_CONTENT_PREV: set[str] = {
    "would", "could", "looks", "look", "sounds", "feel", "feels",
    "seemed", "seems", "taste", "tastes", "just", "nothing", "something",
    "anything",
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _sentence_positions(words: list[dict]) -> list[str]:
    """
    Return a list of the same length as words, each entry being:
      'initial'  — first word of its sentence
      'final'    — last word of its sentence
      'middle'   — any other position
    """
    n = len(words)
    positions: list[str] = ["middle"] * n
    for i, w in enumerate(words):
        sid = w["sentence_id"]
        is_first = (i == 0) or (words[i - 1]["sentence_id"] != sid)
        is_last  = (i == n - 1) or (words[i + 1]["sentence_id"] != sid)
        if is_first and is_last:
            positions[i] = "initial"   # single-word sentence
        elif is_first:
            positions[i] = "initial"
        elif is_last:
            positions[i] = "final"
    return positions


def _clear_filler(word: dict) -> None:
    word["is_filler"]      = False
    word["filler_type"]    = None
    word["filler_pattern"] = None


def _set_filler(word: dict, ftype: str, pattern: str) -> None:
    word["is_filler"]      = True
    word["filler_type"]    = ftype
    word["filler_pattern"] = pattern


# ═══════════════════════════════════════════════════════════════════════════
#  2a.  Lexicon method
# ═══════════════════════════════════════════════════════════════════════════

def _flag_fillers_lexicon(words: list[dict]) -> list[dict]:
    """Rule-based filler detection. Modifies words in-place."""
    n = len(words)
    positions = _sentence_positions(words)

    # Initialise all words as non-fillers
    for w in words:
        _clear_filler(w)

    # Mark multi-word patterns first (longest → shortest, first match wins)
    matched_indices: set[int] = set()
    for pattern, ftype in MULTI_WORD_FILLERS:
        k = len(pattern)
        for i in range(n - k + 1):
            if i in matched_indices:
                continue
            segment = [words[i + j]["word"].lower() for j in range(k)]
            if segment == pattern:
                pname = " ".join(pattern)
                for j in range(k):
                    _set_filler(words[i + j], ftype, pname)
                    matched_indices.add(i + j)

    # Mark single-word always-fillers
    for i, w in enumerate(words):
        if i in matched_indices:
            continue
        token = w["word"].lower()
        if token in ALWAYS_FILLERS:
            _set_filler(w, ALWAYS_FILLERS[token], token)
            matched_indices.add(i)

    # Mark positional fillers
    for i, w in enumerate(words):
        if i in matched_indices:
            continue
        token = w["word"].lower()
        if token not in POSITIONAL_FILLERS:
            continue
        ftype, allowed_pos = POSITIONAL_FILLERS[token]
        pos = positions[i]

        # Special case: "like" is a filler only when not preceded by a content verb
        if token == "like":
            prev_word = words[i - 1]["word"].lower() if i > 0 else ""
            if prev_word in _LIKE_CONTENT_PREV:
                continue

        if allowed_pos == "any" or pos == allowed_pos:
            _set_filler(w, ftype, token)
            matched_indices.add(i)

    return words


# ═══════════════════════════════════════════════════════════════════════════
#  2b.  LLM method (Anthropic claude-haiku-4-5)
# ═══════════════════════════════════════════════════════════════════════════

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

_LLM_BATCH = 25  # sentences per API call


def _flag_fillers_llm(words: list[dict]) -> list[dict]:
    """
    Use Anthropic claude-haiku-4-5 to detect fillers.
    Requires ANTHROPIC_API_KEY in environment.
    Falls back to lexicon on API error.
    """
    try:
        import anthropic
    except ImportError:
        print("anthropic package not installed — falling back to lexicon method.",
              file=sys.stderr)
        return _flag_fillers_lexicon(words)

    client = anthropic.Anthropic()

    # Initialise
    for w in words:
        _clear_filler(w)

    # Group words by sentence
    from collections import defaultdict
    sent_map: dict[int, list[tuple[int, dict]]] = defaultdict(list)
    for i, w in enumerate(words):
        sent_map[w["sentence_id"]].append((i, w))

    sentence_ids = sorted(sent_map.keys())

    # Process in batches
    for batch_start in range(0, len(sentence_ids), _LLM_BATCH):
        batch_sids = sentence_ids[batch_start: batch_start + _LLM_BATCH]

        # Build a flat numbered list for this batch
        # Format: global_word_index | sentence_id | word
        lines: list[str] = []
        for sid in batch_sids:
            for idx, w in sent_map[sid]:
                lines.append(f"{idx} | s{sid} | {w['punctuated_word']}")

        user_msg = "\n".join(lines)

        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1024,
                system=_LLM_SYSTEM,
                messages=[{"role": "user", "content": user_msg}],
            )
            raw = response.content[0].text.strip()
            # Strip markdown fences if model added them
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            hits = json.loads(raw)
        except Exception as exc:
            print(f"LLM batch error (sentences {batch_sids[0]}–{batch_sids[-1]}): {exc}",
                  file=sys.stderr)
            # Fallback: apply lexicon to this batch's words
            batch_words = [w for sid in batch_sids for _, w in sent_map[sid]]
            _flag_fillers_lexicon(batch_words)
            continue

        for hit in hits:
            idx      = hit.get("idx")
            ftype    = hit.get("filler_type", "discourse_marker")
            fpattern = hit.get("filler_pattern", words[idx]["word"] if idx is not None else "")
            if idx is not None and 0 <= idx < len(words):
                _set_filler(words[idx], ftype, fpattern)

    return words


# ═══════════════════════════════════════════════════════════════════════════
#  3.  Public entry point
# ═══════════════════════════════════════════════════════════════════════════

def flag_if_filler(words: list[dict], method: str = "lexicon") -> list[dict]:
    """
    Detect filler words and add three fields to each word object in-place:
      is_filler      bool   — True if this word is a filler
      filler_type    str|None — 'backchannel', 'hesitation', 'discourse_marker',
                                'placeholder', or None
      filler_pattern str|None — the matched pattern (e.g. "you know", "let's say")

    Parameters
    ----------
    words   : list of word dicts (from fluidity.json)
    method  : 'lexicon' (default) or 'llm'
    """
    if method == "llm":
        return _flag_fillers_llm(words)
    return _flag_fillers_lexicon(words)


# ═══════════════════════════════════════════════════════════════════════════
#  4.  CLI
# ═══════════════════════════════════════════════════════════════════════════

def process_file(path: Path, method: str) -> None:
    data  = json.loads(path.read_text(encoding="utf-8"))
    words = data["words"]

    add_speed(words)
    flag_if_filler(words, method=method)

    n_fillers = sum(1 for w in words if w["is_filler"])
    ftype_counts: dict[str, int] = {}
    for w in words:
        if w["is_filler"] and w["filler_type"]:
            ftype_counts[w["filler_type"]] = ftype_counts.get(w["filler_type"], 0) + 1

    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    summary = ", ".join(f"{k}={v}" for k, v in sorted(ftype_counts.items()))
    student = data.get("student", path.parent.parent.name)
    lesson  = data.get("lesson",  path.parent.name)
    print(f"  {student}/{lesson}: {len(words)} words, "
          f"{n_fillers} fillers [{summary}]  ({method})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="*", metavar="fluidity.json",
                        help="Specific fluidity.json files. Default: all lessons.")
    parser.add_argument("--method", choices=["lexicon", "llm"], default="lexicon",
                        help="Filler detection method (default: lexicon).")
    args = parser.parse_args()

    if args.files:
        paths = [Path(f) for f in args.files]
    else:
        paths = sorted(FLUIDITY_ROOT.rglob("fluidity.json"))

    if not paths:
        print("No fluidity.json files found.", file=sys.stderr)
        sys.exit(1)

    for p in paths:
        process_file(p, args.method)

    print(f"\nDone. Processed {len(paths)} file(s).")


if __name__ == "__main__":
    main()
