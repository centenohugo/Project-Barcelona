"""
ErrorChecker: runs LanguageTool on each sentence in a validated-sentence-separation.txt
and returns classified grammar error records.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import language_tool_python

from .rule_mapping import classify_rule

_WEIGHTS_PATH = Path(__file__).parent / "error_weights.json"


def _load_weights() -> dict[str, int]:
    """Return {grammar_category: weight} from error_weights.json."""
    data = json.loads(_WEIGHTS_PATH.read_text(encoding="utf-8"))
    return {cat: entry["weight"] for cat, entry in data["grammar_categories"].items()}


class ErrorChecker:
    """
    Wraps a LanguageTool instance. Reuse a single instance across multiple files
    to avoid repeated JVM startup.

    Parameters
    ----------
    language : str
        LanguageTool language code. Default "en-US".
    """

    def __init__(self, language: str = "en-US") -> None:
        self._lt = language_tool_python.LanguageTool(language)
        self._weights = _load_weights()

    def _classify_match(self, m: Any) -> dict[str, Any] | None:
        """Classify one LanguageTool match. Returns a partial record or None if discarded."""
        result = classify_rule(
            rule_id=m.rule_id,
            category=m.category,
            rule_issue_type=m.rule_issue_type,
            message=m.message,
        )
        if result is None:
            return None
        grammar_cat, dim_code, dim_label = result
        weight = self._weights.get(grammar_cat, 3)
        if weight == 0:
            return None
        return {
            "rule_id": m.rule_id,
            "grammar_category": grammar_cat,
            "dimension_code": dim_code,
            "dimension_label": dim_label,
            "weight": weight,
            "matched_text": m.matched_text,
            "message": m.message,
            "replacements": list(m.replacements),
            "offset": m.offset,
            "error_length": m.error_length,
        }

    def check_sentences(
        self,
        sentences: list[str],
        start_index: int = 1,
    ) -> list[dict[str, Any]]:
        """
        Run error detection on a list of sentence strings.

        Parameters
        ----------
        sentences   : list of sentence texts (one sentence per entry)
        start_index : sentence_index value for the first sentence (default 1)

        Returns the same record format as check_file.
        """
        records: list[dict[str, Any]] = []
        for idx, sentence in enumerate(sentences, start=start_index):
            for m in self._lt.check(sentence):
                partial = self._classify_match(m)
                if partial is not None:
                    records.append({"sentence": sentence, "sentence_index": idx, **partial})
        return records

    def check_file(self, path: Path | str) -> list[dict[str, Any]]:
        """
        Run error detection on every sentence in a validated-sentence-separation.txt.

        Returns a list of error records. Each record:
            sentence          str   the full sentence text
            sentence_index    int   1-based line number
            rule_id           str   exact LT rule ID
            grammar_category  str   medium-level teacher label
            dimension_code    str   "A" | "B" | "C" | "D"
            dimension_label   str   full dimension name
            weight            int   error severity weight (1–5)
            matched_text      str   the erroneous fragment
            message           str   LT explanation
            replacements      list  LT suggestions (may be empty)
            offset            int   char offset within sentence
            error_length      int   length of the error span
        """
        path = Path(path)
        sentences = [
            line.rstrip("\n")
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return self.check_sentences(sentences)

    def save(self, records: list[dict[str, Any]], out_path: Path | str) -> None:
        """Write records to a JSON file, creating parent directories as needed."""
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(records, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def close(self) -> None:
        """Shut down the LanguageTool JVM."""
        self._lt.close()

    def __enter__(self) -> "ErrorChecker":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
