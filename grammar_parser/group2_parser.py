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

from .group1_parser import CEFR_NUMERIC  # shared mapping, no duplication

_DEFAULT_JSON = Path(__file__).parent / "structures" / "strategy2_nominal_pos.json"


def _normalise_patterns(raw: list) -> list:
    """Ensure patterns are in [[token_dict, ...], ...] format.

    pos_patterns in strategy2 are always stored as a flat list of token dicts
    [{"TAG": ...}], representing a single pattern. Wrap to [[{...}]].
    """
    if raw and isinstance(raw[0], dict):
        return [raw]
    return raw


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
    """

    def __init__(
        self,
        nlp: spacy.Language,
        json_path: Path | str | None = None,
    ) -> None:
        self._matcher = Matcher(nlp.vocab)
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

        return results
