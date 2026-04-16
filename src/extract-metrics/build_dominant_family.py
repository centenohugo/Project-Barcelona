"""
src/extract-metrics/build_dominant_family.py

Finds the dominant word family per lesson — the morphological family whose
members (distinct surface forms from the same derivational root) appear
the most in the lesson.

Algorithm:
  1. Lemmatise every content word with NLTK morphy (handles inflections:
     teach/teaches/teaching/taught → "teach").
  2. For each canonical lemma, fetch its DIRECT WordNet derivationally_related_forms.
     No union-find — only 1-hop, direct connections. This prevents transitive
     chains that would merge unrelated words.
  3. A "star" = one canonical lemma + its direct derivational relatives
     (all filtered to lemmas that appear in the lesson).
  4. Each star is expanded back to all surface forms found in the lesson.
  5. The dominant family = the star with the most distinct surface members.
  6. Stem-only fallback if NLTK WordNet is unavailable.

Reads:
  src/vocabulary/output/{student}_{lesson}_contextual.json

Writes:
  data/processed/{student}/{lesson}/vocabulary/dominant_family.json

Usage:
  python src/extract-metrics/build_dominant_family.py                   # all lessons
  python src/extract-metrics/build_dominant_family.py Student-1 lesson-1
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT       = Path(__file__).parent.parent.parent
CONTEXTUAL = ROOT / "src" / "vocabulary" / "output"
PROC       = ROOT / "data" / "processed"

# ── Thresholds ────────────────────────────────────────────────────────────────
CONF_THRESHOLD  = 0.55
MIN_FAMILY_SIZE = 2     # a family needs at least this many distinct surface forms

# ── CEFR helpers ──────────────────────────────────────────────────────────────
CEFR_NUM: dict[str, int] = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
NUM_CEFR: dict[int, str] = {v: k for k, v in CEFR_NUM.items()}

# ── Function-word filter ──────────────────────────────────────────────────────
FUNCTION_WORDS = frozenset({
    "the", "a", "an", "is", "are", "was", "were", "am", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "shall", "should", "may", "might", "can", "could", "must",
    "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us",
    "them", "my", "your", "his", "its", "our", "their",
    "this", "that", "these", "those",
    "and", "but", "or", "nor", "for", "yet", "so",
    "in", "on", "at", "to", "from", "by", "with", "of", "about",
    "up", "out", "off", "over", "under", "into", "onto", "upon",
    "through", "between", "among", "before", "after", "during",
    "since", "until", "not", "no", "if", "then", "than",
    "when", "where", "who", "what", "which", "how",
    "there", "here", "very", "just", "also", "too",
    "as", "all", "each", "every", "both", "some", "any",
    "much", "many", "more", "most", "such",
    "oh", "yeah", "yes", "ok", "okay", "um", "uh", "ah",
    "well", "right", "like", "so", "now", "then",
    "get", "got", "go", "went", "said", "say",
})


def is_content(word: str, source: str, cefr: str) -> bool:
    w = word.lower()
    return (
        w not in FUNCTION_WORDS
        and len(w) >= 3
        and w.isalpha()
        and cefr != "UNKNOWN"
        and source not in ("digit", "none", "whitelist")
    )


# ── NLTK setup ────────────────────────────────────────────────────────────────
try:
    import nltk
    from nltk.corpus import wordnet as wn
    from nltk.stem import PorterStemmer

    nltk.download("wordnet", quiet=True)
    nltk.download("omw-1.4", quiet=True)

    _STEMMER = PorterStemmer()
    _WN = True

    _WN_POS = (wn.VERB, wn.NOUN, wn.ADJ, wn.ADV)

    def _morphy(word: str) -> str:
        """Return the shortest morphy form across all POS (best base form)."""
        best = word
        for pos in _WN_POS:
            cand = wn.morphy(word, pos)
            if cand and len(cand) < len(best):
                best = cand
        return best

    def _derivational_relatives(lemma: str) -> set[str]:
        """Direct WordNet derivationally_related_forms for a lemma (1-hop only)."""
        rels: set[str] = set()
        for synset in wn.synsets(lemma):
            for wn_lemma in synset.lemmas():
                for rel in wn_lemma.derivationally_related_forms():
                    r = rel.name().lower().replace("_", " ")
                    if r != lemma:
                        rels.add(r)
        return rels

except Exception:
    _WN = False
    _STEMMER = None  # type: ignore

    def _morphy(word: str) -> str:  # type: ignore[misc]
        return word

    def _derivational_relatives(lemma: str) -> set[str]:  # type: ignore[misc]
        return set()


# ── Stem fallback (no WordNet) ─────────────────────────────────────────────────
def _stem_families(vocab: set[str], occ: Counter) -> list[list[str]]:
    from collections import defaultdict
    groups: dict[str, list[str]] = defaultdict(list)
    for w in vocab:
        if _STEMMER:
            stem = _STEMMER.stem(w)
        else:
            # Very basic: strip common suffixes
            stem = w
            for suf in ("tion", "sion", "ness", "ment", "ity", "ing", "er",
                        "ed", "ly", "al", "ive", "ous", "ful", "less"):
                if w.endswith(suf) and len(w) - len(suf) >= 3:
                    stem = w[: -len(suf)]
                    break
        groups[stem].append(w)
    return [sorted(v, key=lambda m: -occ[m]) for v in groups.values() if len(v) >= MIN_FAMILY_SIZE]


# ── Core family builder ───────────────────────────────────────────────────────
def build_families(words_data: list[dict]) -> list[dict]:
    """
    Return a list of family dicts sorted by member_count desc, total_occurrences desc.
    Each dict has: root, method, members, member_count, total_occurrences,
                   avg_cefr_numeric, cefr_range.
    """
    # ── Collect per-word stats ────────────────────────────────────────────────
    occ: Counter[str] = Counter()
    cefr_map: dict[str, str] = {}

    for entry in words_data:
        w = entry["word"].lower()
        conf = float(entry.get("confidence", 0.0))
        cefr = entry.get("cefr_level", "UNKNOWN")
        source = entry.get("source", "")

        if not is_content(w, source, cefr):
            continue
        if conf < CONF_THRESHOLD:
            continue

        occ[w] += 1
        if w not in cefr_map:
            cefr_map[w] = cefr

    vocab = set(occ.keys())
    if len(vocab) < 2:
        return []

    # ── Lemmatise: surface form → canonical lemma ─────────────────────────────
    surface_to_lemma: dict[str, str] = {w: _morphy(w) for w in vocab}
    lemma_to_surfaces: dict[str, set[str]] = defaultdict(set)
    for surface, lemma in surface_to_lemma.items():
        lemma_to_surfaces[lemma].add(surface)

    lemma_vocab = set(lemma_to_surfaces.keys())

    # ── WordNet star families ─────────────────────────────────────────────────
    families: list[dict] = []

    if _WN:
        # Direct relatives per lemma (1-hop, no transitivity)
        lemma_direct: dict[str, set[str]] = {}
        for lemma in lemma_vocab:
            raw_rels = _derivational_relatives(lemma)
            # Keep only relatives whose lemma (or morphy) maps to our vocab
            direct: set[str] = set()
            for r in raw_rels:
                r_base = _morphy(r)
                if r_base in lemma_vocab and r_base != lemma:
                    direct.add(r_base)
                elif r in lemma_vocab and r != lemma:
                    direct.add(r)
            lemma_direct[lemma] = direct

        # Build one star per lemma; deduplicate identical stars
        seen_stars: set[frozenset] = set()
        for root_lemma, direct_rels in lemma_direct.items():
            if not direct_rels:
                continue
            family_lemmas = frozenset({root_lemma} | direct_rels)
            if family_lemmas in seen_stars:
                continue
            seen_stars.add(family_lemmas)

            # Collect all surface forms present in the lesson
            surfaces: set[str] = set()
            for lm in family_lemmas:
                surfaces.update(lemma_to_surfaces.get(lm, set()))
            surfaces &= vocab

            if len(surfaces) < MIN_FAMILY_SIZE:
                continue

            # Pick root as the lemma with the most direct relatives (most "central")
            root = max(
                family_lemmas,
                key=lambda lm: (len(lemma_direct.get(lm, set())), -len(lm)),
            )
            families.append(_make_entry(root, surfaces, occ, cefr_map, "wordnet"))

    # ── Stem fallback for any uncovered words ─────────────────────────────────
    covered = {s for f in families for m in f["members"] for s in [m["word"]]}
    remaining = vocab - covered

    if remaining:
        for members in _stem_families(remaining, occ):
            if len(members) < MIN_FAMILY_SIZE:
                continue
            root = min(members, key=len)
            families.append(_make_entry(root, set(members), occ, cefr_map, "stem"))

    families.sort(key=lambda f: (-f["member_count"], -f["total_occurrences"]))
    return families


def _make_entry(
    root: str,
    surfaces: set[str],
    occ: Counter,
    cefr_map: dict[str, str],
    method: str,
) -> dict:
    members_sorted = sorted(surfaces, key=lambda m: -occ[m])
    levels_num = [CEFR_NUM.get(cefr_map.get(m, "A1"), 1) for m in surfaces]
    avg_cefr = sum(levels_num) / len(levels_num)
    cefr_range = [
        NUM_CEFR.get(min(levels_num), "A1"),
        NUM_CEFR.get(max(levels_num), "A1"),
    ]
    return {
        "root": root,
        "method": method,
        "members": [
            {
                "word": m,
                "occurrences": occ[m],
                "cefr_level": cefr_map.get(m, "A1"),
            }
            for m in members_sorted
        ],
        "member_count": len(surfaces),
        "total_occurrences": sum(occ[m] for m in surfaces),
        "avg_cefr_numeric": round(avg_cefr, 2),
        "cefr_range": cefr_range,
    }


# ── Per-lesson runner ─────────────────────────────────────────────────────────
def process_lesson(student: str, lesson: str) -> bool:
    lesson_key = lesson if lesson.startswith("lesson-") else f"lesson-{lesson}"

    ctx_path = CONTEXTUAL / f"{student}_{lesson_key}_contextual.json"
    out_dir  = PROC / student / lesson_key / "vocabulary"
    out_path = out_dir / "dominant_family.json"

    if not ctx_path.exists():
        print(f"  SKIP {student}/{lesson_key}: contextual file not found")
        return False

    with open(ctx_path, encoding="utf-8") as f:
        ctx = json.load(f)

    families = build_families(ctx.get("words", []))

    if not families:
        print(f"  {student}/{lesson_key}: no families found")
        return False

    dominant = families[0]
    result = {
        "student": student,
        "lesson": lesson_key,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "wn_available": _WN,
        "dominant_family": dominant,
        "top_families": families[:10],
        "total_families_found": len(families),
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    members_preview = [m["word"] for m in dominant["members"][:6]]
    print(
        f"  {student}/{lesson_key}: "
        f"dominant={dominant['root']!r} "
        f"({dominant['member_count']} members, "
        f"{dominant['total_occurrences']} occ): "
        f"{members_preview}"
    )
    return True


# ── Lesson discovery ──────────────────────────────────────────────────────────
def discover_lessons() -> list[tuple[str, str]]:
    pairs = []
    for p in sorted(CONTEXTUAL.glob("*_lesson-*_contextual.json")):
        stem = p.stem.replace("_contextual", "")
        idx = stem.rfind("_lesson-")
        if idx != -1:
            pairs.append((stem[:idx], stem[idx + 1:]))
    return pairs


# ── CLI ────────────────────────────────────────────────────────────────────────
def main() -> None:
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        pairs = discover_lessons()
        if not pairs:
            print("No contextual files found in", CONTEXTUAL)
            return
        for student, lesson in pairs:
            process_lesson(student, lesson)
    else:
        print("Usage: build_dominant_family.py [student lesson]")
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
