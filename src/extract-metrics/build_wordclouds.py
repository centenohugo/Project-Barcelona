"""
src/extract-metrics/build_wordclouds.py

Generates a word cloud image for the dominant word family of each lesson.
All family members are rendered at equal visual weight to show variety —
a "dense" cloud signals rich vocabulary range.

Reads:
  data/processed/{student}/{lesson}/vocabulary/dominant_family.json

Writes:
  webapp/public/wordclouds/{student}_{lesson}.png

Usage:
  python src/extract-metrics/build_wordclouds.py                   # all lessons
  python src/extract-metrics/build_wordclouds.py Student-1 lesson-1
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # headless – no display needed
import matplotlib.pyplot as plt
from wordcloud import WordCloud

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent.parent
PROC    = ROOT / "data" / "processed"
OUT_DIR = ROOT / "webapp" / "public" / "wordclouds"

# ── Brand colour ──────────────────────────────────────────────────────────────
PINK = "#FF6B9D"  # var(--primary)


def _color_func(
    word: str,
    font_size: int,
    position: tuple,
    orientation: int | None,
    random_state: random.Random | None = None,
    **kwargs,
) -> str:
    return PINK


def build_cloud(student: str, lesson: str) -> bool:
    lesson_key = lesson if lesson.startswith("lesson-") else f"lesson-{lesson}"
    family_path = PROC / student / lesson_key / "vocabulary" / "dominant_family.json"

    if not family_path.exists():
        print(f"  SKIP {student}/{lesson_key}: dominant_family.json not found")
        return False

    with open(family_path, encoding="utf-8") as f:
        data = json.load(f)

    family = data.get("dominant_family")
    if not family or not family.get("members"):
        print(f"  SKIP {student}/{lesson_key}: no members in dominant family")
        return False

    members = [m["word"] for m in family["members"]]
    root    = family.get("root", "")

    # Equal frequency → equal visual weight (no word looks "dominant")
    freq = {word: 1 for word in members}

    wc = WordCloud(
        width=800,
        height=360,
        background_color="white",
        color_func=_color_func,
        relative_scaling=0,       # sizes driven by canvas space, not frequency
        prefer_horizontal=0.65,
        min_font_size=30,
        max_font_size=64,
        margin=12,
        random_state=42,
        collocations=False,
    ).generate_from_frequencies(freq)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{student}_{lesson_key}.png"

    fig, ax = plt.subplots(figsize=(8, 3.6), dpi=150)
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    plt.tight_layout(pad=0)
    fig.savefig(out_path, bbox_inches="tight", facecolor="white", dpi=150)
    plt.close(fig)

    print(
        f"  {student}/{lesson_key}: "
        f"root={root!r} · {len(members)} members -> {out_path.name}"
    )
    return True


def discover_lessons() -> list[tuple[str, str]]:
    pairs = []
    for p in sorted(PROC.glob("*/lesson-*/vocabulary/dominant_family.json")):
        lesson  = p.parent.parent.name
        student = p.parent.parent.parent.name
        pairs.append((student, lesson))
    return pairs


def main() -> None:
    if len(sys.argv) == 3:
        build_cloud(sys.argv[1], sys.argv[2])
    elif len(sys.argv) == 1:
        pairs = discover_lessons()
        if not pairs:
            print("No dominant_family.json files found in", PROC)
            return
        for student, lesson in pairs:
            build_cloud(student, lesson)
    else:
        print("Usage: build_wordclouds.py [student lesson]")
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
