# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

NLP pipeline that analyses transcribed English speech from language learners. It detects grammar structures in each lesson, maps them to CEFR proficiency levels (A1–C2), tracks grammatical errors via LanguageTool, and produces per-lesson reports and cross-lesson comparisons per student.

## Environment

- Python 3, virtual environment at `.venv/`
- Activate: `source .venv/Scripts/activate` (Windows/bash)
- Core dependencies: `spacy>=3.7`, `jupyterlab>=4.0`, `language_tool_python` (install separately if missing)
- spaCy model: `python -m spacy download en_core_web_sm`

## Commands

```bash
# Activate environment
source .venv/Scripts/activate

# Extract learner speech from raw ASR JSON → text lines
python extract_channel0_texts.py <input.json> [-o <output.txt>]

# Sentence segmentation: merged.txt → validated-sentence-separation.txt
python separate_sentences.py                          # all lessons
python separate_sentences.py <path/to/merged.txt>    # single file

# Build fluidity data (word/gap/filler stats per lesson)
python build_fluidity.py

# Enrich fluidity with speech speed and filler detection
python fluidity_analysis.py

# Build per-lesson sentence analysis (fluency score 0–100)
python build_sentences_analysis.py

# Run LanguageTool grammar error detection → processed_data/errors/
python check_grammar_errors.py

# Run notebooks
jupyter lab
jupyter nbconvert --to notebook --execute --inplace notebooks/<name>.ipynb
```

## Data Flow

```
raw_data/TheEuropaHack_PublicDataSample/
  Student-N/lesson-N/*.json          ← raw ASR (channel 0 = learner, channel 1 = teacher)

extract_channel0_texts.py            → text lines per file
separate_sentences.py                → processed_data/sentences/Student-N/lesson-N/
                                          merged.txt                        (raw turns)
                                          validated-sentence-separation.txt (pipeline input)

── Grammar detection ──────────────────────────────────────────────────────────
grammar_parser/ (Group1–4Parser)    → CEFR structure matches per sentence
                                      used in notebooks directly, no batch script

── Error detection ────────────────────────────────────────────────────────────
check_grammar_errors.py             → processed_data/errors/Student-N/lesson-N/grammar_errors.json
grammar_errors/error_checker.py     → wraps LanguageTool, classifies via rule_mapping.py + error_weights.json

── Fluidity ───────────────────────────────────────────────────────────────────
build_fluidity.py                   → processed_data/fluidity/Student-N/lesson-N/fluidity.json
fluidity_analysis.py                → enriches fluidity.json with speed, fillers
build_sentences_analysis.py         → processed_data/sentences_analysis/Student-N/lesson-N/sentences-analysis.json

── Notebooks ──────────────────────────────────────────────────────────────────
pipeline_demo.ipynb                 → grammar parser demo, one lesson
errors_demo.ipynb                   → LanguageTool error counts by category
fluidity_demo.ipynb                 → speech speed, gaps, filler rates, fluency score
progression_demo.ipynb              → cross-lesson CEFR progression per student
paragraph_error_valoration.ipynb    → paragraph-level errors, clickable HTML, 0–100 score
paragraph_grammar_richness.ipynb    → grammar diversity and CEFR distribution per paragraph
grammar_comparison_student2.ipynb   → side-by-side lesson comparison (structures + errors)
```

The canonical input for all analysis is `validated-sentence-separation.txt` (one sentence per line). `merged.txt` is raw and must go through `separate_sentences.py` first.

## Module: `grammar_parser/`

Four spaCy-based parsers, each loading rules from a `structures/strategy*.json` file:

```python
from grammar_parser import Group1Parser, Group2Parser, Group3Parser, Group4Parser
nlp = spacy.load('en_core_web_sm')
parser = Group1Parser(nlp, resolve=True)   # resolve=True filters overlapping spans
matches = parser.parse(doc)                # doc is a spacy.tokens.Doc
```

Each match dict contains: `structure_id, category, guideword, lowest_level, lowest_level_numeric, span_text, explanation`.

**Detection Strategies:**

