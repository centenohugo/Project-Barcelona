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

separate_sentences.py                ← sentence segmentation (run once, or per new lesson)
  python separate_sentences.py       # processes all merged.txt files
  python separate_sentences.py <path/to/merged.txt>  # single file

processed_data/sentences/
  Student-N/lesson-N/
    01s.txt … NNs.txt                           ← per-source-file sentence lists
    merged.txt                                  ← raw joined lines (one speech turn per line)
    validated-sentence-separation.txt           ← properly segmented sentences (pipeline input)

grammar_parser/
  __init__.py
  group1_parser.py                   ← Group1Parser (token-based, spacy.matcher.Matcher) [legacy]
  structures/                        ← grammar rule definitions
    strategy1_lexical_trigger.json   ← LEXICAL_TRIGGER (225 rules: MODALITY, NEGATION, DISCOURSE MARKERS, CONJUNCTIONS, PREPOSITIONS)
    strategy2_nominal_pos.json       ← NOMINAL_POS (341 rules: PRONOUNS, DETERMINERS, NOUNS, ADJECTIVES, ADVERBS)
    strategy3_verbal_morphology.json ← VERBAL_MORPHOLOGY (230 rules: PAST, PRESENT, FUTURE, PASSIVES, VERBS)
    strategy4_syntactic_structure.json ← SYNTACTIC_STRUCTURE (198 rules: CLAUSES, REPORTED SPEECH, FOCUS, QUESTIONS)
    strategy5_hybrid_pattern.json    ← HYBRID_PATTERN (0 rules, reserved for complex multi-modal cases)
    group1_tokens.json               ← [legacy, preserved for reference]
    group2_pos.json                  ← [legacy, preserved for reference]
    group3_deps.json                 ← [legacy, preserved for reference]
    group4_patterns.json             ← [legacy, preserved for reference]

notebooks/
  pipeline_demo.ipynb                ← demo: runs all parsers on one lesson, human-readable output
```

The pipeline entry point reads `validated-sentence-separation.txt` (one proper sentence per line).
`merged.txt` contains raw speech turns — multiple sentences per line and utterances split across lines — and must be pre-processed by `separate_sentences.py` before parsing.

## Grammar Structure Files

Each file in `grammar_parser/structures/` is a JSON object with the following top-level shape:

```json
{
  "group": "...",
  "detection_method": "...",
  "description": "...",
  "total_structures": 0,
  "categories": { "CATEGORY_NAME": count },
  "level_distribution": { "A1": 0, "A2": 0, "B1": 0, "B2": 0, "C1": 0, "C2": 0 },
  "structures": [ ... ]
}
```

Every structure object in `structures` shares these fields:

| Field | Description |
|---|---|
| `id` | Unique identifier |
| `category` | Grammar category (e.g. MODALITY, CLAUSES) |
| `guideword` | Human-readable label |
| `levels` | List of CEFR levels this structure belongs to |
| `lowest_level` | Minimum CEFR level (A1–C2) |
| `examples` | Real learner sentences with `pass`/`fail` assessment |

### Detection Strategies (technical grouping by spaCy mechanism)

The active rule files use the term **Detection Strategy** — grouping by *how* spaCy detects the structure:

| File | Strategy | spaCy Tool | Detection fields | Total |
|---|---|---|---|---|
| `strategy1_lexical_trigger.json` | LEXICAL_TRIGGER | `Matcher` (keywords/lemmas) + Regex | `keywords`, `spacy_patterns` | 225 |
| `strategy2_nominal_pos.json` | NOMINAL_POS | `Matcher` (POS/TAG sequences) | `pos_patterns` | 341 |
| `strategy3_verbal_morphology.json` | VERBAL_MORPHOLOGY | `Matcher` (verb TAG sequences) + Regex | `pos_patterns`, `spacy_patterns`, `regex_pattern` | 230 |
| `strategy4_syntactic_structure.json` | SYNTACTIC_STRUCTURE | `DependencyMatcher` + `Matcher` | `dep_patterns`, `spacy_patterns` | 198 |
| `strategy5_hybrid_pattern.json` | HYBRID_PATTERN | `Matcher` + Regex (complex multi-modal) | TBD | 0 (reserved) |

Categories per strategy:
- **strategy1**: MODALITY (153), NEGATION (31), DISCOURSE MARKERS (11), CONJUNCTIONS (21), PREPOSITIONS (9)
- **strategy2**: PRONOUNS (109), DETERMINERS (61), ADJECTIVES (70), ADVERBS (50), NOUNS (51)
- **strategy3**: PAST (57), PRESENT (28), FUTURE (56), PASSIVES (37), VERBS (52)
- **strategy4**: CLAUSES (133), REPORTED SPEECH (17), FOCUS (15), QUESTIONS (33)
- **strategy5**: empty — reserved for pragmatic/USE-variation rules requiring combined detection

CEFR level distribution across strategies (rules by `lowest_level`):

| Strategy | A1 | A2 | B1 | B2 | C1 | C2 | Total |
|---|---|---|---|---|---|---|---|
| strategy1 | 20 | 32 | 62 | 50 | 37 | 24 | 225 |
| strategy2 | 55 | 108 | 72 | 53 | 25 | 28 | 341 |
| strategy3 | 19 | 55 | 61 | 58 | 20 | 17 | 230 |
| strategy4 | 12 | 46 | 64 | 30 | 23 | 23 | 198 |
| **Total** | **106** | **241** | **259** | **191** | **105** | **92** | **994** |

> **Legacy files** `group1_tokens.json`, `group2_pos.json`, `group3_deps.json`, `group4_patterns.json` are preserved for reference. Use the `strategy*.json` files for all new parser development.

### Proficiency Dimensions (pedagogical grouping for student assessment)

Separate from detection strategies, the **Proficiency Dimensions** group grammar categories from a *teacher's perspective* to support qualitative student evaluation:

| Dimension | Grammar categories covered | What it measures |
|---|---|---|
| **A — Sentence Architecture** | CLAUSES, QUESTIONS, REPORTED SPEECH, CONJUNCTIONS, DISCOURSE MARKERS | Ability to build and combine complex sentences; discourse coherence |
| **B — Tense & Aspect Mastery** | PAST, PRESENT, FUTURE, PASSIVES, VERBS, NEGATION | Command of the English verb system; tense, aspect, voice, negation |
| **C — Nominal Precision** | PRONOUNS, DETERMINERS, NOUNS, ADJECTIVES, ADVERBS, PREPOSITIONS | Accuracy of noun phrases, reference, modification, and article use |
| **D — Modal & Functional Range** | MODALITY, FOCUS | Ability to express nuance, certainty, obligation, stance, and emphasis |

Use Proficiency Dimensions in per-lesson reports and cross-lesson comparisons to give teachers a high-level view of student progress. Use Detection Strategies only in internal parser code.

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
For each `Student-N/lesson-N/validated-sentence-separation.txt`:
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
