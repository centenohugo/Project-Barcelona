"""
filter_overfire_rules.py

Removes grammar rules from the strategy JSON files whose fire rate (fraction of
lesson sentences that trigger the rule) exceeds a level-dependent threshold.

Rationale: rules that fire very frequently at high CEFR levels (B2-C2) cause
overestimation of learner proficiency — a student saying "can" should not get
credit for 40+ B2-C2 MODALITY structures that share the same pattern.

Thresholds (fire_rate = matches / total_sentences):
  A2 : > 25%   (~374 / 1495)
  B1 : > 15%   (~224 / 1495)
  B2 : >  8%   (~120 / 1495)
  C1 : >  5%   (~ 75 / 1495)
  C2 : >  5%   (~ 75 / 1495)

Run from repo root:
    source .venv/Scripts/activate
    python scripts/filter_overfire_rules.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

STRATEGY_FILES = [
    REPO_ROOT / "grammar_parser" / "structures" / "strategy1_lexical_trigger.json",
    REPO_ROOT / "grammar_parser" / "structures" / "strategy2_nominal_pos.json",
    REPO_ROOT / "grammar_parser" / "structures" / "strategy3_verbal_morphology.json",
    REPO_ROOT / "grammar_parser" / "structures" / "strategy4_syntactic_structure.json",
]

LESSON_GLOB = "processed_data/sentences/**/validated-sentence-separation.txt"

FIRE_RATE_THRESHOLDS: dict[str, float] = {
    "A2": 0.25,
    "B1": 0.15,
    "B2": 0.08,
    "C1": 0.05,
    "C2": 0.05,
}


# ---------------------------------------------------------------------------
# Step 1 — count fire rates across all lesson data
# ---------------------------------------------------------------------------
def compute_fire_rates(total_sentences: int) -> dict[str, float]:
    import spacy
    from grammar_parser import Group1Parser, Group2Parser, Group3Parser, Group4Parser

    nlp = spacy.load("en_core_web_sm")
    parsers = [
        Group1Parser(nlp, resolve=True),
        Group2Parser(nlp, resolve=True),
        Group3Parser(nlp, resolve=True),
        Group4Parser(nlp, resolve=True),
    ]

    lesson_paths = list(REPO_ROOT.glob(LESSON_GLOB))
    rule_counts: Counter[str] = Counter()

    for lp in lesson_paths:
        sentences = [l.strip() for l in lp.read_text(encoding="utf-8").splitlines() if l.strip()]
        docs = list(nlp.pipe(sentences))
        for doc in docs:
            seen: set[tuple] = set()
            for parser in parsers:
                for m in parser.parse(doc):
                    key = (m["structure_id"], m["start_token"], m["end_token"])
                    if key not in seen:
                        seen.add(key)
                        rule_counts[m["structure_id"]] += 1

    return {sid: count / total_sentences for sid, count in rule_counts.items()}


def count_total_sentences() -> int:
    total = 0
    for lp in REPO_ROOT.glob(LESSON_GLOB):
        total += sum(1 for l in lp.read_text(encoding="utf-8").splitlines() if l.strip())
    return total


# ---------------------------------------------------------------------------
# Step 2 — filter each JSON and rewrite in place
# ---------------------------------------------------------------------------
def filter_file(
    path: Path,
    fire_rates: dict[str, float],
) -> tuple[int, int, dict[str, list[str]]]:
    """Return (kept, removed, removed_by_level)."""
    data = json.loads(path.read_text(encoding="utf-8"))
    original = data["structures"]
    kept = []
    removed_by_level: dict[str, list[str]] = {}

    for s in original:
        sid = s["id"]
        level = s.get("lowest_level", "")
        threshold = FIRE_RATE_THRESHOLDS.get(level)
        rate = fire_rates.get(sid, 0.0)

        if threshold is not None and rate > threshold:
            removed_by_level.setdefault(level, []).append(
                f"{rate*100:.1f}%  {s['category']}  {s['guideword']}"
            )
        else:
            kept.append(s)

    # Recompute metadata
    from collections import Counter as C
    data["structures"] = kept
    data["total_structures"] = len(kept)
    data["level_distribution"] = {
        lv: C(s["lowest_level"] for s in kept).get(lv, 0)
        for lv in ["A1", "A2", "B1", "B2", "C1", "C2"]
    }
    data["categories"] = dict(C(s["category"] for s in kept))

    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return len(kept), len(original) - len(kept), removed_by_level


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("Computing total sentences...")
    total = count_total_sentences()
    print(f"  {total} sentences across all lessons\n")

    print("Running parsers to compute fire rates (this takes ~30s)...")
    fire_rates = compute_fire_rates(total)
    print(f"  {len(fire_rates)} rules with at least 1 match\n")

    print("Thresholds applied:")
    for level, thr in FIRE_RATE_THRESHOLDS.items():
        print(f"  {level}: fire_rate > {thr*100:.0f}%")
    print()

    total_kept = 0
    total_removed = 0

    for path in STRATEGY_FILES:
        kept, removed, by_level = filter_file(path, fire_rates)
        total_kept += kept
        total_removed += removed
        print(f"{path.name}: {kept + removed} -> {kept}  ({removed} removed)")
        for level in ["A2", "B1", "B2", "C1", "C2"]:
            entries = by_level.get(level, [])
            if entries:
                print(f"  [{level}] {len(entries)} removed:")
                for e in entries:
                    print(f"    - {e}")

    print(f"\nTotal: {total_kept + total_removed} -> {total_kept}  ({total_removed} removed)")


if __name__ == "__main__":
    main()
