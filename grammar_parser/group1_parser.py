"""
Group1Parser: detects LEXICAL_TRIGGER grammar structures (MODALITY, NEGATION,
DISCOURSE MARKERS, CONJUNCTIONS, PREPOSITIONS) using spaCy Matcher against
strategy1_lexical_trigger.json.

Detection method: spacy.matcher.Matcher on token lemmas / lowercase forms or
POS/TAG sequences, with optional regex validation for complex conjunction patterns.

Detection fields used per category:
  MODALITY, NEGATION, DISCOURSE MARKERS: spacy_patterns (lemma/lowercase)
  CONJUNCTIONS: spacy_patterns + optional regex_pattern (e.g. "either…or")
  PREPOSITIONS: pos_patterns (TAG-based sequences)

Note: many MODALITY structures share the same modal-verb LEMMA pattern —
a single occurrence of "can" will correctly fire once per matching structure
(each has a distinct guideword representing a different grammatical use).

Note: patterns like {"LOWER": "wont"} target un-apostrophised forms only;
spaCy tokenises "won't" as ["wo", "n't"], so those contracted forms won't match.

Note: for CONJUNCTIONS rules that carry a regex_pattern, the Matcher provides
the candidate span and the regex is validated against the full sentence text.
A match is only reported when both the token pattern and the regex pass.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc

# ---------------------------------------------------------------------------
# CEFR level → numeric (A1=1 … C2=6). Exposed for callers that need sorting.
# ---------------------------------------------------------------------------
CEFR_NUMERIC: dict[str, int] = {
    "A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6,
}

_DEFAULT_JSON = Path(__file__).parent / "structures" / "strategy1_lexical_trigger.json"


def _normalise_patterns(raw: list) -> list:
    """Return patterns in [[token_dict, ...], ...] format for Matcher.add().

    Handles three input shapes found across the strategy JSON files:
      NESTED  [[{...}], [{...}]]  — already correct, return unchanged
      FLAT    [{...}, {...}]      — single multi-token pattern, wrap in a list
      MIXED   [[{...}], {...}]    — normalise each element individually

    Checking only raw[0] is fragile for mixed arrays, so each element is
    inspected explicitly.
    """
    if not raw:
        return raw
    if all(isinstance(p, list) for p in raw):   # already nested
        return raw
    if all(isinstance(p, dict) for p in raw):   # flat single pattern
        return [raw]
    # mixed: some elements are already patterns (lists), some are lone token dicts
    result = []
    for p in raw:
        if isinstance(p, list):
            result.append(p)
        elif isinstance(p, dict):
            result.append([p])
    return result


def _dep_disambiguate(
    cat_a: str, cat_b: str, start: int, end: int, doc: Doc
) -> str | None:
    """Apply spaCy DEP heuristics for known incompatible category pairs.

    Returns the winning category name, or None if the signal is inconclusive.
    Only called when both cat_a and cat_b have matches on the same span.

    Supported pairs (order-independent):
      PASSIVES / PRESENT  — disambiguates VBN spans (passive vs present perfect)
      PAST     / PASSIVES — disambiguates VBN tokens (simple past vs passive)
    """
    pair = frozenset({cat_a, cat_b})

    if pair == frozenset({"PASSIVES", "PRESENT"}):
        # Passive signal: nsubjpass dependency on any token in the span
        for i in range(start, end):
            if doc[i].dep_ == "nsubjpass":
                return "PASSIVES"
        # Passive signal: 'by' agent phrase within 5 tokens after the span
        for j in range(end, min(end + 5, len(doc))):
            if doc[j].lower_ == "by":
                return "PASSIVES"
        # Present progressive signal: VBG within 3 tokens after the span
        # (e.g. "has been working" — 'working' follows the auxiliary span)
        for j in range(end, min(end + 3, len(doc))):
            if doc[j].tag_ == "VBG":
                return "PRESENT"
        return None  # inconclusive

    if pair == frozenset({"PAST", "PASSIVES"}):
        # Passive signal: auxiliary 'be' immediately before the span
        if start > 0 and doc[start - 1].lemma_ == "be":
            return "PASSIVES"
        # Passive signal: nsubjpass on any token in the span
        for i in range(start, end):
            if doc[i].dep_ == "nsubjpass":
                return "PASSIVES"
        return "PAST"  # default: no auxiliary → simple past

    return None  # pair not handled


def _resolve_matches(
    matches: list[dict[str, Any]],
    doc: Doc,
    incompatible_pairs: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Resolve Tipo B conflicts: same span, mutually incompatible categories.

    For each pair (cat_a, cat_b) in incompatible_pairs, when both categories
    produce matches on the exact same (start_token, end_token), applies DEP
    heuristics via _dep_disambiguate to pick the winner. If heuristics are
    inconclusive, keeps the category with the lowest lowest_level_numeric
    (most basic structure).

    Tipo A (same category, multiple guidewords) is NOT filtered — all
    guidewords are pedagogically distinct and intentionally kept.

    Parameters
    ----------
    matches           : raw list of match dicts from parse()
    doc               : the spaCy Doc the matches came from
    incompatible_pairs: list of (cat_a, cat_b) that are mutually exclusive
                        when they share the same span
    """
    if not incompatible_pairs:
        return matches

    # Step 1a — Filter PASSIVES false positives (present perfect progressive).
    # Pattern [VBZ/VBP + VBN] is ambiguous: "has been seen" (passive) vs
    # "has been working" (present perfect progressive). When the span ends
    # immediately before a VBG token, it is progressive → drop PASSIVES.
    if any("PASSIVES" in pair for pair in incompatible_pairs):
        matches = [
            m for m in matches
            if not (
                m["category"] == "PASSIVES"
                and m["end_token"] < len(doc)
                and doc[m["end_token"]].tag_ == "VBG"
            )
        ]

    # Step 1b — Filter PAST false positives (passive auxiliary).
    # "was written" fires PAST on "was" (VBD), but spaCy marks it dep=auxpass
    # when it's a passive auxiliary, not a simple past main verb. Drop those.
    if any("PAST" in pair for pair in incompatible_pairs):
        matches = [
            m for m in matches
            if not (
                m["category"] == "PAST"
                and any(
                    doc[i].dep_ == "auxpass"
                    for i in range(m["start_token"], m["end_token"])
                )
            )
        ]

    # Step 2 — Same-span conflict resolution (Tipo B strict).
    by_span: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for m in matches:
        by_span[(m["start_token"], m["end_token"])].append(m)

    to_remove: set[tuple[str, int, int]] = set()

    for (start, end), span_matches in by_span.items():
        cats_present = {m["category"] for m in span_matches}
        for cat_a, cat_b in incompatible_pairs:
            if cat_a not in cats_present or cat_b not in cats_present:
                continue

            winner = _dep_disambiguate(cat_a, cat_b, start, end, doc)

            if winner is None:
                # Tiebreak: keep the category with the lowest minimum level
                a_min = min(
                    m["lowest_level_numeric"]
                    for m in span_matches if m["category"] == cat_a
                )
                b_min = min(
                    m["lowest_level_numeric"]
                    for m in span_matches if m["category"] == cat_b
                )
                winner = cat_a if a_min <= b_min else cat_b

            loser = cat_b if winner == cat_a else cat_a
            for m in span_matches:
                if m["category"] == loser:
                    to_remove.add((m["structure_id"], start, end))

    if not to_remove:
        return matches

    return [
        m for m in matches
        if (m["structure_id"], m["start_token"], m["end_token"]) not in to_remove
    ]


