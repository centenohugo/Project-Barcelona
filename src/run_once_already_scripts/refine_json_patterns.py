#!/usr/bin/env python3
"""
Refine spaCy patterns in strategy JSON files to reduce false positives.

Changes applied:
  strategy1 (LEXICAL_TRIGGER):
    - PREPOSITIONS: 9 structures all with generic {"TAG": "IN"}.  Add regex
      constraints where the guideword mentions a specific context word, then
      deduplicate the remaining generic ones.

  strategy2 (NOMINAL_POS):
    - PRONOUNS/DETERMINERS/ADVERBS: replace generic TAG with {"LOWER": word}
      when the guideword names specific function words.
    - ADJECTIVES/NOUNS/leftover generics: deduplicate identical-pattern groups,
      keeping the representative at the lowest CEFR level.

  strategy3 (VERBAL_MORPHOLOGY):
    - Add regex_pattern to structures whose guideword contains a specific
      context word ('YET', 'WHEN', 'ALREADY', etc.) so they only fire when
      that word is present in the sentence.
    - Deduplicate remaining structures with identical generic TAG patterns,
      keeping one representative per group at the lowest CEFR level.

  strategy4 (SYNTACTIC_STRUCTURE):
    - dep_patterns structures (165): add context-word regex from guideword,
      then deduplicate within each dep-type group.
    - QUESTIONS spacy_patterns (29 generic TAG): replace with specific
      auxiliary lemma where guideword names one, then add regex_pattern
      "(?i)\\?" so they only fire in interrogative sentences.  Deduplicate.

Strategy1 MODALITY/NEGATION/DISCOURSE MARKERS/CONJUNCTIONS are not modified —
they already use specific lemma patterns.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

STRUCTURES_DIR = Path(__file__).parent.parent / "grammar_parser" / "structures"

CEFR_NUMERIC = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}

# ---------------------------------------------------------------------------
# Functional word sets — used to identify specific lexical anchors in guidewords
# ---------------------------------------------------------------------------
PRONOUN_WORDS: set[str] = {
    "i", "me", "you", "him", "her", "it", "we", "us", "they", "them",
    "my", "your", "his", "its", "our", "their",
    "myself", "yourself", "himself", "herself", "itself",
    "ourselves", "yourselves", "themselves",
    "everything", "everyone", "everybody", "something", "someone",
    "anything", "anyone", "nothing", "nobody", "one", "ones",
    "this", "that", "these", "those",
    "mine", "yours", "hers", "ours", "theirs",
    "who", "whom", "whose", "which", "what",
}

DETERMINER_WORDS: set[str] = {
    "a", "an", "the",
    "this", "that", "these", "those",
    "every", "each", "either", "neither", "no",
    "some", "any", "both", "all",
    "another", "other",
    "much", "many", "few", "little", "more", "most",
}

ADVERB_WORDS: set[str] = {
    "very", "really", "quite", "rather", "pretty", "fairly", "extremely",
    "just", "so", "too", "also", "already", "yet", "still", "ever",
    "never", "always", "often", "sometimes", "usually", "rarely",
    "soon", "here", "there", "now", "then",
    "actually", "certainly", "definitely", "probably", "perhaps", "maybe",
    "even", "only", "nearly", "almost", "hardly", "barely",
}

# ---------------------------------------------------------------------------
# Context-word → regex map.
# Order matters: longer / more specific markers MUST come before shorter ones
# (e.g. 'IF ONLY' before 'IF').  Inflected verb forms are included so that
# "said" matches 'SAY', "got" matches 'GET', etc.
# ---------------------------------------------------------------------------
CONTEXT_REGEX_MAP: list[tuple[str, str]] = [
    # --- multi-word markers first ---
    ("'IF ONLY'",       r"(?i)\bif only\b"),
    ("'NO SOONER'",     r"(?i)\bno sooner\b"),
    ("'NOT ONLY'",      r"(?i)\bnot only\b"),
    ("'OR NOT'",        r"(?i)\bor not\b"),
    ("'SO THAT'",       r"(?i)\bso that\b"),
    ("'NOW THAT'",      r"(?i)\bnow that\b"),
    ("'IN ORDER'",      r"(?i)\bin order\b"),
    ("'IN CASE'",       r"(?i)\bin case\b"),
    ("'AS IF'",         r"(?i)\bas if\b"),
    ("'AS THOUGH'",     r"(?i)\bas though\b"),
    ("'AS LONG'",       r"(?i)\bas long\b"),
    ("'EVEN THOUGH'",   r"(?i)\beven though\b"),
    ("'EVEN IF'",       r"(?i)\beven if\b"),
    ("'NEITHER'",       r"(?i)\bneither\b"),
    ("'RATHER THAN'",   r"(?i)\brather than\b"),
    ("'LET ME'",        r"(?i)\blet me\b"),
    ("'LET'S'",         r"(?i)\blet'?s\b"),
    ("'WHAT A'",        r"(?i)\bwhat a\b"),
    # --- single-word markers ---
    ("'YET'",           r"(?i)\byet\b"),
    ("'WHEN'",          r"(?i)\bwhen\b"),
    ("'ALREADY'",       r"(?i)\balready\b"),
    ("'SINCE'",         r"(?i)\bsince\b"),
    ("'IF'",            r"(?i)\bif\b"),
    ("'BECAUSE'",       r"(?i)\bbecause\b"),
    ("'STILL'",         r"(?i)\bstill\b"),
    ("'REALLY'",        r"(?i)\breally\b"),
    ("'NEVER'",         r"(?i)\bnever\b"),
    ("'WISH'",          r"(?i)\b(wish|wishes|wished)\b"),
    ("'DID'",           r"(?i)\bdid\b"),
    ("'BY'",            r"(?i)\bby\b"),
    ("'GET'",           r"(?i)\b(get|gets|got|getting)\b"),
    ("'HAVE'",          r"(?i)\b(have|has|had)\b"),
    ("'SAY'",           r"(?i)\b(say|says|said)\b"),
    ("'TELL'",          r"(?i)\b(tell|tells|told)\b"),
    ("'ASK'",           r"(?i)\b(ask|asks|asked)\b"),
    ("'REPORT'",        r"(?i)\b(report|reports|reported)\b"),
    ("'CLAIM'",         r"(?i)\b(claim|claims|claimed)\b"),
    ("'HARDLY'",        r"(?i)\bhardly\b"),
    ("'SCARCELY'",      r"(?i)\bscarcely\b"),
    ("'HOWEVER'",       r"(?i)\bhowever\b"),
    ("'THOUGH'",        r"(?i)\bthough\b"),
    ("'WHERE'",         r"(?i)\bwhere\b"),
    ("'WHO'",           r"(?i)\bwho\b"),
    ("'WHICH'",         r"(?i)\bwhich\b"),
    ("'THAT'",          r"(?i)\bthat\b"),
    ("'FOR'",           r"(?i)\bfor\b"),
    ("'WHILE'",         r"(?i)\bwhile\b"),
    ("'BEFORE'",        r"(?i)\bbefore\b"),
    ("'AFTER'",         r"(?i)\bafter\b"),
    ("'ONCE'",          r"(?i)\bonce\b"),
    ("'UNTIL'",         r"(?i)\buntil\b"),
    ("'UNLESS'",        r"(?i)\bunless\b"),
    ("'HOW'",           r"(?i)\bhow\b"),
    ("'EITHER'",        r"(?i)\beither\b"),
    ("'NOR'",           r"(?i)\bnor\b"),
    ("'ENOUGH'",        r"(?i)\benough\b"),
    ("'TOO'",           r"(?i)\btoo\b"),
    ("'LET'",           r"(?i)\b(let|lets)\b"),
    ("'DO'",            r"(?i)\b(do|does|did)\b"),
    ("'IT'",            r"(?i)\bit\b"),
    ("'WHAT'",          r"(?i)\bwhat\b"),
    ("'THERE'",         r"(?i)\bthere\b"),
    ("'RIGHT'",         r"(?i)\bright\b"),
    ("'WH'",            r"(?i)\b(who|what|which|where|when|why|how|whom|whose)\b"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract_quoted_words(guideword: str) -> list[str]:
    """Return all single-quoted phrases from a guideword (without the quotes)."""
    return re.findall(r"'([^']+)'", guideword)


def is_single_word(phrase: str) -> bool:
    return len(phrase.split()) == 1


def make_lower_pattern(words: list[str]) -> dict:
    """Return a {"LOWER": ...} dict for one or more words."""
    if len(words) == 1:
        return {"LOWER": words[0]}
    return {"LOWER": {"IN": sorted(words)}}


def _dedup_key(s: dict) -> str:
    """Serialise the full detection pattern of a structure for dedup grouping."""
    pos = json.dumps(s.get("pos_patterns", []), sort_keys=True)
    spa = json.dumps(s.get("spacy_patterns", []), sort_keys=True)
    dep = json.dumps(s.get("dep_patterns", []), sort_keys=True)
    reg = s.get("regex_pattern") or ""
    return f"{pos}||{spa}||{dep}||{reg}"


def _is_generic(s: dict) -> bool:
    """True when no LOWER / LEMMA constraint is present in any pattern field."""
    combined = json.dumps({
        "p": s.get("pos_patterns", []),
        "sp": s.get("spacy_patterns", []),
    })
    return '"LOWER"' not in combined and '"LEMMA"' not in combined


def _dedup(structures: list[dict], only_generic: bool = True) -> tuple[list[dict], int]:
    """
    Deduplicate structures with the same detection key.
    Keeps one per group (lowest CEFR level; ties broken by shorter guideword).
    Returns (filtered_list, n_removed).
    """
    groups: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(structures):
        if only_generic and not _is_generic(s):
            continue
        groups[_dedup_key(s)].append(i)

    to_remove: set[int] = set()
    for key, idxs in groups.items():
        if len(idxs) <= 1:
            continue
        idxs_sorted = sorted(
            idxs,
            key=lambda i: (
                CEFR_NUMERIC.get(structures[i]["lowest_level"], 7),
                len(structures[i].get("guideword", "")),
            ),
        )
        for i in idxs_sorted[1:]:
            to_remove.add(i)

    filtered = [s for i, s in enumerate(structures) if i not in to_remove]
    return filtered, len(to_remove)


def _context_regex_for(guideword: str) -> str | None:
    """
    Scan guideword for context-word markers (longest first) and build a
    combined regex.  Returns None if no markers found.
    """
    guideword_upper = guideword.upper()
    matched_regexes: list[str] = []

    for marker, regex in CONTEXT_REGEX_MAP:
        if marker in guideword_upper:
            matched_regexes.append(regex)

    if not matched_regexes:
        return None
    if len(matched_regexes) == 1:
        return matched_regexes[0]

    # Combine multiple matches into one alternation regex
    bodies: list[str] = []
    for r in matched_regexes:
        m = re.match(r"\(\?i\)\\b(.+?)\\b$", r)
        bodies.append(m.group(1) if m else r)
    return r"(?i)\b(" + "|".join(bodies) + r")\b"


# ===========================================================================
# Strategy 1 — LEXICAL_TRIGGER (PREPOSITIONS only)
# ===========================================================================

def transform_strategy1(structures: list[dict]) -> tuple[list[dict], dict]:
    """
    - PREPOSITIONS: add context-word regex from guideword where possible.
    - All non-MODALITY categories: deduplicate structures that share the same
      detection pattern, keeping one representative per group at the lowest
      CEFR level.  MODALITY is explicitly excluded (Tipo A — user keeps all
      guidewords to preserve every semantic distinction of modal verbs).
    """
    modified = 0

    for s in structures:
        if s.get("category") != "PREPOSITIONS":
            continue
        if s.get("regex_pattern"):
            continue
        ctx_regex = _context_regex_for(s.get("guideword", ""))
        if ctx_regex:
            s["regex_pattern"] = ctx_regex
            modified += 1

    # Deduplicate everything except MODALITY
    modality = [s for s in structures if s["category"] == "MODALITY"]
    non_modality = [s for s in structures if s["category"] != "MODALITY"]
    non_modality, deduped = _dedup(non_modality, only_generic=False)
    structures = modality + non_modality

    return structures, {
        "modified": modified,
        "deduplicated": deduped,
        "unchanged": len(structures) - modified,
    }


# ===========================================================================
# Strategy 2 — NOMINAL_POS
# ===========================================================================

def transform_strategy2(structures: list[dict]) -> tuple[list[dict], dict]:
    """
    1. Replace generic TAG patterns with {"LOWER": word} where the guideword
       names specific function words (pronouns, determiners, adverbs).
    2. Deduplicate remaining structures with identical generic TAG patterns.
    """
    WORD_SETS: dict[str, set[str]] = {
        "PRONOUNS":    PRONOUN_WORDS,
        "DETERMINERS": DETERMINER_WORDS,
        "ADVERBS":     ADVERB_WORDS,
    }

    modified = 0

    for s in structures:
        cat = s["category"]
        word_set = WORD_SETS.get(cat)
        if word_set is None:
            continue

        guideword = s.get("guideword", "")
        quoted = extract_quoted_words(guideword)
        single = [w.strip().lower() for w in quoted if is_single_word(w)]
        matches = [w for w in single if w in word_set]

        if matches:
            s["pos_patterns"] = [make_lower_pattern(matches)]
            modified += 1

    # Deduplicate ALL structures per category (including LOWER-anchored ones),
    # so that multiple structures sharing the same LOWER pattern (e.g. multiple
    # "THIS" DETERMINER structures at different levels) collapse to the
    # lowest-level representative.  MODALITY in strategy1 is the intentional
    # exception (Tipo A) — not touched here.
    structures, deduped = _dedup(structures, only_generic=False)

    return structures, {
        "modified": modified,
        "deduplicated": deduped,
        "unchanged": len(structures) - modified,
    }


# ===========================================================================
# Strategy 3 — VERBAL_MORPHOLOGY
# ===========================================================================

def transform_strategy3(structures: list[dict]) -> tuple[list[dict], dict]:
    """
    1. Add regex_pattern to structures with context words in guideword.
    2. Deduplicate remaining generic-TAG structures by keeping lowest level.
    """
    modified = 0

    for s in structures:
        if s.get("regex_pattern"):
            continue
        ctx_regex = _context_regex_for(s.get("guideword", ""))
        if ctx_regex:
            s["regex_pattern"] = ctx_regex
            modified += 1

    structures, deduped = _dedup(structures, only_generic=True)

    return structures, {
        "modified": modified,
        "deduplicated": deduped,
        "unchanged": len(structures) - modified,
    }


# ===========================================================================
# Strategy 4 — SYNTACTIC_STRUCTURE
# ===========================================================================

_GENERIC_VERB_TAG_PAT = json.dumps(
    [{"TAG": {"IN": ["VBD", "VBZ", "VBP", "MD"]}}], sort_keys=True
)

_AUXILIARY_REPLACEMENTS: list[tuple[str, list[dict]]] = [
    ("'BE'",   [{"LEMMA": "be"}]),
    ("'HAVE'", [{"LEMMA": "have"}]),
    ("'DO'",   [{"LEMMA": "do"}]),
    ("MODAL",  [{"TAG": "MD"}]),
]


def transform_strategy4(structures: list[dict]) -> tuple[list[dict], dict]:
    """
    1. QUESTIONS spacy_patterns: swap to specific aux lemma where guideword
       names one, then add regex_pattern "(?i)\\?" (question mark required).
    2. dep_patterns (CLAUSES / REPORTED SPEECH / FOCUS): add context-word
       regex from guideword where possible.
    3. Deduplicate:
       - spacy_patterns QUESTIONS among themselves.
       - dep_patterns among themselves per (dep-type × pattern × regex) group.
    """
    modified_q = 0
    modified_dep = 0
    regex_q = r"(?i)\?"

    # Step 1 — refine QUESTIONS spacy_patterns
    for s in structures:
        if s.get("category") != "QUESTIONS":
            continue
        spacy = s.get("spacy_patterns")
        if not spacy:
            continue
        if json.dumps(spacy, sort_keys=True) != _GENERIC_VERB_TAG_PAT:
            continue
        if s.get("regex_pattern"):
            continue

        guideword_upper = s.get("guideword", "").upper()
        new_pat = None
        for keyword, replacement in _AUXILIARY_REPLACEMENTS:
            if keyword in guideword_upper:
                new_pat = replacement
                break

        if new_pat is not None:
            s["spacy_patterns"] = new_pat
        s["regex_pattern"] = regex_q
        modified_q += 1

    # Step 2 — add context-word regex to dep_patterns structures
    for s in structures:
        if "dep_patterns" not in s:
            continue
        if s.get("regex_pattern"):
            continue
        ctx_regex = _context_regex_for(s.get("guideword", ""))
        if ctx_regex:
            s["regex_pattern"] = ctx_regex
            modified_dep += 1

    # Step 3 — deduplicate (dep and spacy separately to avoid cross-mixing)
    dep_structs = [s for s in structures if "dep_patterns" in s]
    spa_structs = [s for s in structures if "spacy_patterns" in s]

    dep_structs, deduped_dep = _dedup(dep_structs, only_generic=False)
    spa_structs, deduped_spa = _dedup(spa_structs, only_generic=False)

    structures = dep_structs + spa_structs

    return structures, {
        "modified": modified_q + modified_dep,
        "deduplicated": deduped_dep + deduped_spa,
        "unchanged": len(structures) - (modified_q + modified_dep),
    }


# ===========================================================================
# Main
# ===========================================================================

def process_file(path: Path, transform_fn) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    original_count = len(data["structures"])

    updated, stats = transform_fn(data["structures"])
    data["structures"] = updated
    data["total_structures"] = len(updated)

    cat_counts: dict[str, int] = defaultdict(int)
    level_counts: dict[str, int] = {"A1": 0, "A2": 0, "B1": 0, "B2": 0, "C1": 0, "C2": 0}
    for s in updated:
        cat_counts[s["category"]] += 1
        lvl = s.get("lowest_level", "")
        if lvl in level_counts:
            level_counts[lvl] += 1

    data["categories"] = dict(cat_counts)
    data["level_distribution"] = level_counts

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    print("%s" % path.name)
    print("  Structures: %d -> %d" % (original_count, len(updated)))
    print("  Modified (new regex/pattern): %d" % stats["modified"])
    print("  Deduplicated (removed):       %d" % stats["deduplicated"])
    print()


def main() -> None:
    print("Refining spaCy patterns in strategy JSON files...")
    print()

    process_file(
        STRUCTURES_DIR / "strategy1_lexical_trigger.json",
        transform_strategy1,
    )
    process_file(
        STRUCTURES_DIR / "strategy2_nominal_pos.json",
        transform_strategy2,
    )
    process_file(
        STRUCTURES_DIR / "strategy3_verbal_morphology.json",
        transform_strategy3,
    )
    process_file(
        STRUCTURES_DIR / "strategy4_syntactic_structure.json",
        transform_strategy4,
    )

    print("Done.")


if __name__ == "__main__":
    main()
