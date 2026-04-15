"""
Group3Parser: detects VERBAL_MORPHOLOGY grammar structures (PAST, PRESENT,
FUTURE, PASSIVES, VERBS) using spaCy Matcher against
strategy3_verbal_morphology.json.

Detection method: spacy.matcher.Matcher on verb TAG sequences (pos_patterns)
or lemma/TAG sequences (spacy_patterns), with optional regex validation.

Detection fields used per structure:
  pos_patterns only  (122 rules): TAG-based sequences, flat or nested
  spacy_patterns + regex_pattern (108 rules): lemma/TAG patterns with optional
    regex post-validation for complex tense constructions

Note: pos_patterns may be stored flat ([{TAG: ...}]) or nested
([[{TAG: ...}], ...]) — both are normalised before passing to Matcher.add().
spacy_patterns in this file are always already nested ([[token_dict, ...], ...]).

Note: regex_pattern may be present but set to null — only compile when non-null.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import spacy
from spacy.matcher import Matcher
from spacy.tokens import Doc

from .group1_parser import CEFR_NUMERIC, _normalise_patterns, _resolve_matches

_DEFAULT_JSON = Path(__file__).parent / "structures" / "strategy3_verbal_morphology.json"


class Group3Parser:
    """
    Detects Strategy 3 (VERBAL_MORPHOLOGY) grammar structures in a spaCy Doc.

    Covers: PAST, PRESENT, FUTURE, PASSIVES, VERBS.

    Parameters
    ----------
    nlp : spacy.Language
        A loaded spaCy Language object. Used to create the Matcher vocab;
        the parser does NOT call nlp() internally — callers pass ready Docs.
    json_path : Path | str | None
        Path to strategy3_verbal_morphology.json. Defaults to the bundled file.
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
        # Intra-parser incompatible pairs for VERBAL_MORPHOLOGY:
        #   PASSIVES / PRESENT  — same VBN span can be passive or present perfect
        #   PAST     / PASSIVES — same VBN span can be simple past or passive
        self._incompatible_pairs: list[tuple[str, str]] = [
            ("PASSIVES", "PRESENT"),
            ("PAST", "PASSIVES"),
        ]
        self.structures: dict[str, dict[str, Any]] = {}
        self._regex: dict[str, re.Pattern[str]] = {}

        path = Path(json_path) if json_path is not None else _DEFAULT_JSON
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        for structure in data["structures"]:
            sid = structure["id"]
            raw_spacy = structure.get("spacy_patterns")
            raw_pos   = structure.get("pos_patterns")

            if raw_spacy:
                # strategy3 spacy_patterns may be flat or nested — normalise
                patterns = _normalise_patterns(raw_spacy)
            elif raw_pos:
                # May be flat or nested — normalise
                patterns = _normalise_patterns(raw_pos)
            else:
                continue

            self.structures[sid] = {
                "category": structure["category"],
                "guideword": structure["guideword"],
                "levels": structure["levels"],
                "lowest_level": structure["lowest_level"],
                "lowest_level_numeric": CEFR_NUMERIC.get(structure["lowest_level"], 0),
            }

            self._matcher.add(sid, patterns)

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
            category             str   e.g. "PAST"
            guideword            str   e.g. "FORM: PAST SIMPLE, AFFIRMATIVE"
            levels               list  e.g. ["A1", "A2"]
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
