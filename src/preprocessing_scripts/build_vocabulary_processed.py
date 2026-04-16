"""
Generates data/processed/{student}/{lesson}/vocabulary/vocabulary_richness.json from:
  - data/preprocessed/{student}/{lesson}/sentences.json
  - src/vocabulary/ENGLISH_CEFR_WORDS.csv  (Kaggle: nezahatkk/10-000-english-words-cerf-labelled)

For each paragraph, analyses content words (NOUN, VERB, ADJ, ADV) against the
CEFR vocabulary list and computes:
  - Per-match: word, lemma, POS, CEFR level, sentence index
  - Per-paragraph: level distribution, richness score, type-token ratio, lexical density
  - Overall summary: totals and averages across the lesson

Richness formula mirrors grammar_richness:
  score = 0.60 * level_score + 0.40 * variety_score  (0-100)
  level_score  = (avg_cefr_numeric - 1) / 5   clipped [0, 1]
  variety_score = distinct_levels_used / 6     clipped [0, 1]

Usage:
  python preprocessing_scripts/build_vocabulary_processed.py Student-1 lesson-1
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path

import spacy

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT    = Path(__file__).parent.parent.parent
PREP    = ROOT / 'data' / 'preprocessed'
PROC    = ROOT / 'data' / 'processed'
CSV_PATH = ROOT / 'src' / 'vocabulary' / 'ENGLISH_CEFR_WORDS.csv'

# ── Constants ─────────────────────────────────────────────────────────────────
CEFR_NUMERIC = {'A1': 1, 'A2': 2, 'B1': 3, 'B2': 4, 'C1': 5, 'C2': 6}
LEVEL_MIN, LEVEL_MAX = 1, 6

LEVEL_WEIGHT   = 0.60
VARIETY_WEIGHT = 0.40

CONTENT_POS = {'NOUN', 'VERB', 'ADJ', 'ADV'}

QUALITY_LEVELS = [
    (70, 'Rich',     '#15803d'),
    (50, 'Moderate', '#d97706'),
    (30, 'Basic',    '#ea580c'),
    ( 0, 'Sparse',   '#dc2626'),
]


# ── Vocabulary lookup ─────────────────────────────────────────────────────────

def build_vocab_lookup(csv_path: Path) -> dict:
    """
    Returns {word_lowercase: cefr_level} from the CEFR CSV.
    Handles compound headwords like 'a.m./A.M./am/AM' by splitting on '/'.
    Skips multi-word entries (contain space after splitting).
    """
    lookup: dict[str, str] = {}
    with open(csv_path, encoding='utf-8') as f:
        next(f)  # skip header
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.rsplit(',', 1)
            if len(parts) != 2:
                continue
            headword_raw, level = parts[0].strip(), parts[1].strip()
            if level not in CEFR_NUMERIC:
                continue
            for variant in headword_raw.split('/'):
                variant = variant.strip().lower()
                # Skip multi-word entries and empty strings
                if not variant or ' ' in variant:
                    continue
                # Remove punctuation variants like "a.m." → keep "am" variant separately
                clean = re.sub(r'[^a-z]', '', variant)
                if clean:
                    # Only overwrite if new level is higher (prefer highest CEFR for ambiguous)
                    if clean not in lookup or CEFR_NUMERIC[level] > CEFR_NUMERIC[lookup[clean]]:
                        lookup[clean] = level
                # Also store the variant with punctuation (lowercased)
                if variant not in lookup or CEFR_NUMERIC[level] > CEFR_NUMERIC[lookup[variant]]:
                    lookup[variant] = level
    return lookup


def _lookup_word(token, lookup: dict) -> str | None:
    """Try lemma first, then surface form. Returns CEFR level or None."""
    for candidate in (token.lemma_.lower(), token.text.lower()):
        if candidate in lookup:
            return lookup[candidate]
    return None


# ── Richness computation ──────────────────────────────────────────────────────

def compute_richness(matches: list) -> dict:
    """
    matches: list of dicts with 'cefr_level' key (content words found in vocab list).
    """
    if not matches:
        return {
            'score': 0, 'label': 'Sparse', 'color': '#dc2626',
            'level_score': 0.0, 'variety_score': 0.0,
            'avg_level': None, 'avg_level_str': '-',
            'distinct_levels': [], 'level_distribution': {},
            'n_matched': 0,
        }

    levels_numeric = [CEFR_NUMERIC[m['cefr_level']] for m in matches]
    avg_level      = sum(levels_numeric) / len(levels_numeric)
    level_score    = max(0.0, min(1.0, (avg_level - LEVEL_MIN) / (LEVEL_MAX - LEVEL_MIN)))

    distinct_levels  = sorted({m['cefr_level'] for m in matches}, key=lambda l: CEFR_NUMERIC[l])
    variety_score    = min(len(distinct_levels) / 6, 1.0)

    raw   = LEVEL_WEIGHT * level_score + VARIETY_WEIGHT * variety_score
    score = max(0, min(100, round(raw * 100)))

    label, color = 'Sparse', '#dc2626'
    for threshold, lbl, clr in QUALITY_LEVELS:
        if score >= threshold:
            label, color = lbl, clr
            break

    lv_labels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    avg_level_str = lv_labels[max(0, min(5, round(avg_level) - 1))]

    return {
        'score':              score,
        'label':              label,
        'color':              color,
        'level_score':        round(level_score, 4),
        'variety_score':      round(variety_score, 4),
        'avg_level':          round(avg_level, 4),
        'avg_level_str':      avg_level_str,
        'distinct_levels':    distinct_levels,
        'level_distribution': dict(Counter(m['cefr_level'] for m in matches)),
        'n_matched':          len(matches),
    }


# ── Paragraph analysis ────────────────────────────────────────────────────────

def analyse_paragraph(sentences: list, nlp, lookup: dict) -> tuple[list, dict]:
    """
    Returns (matches, stats) for a paragraph.
    matches: content words found in the CEFR vocab list.
    stats: total_words, content_words, matched_words, ttr, lexical_density.
    """
    all_tokens   = []
    matches      = []
    seen_types   = set()

    for s in sentences:
        doc = nlp(s['text'])
        for token in doc:
            if token.is_space or token.is_punct:
                continue

            all_tokens.append(token.text.lower())

            if token.pos_ not in CONTENT_POS:
                continue

            cefr = _lookup_word(token, lookup)
            if cefr is None:
                continue

            matches.append({
                'sentence_index': s['sentence_index'],
                'sentence_text':  s['text'],
                'word':           token.text,
                'lemma':          token.lemma_.lower(),
                'pos':            token.pos_,
                'cefr_level':     cefr,
                'cefr_numeric':   CEFR_NUMERIC[cefr],
            })
            seen_types.add(token.lemma_.lower())

    total_words   = len(all_tokens)
    content_words = sum(1 for m in matches)
    unique_tokens = len(set(all_tokens))
    ttr           = round(unique_tokens / total_words, 4) if total_words else 0.0
    lex_density   = round(content_words / total_words, 4) if total_words else 0.0

    stats = {
        'total_words':    total_words,
        'content_words':  content_words,
        'matched_words':  len(matches),
        'unique_types':   len(seen_types),
        'ttr':            ttr,
        'lexical_density': lex_density,
    }
    return matches, stats


# ── Lesson processor ──────────────────────────────────────────────────────────

def process_lesson(student: str, lesson: str):
    sentences_path = PREP / student / lesson / 'sentences.json'
    out_dir        = PROC / student / lesson / 'vocabulary'
    out_path       = out_dir / 'vocabulary_richness.json'

    if not sentences_path.exists():
        print(f'  SKIP {student}/{lesson}: no sentences.json')
        return

    print(f'  Loading vocabulary lookup...')
    lookup = build_vocab_lookup(CSV_PATH)
    print(f'    {len(lookup)} entries loaded')

    print(f'  Loading spaCy...')
    nlp = spacy.load('en_core_web_sm')

    print(f'  Processing {student}/{lesson}...')
    inp = json.loads(sentences_path.read_text('utf-8'))

    paragraphs_out = []
    all_matches    = []

    for para in inp['paragraphs']:
        if not para.get('conversation_boolean', True):
            continue

        pid       = para['paragraph_id']
        sentences = para['sentences']

        matches, stats = analyse_paragraph(sentences, nlp, lookup)
        richness       = compute_richness(matches)
        all_matches.extend(matches)

        paragraphs_out.append({
            'paragraph_id':   pid,
            'label':          para.get('label', ''),
            'sentence_count': len(sentences),
            'word_start_id':  para.get('word_start_id'),
            'word_end_id':    para.get('word_end_id'),
            'stats':          stats,
            'matches':        matches,
            'richness':       richness,
        })

        print(f'    para {pid}: {stats["total_words"]} words, '
              f'{stats["matched_words"]} matched, '
              f'richness={richness["score"]} ({richness["label"]}), '
              f'avg={richness["avg_level_str"]}')

    # Overall summary
    overall_richness = compute_richness(all_matches)
    total_words_all  = sum(p['stats']['total_words'] for p in paragraphs_out)
    matched_all      = sum(p['stats']['matched_words'] for p in paragraphs_out)

    output = {
        'source':           str(sentences_path.relative_to(ROOT)).replace('\\', '/'),
        'student':          inp['student'],
        'lesson':           inp['lesson'],
        'partition_method': inp.get('partition_method', ''),
        'summary': {
            'paragraph_count':    len(paragraphs_out),
            'total_words':        total_words_all,
            'total_matched':      matched_all,
            'coverage_rate':      round(matched_all / total_words_all, 4) if total_words_all else 0.0,
            'overall_richness':   overall_richness,
        },
        'paragraphs': paragraphs_out,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), 'utf-8')
    print(f'    Wrote {out_path}')
    print(f'    Total matched: {matched_all}/{total_words_all} words, '
          f'overall richness={overall_richness["score"]} ({overall_richness["label"]})')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    else:
        print('Usage: python preprocessing_scripts/build_vocabulary_processed.py <student> <lesson>')
        print('Example: python preprocessing_scripts/build_vocabulary_processed.py Student-1 lesson-1')
        sys.exit(1)
