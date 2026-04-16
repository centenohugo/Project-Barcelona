"""
Group4Parser: detects SYNTACTIC_STRUCTURE grammar structures (CLAUSES,
REPORTED SPEECH, FOCUS, QUESTIONS) using spaCy Matcher against
strategy4_syntactic_structure.json.

Detection method: spacy.matcher.Matcher on dependency relation (DEP)
sequences (dep_patterns) or lemma/TAG sequences (spacy_patterns), with
optional regex validation.

Detection fields used per structure:
  dep_patterns only  (165 rules): stored as [{type, pattern}] objects;
    the 'pattern' list ([{DEP: ...}]) is extracted and used with Matcher.
    The 'type' field is human-readable metadata and not used for matching.
  spacy_patterns + regex_pattern (33 rules): lemma/TAG patterns with optional
    regex post-validation, same as strategy1/3.

Note: both dep_patterns[].pattern and spacy_patterns in this file are stored
flat ([{attr: val}]) and are normalised before passing to Matcher.add().

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

from .group1_parser import CEFR_NUMERIC, _context_span, _normalise_patterns, _resolve_matches

_DEFAULT_JSON = Path(__file__).parent / "structures" / "strategy4_syntactic_structure.json"


class Group4Parser:
    """
    Detects Strategy 4 (SYNTACTIC_STRUCTURE) grammar structures in a spaCy Doc.

    Covers: CLAUSES, REPORTED SPEECH, FOCUS, QUESTIONS.

    Parameters
    ----------
    nlp : spacy.Language
        A loaded spaCy Language object. Used to create the Matcher vocab;
        the parser does NOT call nlp() internally — callers pass ready Docs.
    json_path : Path | str | None
        Path to strategy4_syntactic_structure.json. Defaults to the bundled file.
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
        # No intra-parser incompatible pairs identified yet for SYNTACTIC_STRUCTURE.
        self._incompatible_pairs: list[tuple[str, str]] = []
        self.structures: dict[str, dict[str, Any]] = {}
        self._regex: dict[str, re.Pattern[str]] = {}

        path = Path(json_path) if json_path is not None else _DEFAULT_JSON
        with path.open(encoding="utf-8") as fh:
            data = json.load(fh)

        for structure in data["structures"]:
            sid = structure["id"]
            raw_spacy = structure.get("spacy_patterns")
            raw_dep   = structure.get("dep_patterns")

            if raw_spacy:
                # Flat in strategy4 spacy_patterns — normalise
                patterns = _normalise_patterns(raw_spacy)
            elif raw_dep:
                # Each entry is {type, pattern}; extract the pattern list and
                # normalise. All entries in this file have exactly one item.
                raw_pattern = raw_dep[0]["pattern"]
                patterns = _normalise_patterns(raw_pattern)
            else:
                continue

            self.structures[sid] = {
                "category": structure["category"],
                "guideword": structure["guideword"],
                "levels": structure["levels"],
                "lowest_level": structure["lowest_level"],
                "lowest_level_numeric": CEFR_NUMERIC.get(structure["lowest_level"], 0),
                "explanation": structure.get("explanation", ""),
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
            category             str   e.g. "CLAUSES"
            guideword            str   e.g. "FORM/USE: 'BECAUSE', REASONS"
            levels               list  e.g. ["A2", "B1"]
            lowest_level         str   e.g. "A2"
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

            if sid in self._regex and not self._regex[sid].search(doc.text):
                continue

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
