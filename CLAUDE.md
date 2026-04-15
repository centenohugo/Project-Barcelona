# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

NLP pipeline that analyses transcribed English speech from language learners. It detects grammar structures in each lesson, maps them to CEFR proficiency levels (A1–C2), tracks grammatical errors, and produces per-lesson reports and cross-lesson comparisons per student.

## Environment

- Python 3, virtual environment at `.venv/`
- Activate: `source .venv/Scripts/activate` (Windows/bash)
- spaCy is the core NLP library (`en_core_web_*` model required)

## Data Flow

```
raw_data/TheEuropaHack_PublicDataSample/
  Student-N/lesson-N/*.json          ← raw speech-to-text (channel 0 = learner)

extract_channel0_texts.py            ← extracts learner speech sentences
  python extract_channel0_texts.py <input.json> [-o <output.txt>]

processed_data/sentences/
  Student-N/lesson-N/
    01s.txt … NNs.txt                ← per-source-file sentence lists
    merged.txt                       ← all sentences for that lesson (pipeline input)

grammar_parser/                      ← detection pipeline (to be built)
  structures/                        ← grammar rule definitions (do not modify)
    group1_tokens.json
    group2_pos.json
    group3_deps.json
    group4_patterns.json
```

The pipeline entry point reads any `merged.txt` matching the pattern `processed_data/sentences/Student-*/lesson-*/merged.txt`.

## Grammar Structure Files

Each file in `grammar_parser/structures/` is a JSON array. Every structure object shares these fields:

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `category` | Grammar category (e.g. MODALITY, CLAUSES) |
| `guideword` | Human-readable label |
| `levels` | List of CEFR levels this structure belongs to |
| `lowest_level` | Minimum CEFR level (A1–C2) |
| `examples` | Real learner sentences with `pass`/`fail` assessment |

Detection method per group:

| File | spaCy Tool | Content |
|---|---|---|
| `group1_tokens.json` | `spacy.matcher.Matcher` | `keywords` field; keyword/token patterns |
| `group2_pos.json` | `spacy.matcher.Matcher` | `pos_patterns` field; POS tag sequences |
| `group3_deps.json` | `spacy.matcher.DependencyMatcher` | `dep_patterns` field; dependency arc patterns |
| `group4_patterns.json` | `spacy.matcher.Matcher` + `re` | `spacy_patterns` + regex; mixed detection |

Categories per group:
- **group1**: MODALITY (153), NEGATION (31), DISCOURSE_MARKERS (11)
- **group2**: PRONOUNS (109), DETERMINERS (61), ADJECTIVES (70), ADVERBS (50), NOUNS (51), PASSIVES (37), PAST (57), PRESENT (28), PREPOSITIONS (9)
- **group3**: CLAUSES (133), REPORTED SPEECH (17), FOCUS (15)
- **group4**: FUTURE (56), VERBS (52), QUESTIONS (33), CONJUNCTIONS (21)

## CEFR Level Mapping

| Level | Numeric |
|---|---|
| A1 | 1 |
| A2 | 2 |
| B1 | 3 |
| B2 | 4 |
| C1 | 5 |
| C2 | 6 |

Use `lowest_level` as the canonical level for a detected structure when computing progression scores.

## Pipeline Architecture (to build)

The grammar parser should produce two types of output:

### Per-lesson report
For each `Student-N/lesson-N/merged.txt`:
- List of detected structures (id, category, guideword, level)
- Error instances: sentences where a structure was matched but the pattern corresponds to an incorrect usage (cross-reference `examples[].pass == false` patterns to define error signatures)
- Level distribution: count of structures per CEFR level

### Cross-lesson comparison (per student)
Across all lessons for the same student:
- CEFR level progression: does the student use higher-level structures in later lessons?
- Error correction tracking: structures that appeared as errors in lesson N and reappear correctly in lesson N+k
- New structures introduced per lesson

## Benchmark Reference

`benchmarks/EnglishGrammarProfile.xlsx` — the English Grammar Profile source data. The JSON files in `grammar_parser/structures/` are the intermediate representation derived from this file; work with the JSON files directly, not the Excel.
