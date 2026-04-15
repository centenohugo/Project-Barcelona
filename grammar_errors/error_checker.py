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
            matched_text      str   the erroneous fragment
            message           str   LT explanation
            replacements      list  LT suggestions (may be empty)
            offset            int   char offset within sentence
            error_length      int   length of the error span
        """
        path = Path(path)
        records: list[dict[str, Any]] = []

        sentences = [
            line.rstrip("\n")
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

        for idx, sentence in enumerate(sentences, start=1):
            matches = self._lt.check(sentence)
            for m in matches:
                result = classify_rule(
                    rule_id=m.rule_id,
                    category=m.category,
                    rule_issue_type=m.rule_issue_type,
                    message=m.message,
                )
                if result is None:
                    continue  # blacklisted or non-grammar

                grammar_cat, dim_code, dim_label = result

                records.append({
                    "sentence": sentence,
                    "sentence_index": idx,
                    "rule_id": m.rule_id,
                    "grammar_category": grammar_cat,
                    "dimension_code": dim_code,
                    "dimension_label": dim_label,
                    "matched_text": m.matched_text,
                    "message": m.message,
                    "replacements": list(m.replacements),
                    "offset": m.offset,
                    "error_length": m.error_length,
                })

        return records

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
