#!/usr/bin/env python
"""
check_grammar_errors.py — run LanguageTool grammar error detection on all lessons.

Usage:
    python check_grammar_errors.py            # process all lessons
    python check_grammar_errors.py <path>     # process a single validated-*.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

from grammar_errors import ErrorChecker

ROOT = Path(__file__).parent
SENTENCES_DIR = ROOT / "processed_data" / "sentences"
ERRORS_DIR    = ROOT / "processed_data" / "errors"


def output_path(input_path: Path) -> Path:
    # .../sentences/Student-N/lesson-N/validated-*.txt
    # → .../errors/Student-N/lesson-N/grammar_errors.json
    rel = input_path.resolve().parent.relative_to(SENTENCES_DIR)
    return ERRORS_DIR / rel / "grammar_errors.json"


def process(checker: ErrorChecker, src: Path) -> None:
    out = output_path(src)
    records = checker.check_file(src)
    checker.save(records, out)
    print(f"  {src.parent.parent.name}/{src.parent.name}: {len(records)} errors -> {out}")


def main() -> None:
    with ErrorChecker() as checker:
        if len(sys.argv) > 1:
            process(checker, Path(sys.argv[1]))
        else:
            files = sorted(SENTENCES_DIR.rglob("validated-sentence-separation.txt"))
            print(f"Found {len(files)} lesson file(s).")
            for f in files:
                process(checker, f)


if __name__ == "__main__":
    main()
