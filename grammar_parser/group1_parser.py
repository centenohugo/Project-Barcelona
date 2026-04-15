"""
Group1Parser: detects token-based grammar structures (MODALITY, NEGATION,
DISCOURSE MARKERS) using spaCy Matcher against group1_tokens.json.

Detection method: spacy.matcher.Matcher on token lemmas / lowercase forms.

Note: many MODALITY structures share the same modal-verb LEMMA pattern —
a single occurrence of "can" will correctly fire once per matching structure
(each has a distinct guideword representing a different grammatical use).

Note: patterns like {"LOWER": "wont"} target un-apostrophised forms only;
spaCy tokenises "won't" as ["wo", "n't"], so those contracted forms won't match.
"""

from __future__ import annotations

import json
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

_DEFAULT_JSON = Path(__file__).parent / "structures" / "group1_tokens.json"


class Group1Parser:
    """
    Detects Group 1 grammar structures (token-based) in a spaCy Doc.

    Parameters
    ----------
    nlp : spacy.Language
        A loaded spaCy Language object. Used to create the Matcher vocab;
        the parser does NOT call nlp() internally — callers pass ready Docs.
    json_path : Path | str | None
        Path to group1_tokens.json. Defaults to the bundled file.
    """

    def __init__(
        self,
        nlp: spacy.Language,
        json_path: Path | str | None = None,
    ) -> None:
        self._matcher = Matcher(nlp.vocab)
        # Maps structure_id → lightweight metadata dict (no examples/keywords).
        self.structures: dict[str, dict[str, Any]] = {}

        path = Path(json_path) if json_path is not None else _DEFAULT_JSON
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        for structure in data["structures"]:
            sid = structure["id"]
            patterns = structure.get("spacy_patterns", [])

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
            # exactly the format stored in spacy_patterns in the JSON.
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
