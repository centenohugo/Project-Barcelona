# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Barcelona is a contextual CEFR (Common European Framework of Reference) language proficiency classifier for English. It analyzes Deepgram speech transcription JSONs from ESL lessons and classifies each word by CEFR level (A1–C2). Built on Kikuchi et al. (2026) — "CEFR-Annotated WordNet" (arXiv:2510.18466).

## Setup

```bash
python -m venv .env
.env/Scripts/activate        # Windows
pip install -r requirements.txt
python -m nltk.downloader wordnet omw-1.4
```

The contextual classifier requires the CEFR-Annotated WordNet resource extracted under `resources/cefr_wordnet/`.

## Running

```bash
# Simple classifier (cefrpy lookup + whitelists)
python analyze_cefr.py Data/Student-1/lesson-1/01.json

# Contextual classifier (WordNet WSD + sentence-transformers)
python analyze_cefr_contextual.py Data/Student-1/lesson-1/01.json --window 5
```

Output goes to `output/` as `Student-X_lesson-Y_NN.json` or `Student-X_lesson-Y_NN_contextual.json`.

## Architecture

Two classification pipelines share a common fast path (digit detection, A1/A2 whitelists for contractions/interjections) and diverge on unknown words:

- **`analyze_cefr.py`** — Direct cefrpy word-level lookup. Fast, no ML dependencies at runtime.
- **`analyze_cefr_contextual.py`** — Word Sense Disambiguation: embeds a ±N token context window and all WordNet sense glosses with `all-MiniLM-L6-v2`, picks the sense with highest cosine similarity (threshold 0.15), maps it to CEFR via `cefr_wordnet`. Falls back to lemma-level minimum CEFR, then cefrpy, then UNKNOWN.

## Vocabulary Progress Tracking

- **`vocab_progress.py`** — Post-processing module that aggregates contextual classifier outputs per lesson and computes vocabulary metrics. Requires contextual outputs in `output/`.

```bash
# After running contextual classifier on lesson segments:
python vocab_progress.py Student-1 lesson-1
python vocab_progress.py Student-1 lesson-2  # includes cross-lesson comparison
```

Output goes to `progress/`:
- `Student-X_lesson-Y_progress.json` — Tier 1 (per-lesson: vocab level score, lexical sophistication, interesting words) + Tier 2 (cross-lesson: new words, retention, score trend, vocabulary growth).
- `Student-X_history.json` — Cumulative student vocabulary history (updated each run). Lessons must be processed in chronological order.

Key design choices:
- Function words excluded from the numerical vocab level score (only content words count).
- Proper noun filtering via `source` field (requires contextual outputs with `source` preserved).
- Confidence threshold 0.60 for scoring, 0.70 for interesting words.

## Webapp — Charlies CEFR Progress Tracker

Located in `webapp/`. See `webapp/AGENTS.md` for full details.

```bash
cd webapp
npm install
npm run dev          # http://localhost:3000
```

- **Stack:** Next.js 16 (App Router), TypeScript, Tailwind CSS, Recharts, Framer Motion
- **Design system:** `webapp/DESIGN.md` — "The Kinetic Editorial" (pink #FF6B9D / teal #40E0D0, Plus Jakarta Sans + Inter)
- **Routes:** `/` (landing: progress chart + metric bars + stacked lesson cards), `/lesson/[id]` (lesson detail: conversation chunks with CEFR-highlighted words + per-chunk metrics)
- **Data:** Currently hardcoded in `webapp/lib/mock-data.ts`. Will connect to `progress/` and `output/` JSONs.

## Data Conventions

- Input: Deepgram transcription JSONs under `Data/Student-X/lesson-Y/`. Channel 0 = student speech.
- CEFR level ordering: A1 < A2 < B1 < B2 < C1 < C2 < UNKNOWN.
- Output JSON uses UTF-8 with `ensure_ascii=False`.