| File | Strategy | spaCy Tool | Categories |
|---|---|---|---|
| `strategy1_lexical_trigger.json` | LEXICAL_TRIGGER | `Matcher` (keywords/lemmas) + Regex | MODALITY (19), NEGATION (5), DISCOURSE MARKERS (2) |
| `strategy2_nominal_pos.json` | NOMINAL_POS | `Matcher` (POS/TAG sequences) | PRONOUNS, DETERMINERS, NOUNS, ADJECTIVES, ADVERBS |
| `strategy3_verbal_morphology.json` | VERBAL_MORPHOLOGY | `Matcher` (verb TAGs) + Regex | PAST, PRESENT, FUTURE, PASSIVES, VERBS |
| `strategy4_syntactic_structure.json` | SYNTACTIC_STRUCTURE | `DependencyMatcher` + `Matcher` | CLAUSES, REPORTED SPEECH, FOCUS, QUESTIONS |
| `strategy5_hybrid_pattern.json` | HYBRID_PATTERN | reserved | (empty) |

> **Legacy files** `group1_tokens.json`, `group2_pos.json`, `group3_deps.json`, `group4_patterns.json` are preserved for reference only. Use `strategy*.json` for all development.

## Module: `grammar_errors/`

```python
from grammar_errors.error_checker import ErrorChecker
checker = ErrorChecker()
records = checker.check_file('path/to/validated-sentence-separation.txt')
records = checker.check_sentences(['sentence one', 'sentence two'])
```

Each record contains: `sentence, sentence_index, rule_id, grammar_category, dimension_code, dimension_label, weight, matched_text, message, replacements, offset, error_length`.

- `error_weights.json` — severity scale 0–3 per grammar category (0 = suppressed, not returned)
- `rule_mapping.py` — maps LanguageTool rule IDs → grammar categories → Proficiency Dimensions
- Weight 0 errors are filtered out before returning records (not shown as errors)

## Grammar Structure Files

Each `structures/strategy*.json` has this shape:

```json
{
  "group": "...",
  "detection_method": "...",
  "total_structures": 0,
  "categories": { "CATEGORY_NAME": count },
  "level_distribution": { "A1": 0, "A2": 0, "B1": 0, "B2": 0, "C1": 0, "C2": 0 },
  "structures": [ ... ]
}
```

Every structure object includes: `id, category, guideword, levels, lowest_level, examples, explanation`, plus detection fields (`keywords`, `spacy_patterns`, `pos_patterns`, `dep_patterns`, `regex_pattern`) that vary by strategy.

When removing a rule from a JSON file, also update `total_structures`, `categories`, and `level_distribution` counts in the same file header.

## Proficiency Dimensions (pedagogical grouping)

Use these in notebooks and reports — not in parser code (use Detection Strategies there).

| Dimension | Grammar categories | What it measures |
|---|---|---|
| **A — Sentence Architecture** | CLAUSES, QUESTIONS, REPORTED SPEECH, CONJUNCTIONS, DISCOURSE MARKERS | Complex sentence building; discourse coherence |
| **B — Tense & Aspect Mastery** | PAST, PRESENT, FUTURE, PASSIVES, VERBS, NEGATION | Command of the verb system |
| **C — Nominal Precision** | PRONOUNS, DETERMINERS, NOUNS, ADJECTIVES, ADVERBS, PREPOSITIONS | Noun phrase accuracy, reference, modification |
| **D — Modal & Functional Range** | MODALITY, FOCUS | Nuance, certainty, obligation, emphasis |

## CEFR Level Mapping

| Level | Numeric |
|---|---|
| A1 | 1 |
| A2 | 2 |
| B1 | 3 |
| B2 | 4 |
| C1 | 5 |
| C2 | 6 |

Use `lowest_level` as the canonical level for a detected structure. Use `lowest_level_numeric` for sorting and scoring.

## Notebook Patterns

- **HTML rendering**: use `IPython.display.HTML(html_string)`. Build HTML via string concatenation, not f-strings with backslashes (Python 3.10 restriction in f-string expressions).
- **Dimension color scheme** (consistent across notebooks): A=`#3B82F6`/`#DBEAFE`, B=`#F59E0B`/`#FEF3C7`, C=`#10B981`/`#D1FAE5`, D=`#8B5CF6`/`#EDE9FE`
- **Error severity colors**: weight 1 (beginner) = green, weight 2 (medium) = amber, weight 3 (high) = red
- **Notebook caches**: `grammar_comparison_student2.ipynb` writes `processed_data/cache/grammar_comparison_student2.json` to avoid re-running spaCy + LanguageTool on repeated runs. Delete the cache file to force recomputation.

## Benchmark Reference

`benchmarks/EnglishGrammarProfile.xlsx` — English Grammar Profile source data. The `grammar_parser/structures/strategy*.json` files are the derived intermediate representation; work with the JSON files directly.