class Group1Parser:
    """
    Detects Strategy 1 (LEXICAL_TRIGGER) grammar structures in a spaCy Doc.

    Covers: MODALITY, NEGATION, DISCOURSE MARKERS, CONJUNCTIONS, PREPOSITIONS.

    Parameters
    ----------
    nlp : spacy.Language
        A loaded spaCy Language object. Used to create the Matcher vocab;
        the parser does NOT call nlp() internally — callers pass ready Docs.
    json_path : Path | str | None
        Path to strategy1_lexical_trigger.json. Defaults to the bundled file.
    resolve : bool
        If True, apply _resolve_matches after parsing to filter Tipo B
        conflicts (same span, incompatible categories). Default False.
    """

    def __init__(
        self,
        nlp: spacy.Language,
        json_path: Path | str | None = None,
        resolve: bool = False,
    ) -> None:
        self._matcher = Matcher(nlp.vocab)
        self._resolve = resolve
        # Group1 has no intra-parser incompatible pairs (MODALITY multi-guideword
        # matches on the same span are intentional — Tipo A, not Tipo B).
        self._incompatible_pairs: list[tuple[str, str]] = []
        # Maps structure_id → lightweight metadata dict (no examples/keywords).
        self.structures: dict[str, dict[str, Any]] = {}
        # Maps structure_id → compiled regex (only for rules that carry one).
        self._regex: dict[str, re.Pattern[str]] = {}

        path = Path(json_path) if json_path is not None else _DEFAULT_JSON
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        for structure in data["structures"]:
            sid = structure["id"]
            # Prefer spacy_patterns; fall back to pos_patterns (PREPOSITIONS).
            # Normalise to [[token_dict, ...], ...] before calling Matcher.add():
            #   - spacy_patterns is usually already nested [[{...}], ...]
            #   - pos_patterns is always flat [{...}] (single pattern, wrap it)
            #   - a handful of spacy_patterns are also stored flat [{...}] — wrap those too
            raw_spacy = structure.get("spacy_patterns")
            raw_pos   = structure.get("pos_patterns")
            if raw_spacy:
                patterns = _normalise_patterns(raw_spacy)
            elif raw_pos:
                patterns = [raw_pos]
            else:
                patterns = []

            if not patterns:
                continue

            self.structures[sid] = {
                "category": structure["category"],
                "guideword": structure["guideword"],
                "levels": structure["levels"],
                "lowest_level": structure["lowest_level"],
                "lowest_level_numeric": CEFR_NUMERIC.get(structure["lowest_level"], 0),
            }

            # Matcher.add(key, patterns) — patterns is a list of token-dict-lists,
            # exactly the format stored in spacy_patterns / pos_patterns in the JSON.
            self._matcher.add(sid, patterns)

            # Store compiled regex for rules that require post-hoc validation
            # (some CONJUNCTIONS patterns such as "either…or").
            raw_regex = structure.get("regex_pattern")
            if raw_regex:
                self._regex[sid] = re.compile(raw_regex)

    def parse(self, doc: Doc) -> list[dict[str, Any]]:
        """
        Run the Matcher against a spaCy Doc and return all detected structures.

        Parameters
        ----------
        doc : spacy.tokens.Doc
            A processed spaCy document (already passed through nlp()).

        Returns
        -------
        list of dict, each with keys:
            structure_id         str
            category             str   e.g. "MODALITY"
            guideword            str   e.g. "USE: ABILITY"
            levels               list  e.g. ["A1", "A2", "B1"]
            lowest_level         str   e.g. "A1"
            lowest_level_numeric int   1–6
            span_text            str   matched token(s) as a string
            start_token          int   start token index in doc
            end_token            int   end token index (exclusive)
        """
        raw_matches = self._matcher(doc)
        results: list[dict[str, Any]] = []
        seen: set[tuple[str, int, int]] = set()

        for match_id_int, start, end in raw_matches:
            sid = doc.vocab.strings[match_id_int]
            dedup_key = (sid, start, end)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)

            # For rules with a regex_pattern, validate against the full sentence
            # text. This handles patterns like "either…or" where the Matcher only
            # anchors on one token and the regex confirms the full construction.
            if sid in self._regex and not self._regex[sid].search(doc.text):
                continue

            meta = self.structures[sid]
            results.append({
                "structure_id": sid,
                "category": meta["category"],
                "guideword": meta["guideword"],
                "levels": meta["levels"],
                "lowest_level": meta["lowest_level"],
                "lowest_level_numeric": meta["lowest_level_numeric"],
                "span_text": doc[start:end].text,
                "start_token": start,
                "end_token": end,
            })

        if self._resolve:
            results = _resolve_matches(results, doc, self._incompatible_pairs)

        return results
