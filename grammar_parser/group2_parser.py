"""
Group2Parser: detects NOMINAL_POS grammar structures (PRONOUNS, DETERMINERS,
NOUNS, ADJECTIVES, ADVERBS) using spaCy Matcher against
strategy2_nominal_pos.json.

Detection method: spacy.matcher.Matcher on POS/TAG sequences.

Detection fields used per category:
  ALL categories: pos_patterns (TAG-based single-token sequences)

Note: many structures within each category share the same POS/TAG pattern —
a single token of that TAG will correctly fire once per matching structure
(each has a distinct guideword representing a different grammatical use).
This is by design: the parser detects the presence of a nominal-level feature;
callers use the guideword and CEFR level to interpret the result.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc

from .group1_parser import CEFR_NUMERIC, _context_span, _normalise_patterns, _resolve_matches

_DEFAULT_JSON = Path(__file__).parent / "structures" / "strategy2_nominal_pos.json"


class Group2Parser:
    """
    Detects Strategy 2 (NOMINAL_POS) grammar structures in a spaCy Doc.

    Covers: PRONOUNS, DETERMINERS, NOUNS, ADJECTIVES, ADVERBS.

    Parameters
    ----------
    nlp : spacy.Language
        A loaded spaCy Language object. Used to create the Matcher vocab;
        the parser does NOT call nlp() internally — callers pass ready Docs.
    json_path : Path | str | None
        Path to strategy2_nominal_pos.json. Defaults to the bundled file.
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
        # No intra-parser incompatible pairs identified for NOMINAL_POS.
        self._incompatible_pairs: list[tuple[str, str]] = []
        # Maps structure_id → lightweight metadata dict (no examples).
        self.structures: dict[str, dict[str, Any]] = {}

        path = Path(json_path) if json_path is not None else _DEFAULT_JSON
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        for structure in data["structures"]:
            sid = structure["id"]
            raw_pos = structure.get("pos_patterns")
            if not raw_pos:
                continue

            patterns = _normalise_patterns(raw_pos)

            self.structures[sid] = {
                "category": structure["category"],
                "guideword": structure["guideword"],
                "levels": structure["levels"],
                "lowest_level": structure["lowest_level"],
                "lowest_level_numeric": CEFR_NUMERIC.get(structure["lowest_level"], 0),
                "explanation": structure.get("explanation", ""),
            }

            self._matcher.add(sid, patterns)

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
            category             str   e.g. "PRONOUNS"
            guideword            str   e.g. "FORM: (SUBJECT) STATEMENTS"
            levels               list  e.g. ["A1"]
            lowest_level         str   e.g. "A1"
            lowest_level_numeric int   1–6
            explanation          str   human-readable description of the rule
            span_text            str   matched token(s) as a string
            start_token          int   start token index in doc
            end_token            int   end token index (exclusive)
            context_start_token  int   start of wider visualization context
            context_end_token    int   end of wider visualization context
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

            meta = self.structures[sid]
            ctx_start, ctx_end = _context_span(doc, start, end)
            results.append({
                "structure_id": sid,
                "category": meta["category"],
                "guideword": meta["guideword"],
                "levels": meta["levels"],
                "lowest_level": meta["lowest_level"],
                "lowest_level_numeric": meta["lowest_level_numeric"],
                "explanation": meta["explanation"],
                "span_text": doc[start:end].text,
                "start_token": start,
                "end_token": end,
                "context_start_token": ctx_start,
                "context_end_token": ctx_end,
            })

        if self._resolve:
            results = _resolve_matches(results, doc, self._incompatible_pairs)

        return results
