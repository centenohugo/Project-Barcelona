"""
Generates data/processed/{student}/{lesson}/grammar/grammar_richness.json from:
  - data/preprocessed/{student}/{lesson}/sentences.json

For each paragraph:
  1. Runs Group1–4Parser on every sentence (spaCy + grammar_parser)
  2. Computes richness score (same formula as paragraph_grammar_richness.ipynb)
  3. Saves all matches + richness + sentence texts to the output file

Output is consumed by notebooks/paragraph_grammar_richness.ipynb.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import spacy

# ── Path setup ───────────────────────────────────────────────────────────────
# __file__ is src/preprocessing_scripts/build_grammar_processed.py
# ROOT is three levels up: preprocessing_scripts -> src -> repo root
ROOT = Path(__file__).parent.parent.parent
PREP = ROOT / 'data' / 'preprocessed'
PROC = ROOT / 'data' / 'processed'

GRAMMAR_SRC = ROOT / 'src' / 'grammar'
if str(GRAMMAR_SRC) not in sys.path:
    sys.path.insert(0, str(GRAMMAR_SRC))

from grammar_parser import Group1Parser, Group2Parser, Group3Parser, Group4Parser

# ── Constants (mirrored from notebook Cell 1) ─────────────────────────────────
DIMENSION_MAP = {
    "CLAUSES": "A", "QUESTIONS": "A", "REPORTED SPEECH": "A",
    "CONJUNCTIONS": "A", "DISCOURSE MARKERS": "A",
    "PAST": "B", "PRESENT": "B", "FUTURE": "B",
    "PASSIVES": "B", "VERBS": "B", "NEGATION": "B",
    "PRONOUNS": "C", "DETERMINERS": "C", "NOUNS": "C",
    "ADJECTIVES": "C", "ADVERBS": "C", "PREPOSITIONS": "C",
    "MODALITY": "D", "FOCUS": "D",
}
LEVEL_WEIGHT    = 0.60
VARIETY_WEIGHT  = 0.40
VARIETY_CEILING = 15
LEVEL_MIN, LEVEL_MAX = 2, 6


# ── Match extraction ──────────────────────────────────────────────────────────

def parse_paragraph(sentences, parsers, nlp):
    """
    sentences : list of {'sentence_index': int, 'text': str, ...}
    Returns   : list of match dicts with char offsets + sentence metadata.
    """
    matches = []
    for s in sentences:
        doc = nlp(s['text'])
        for parser in parsers:
            for m in parser.parse(doc):
                span = doc[m['start_token']:m['end_token']]
                ctx  = doc[m['context_start_token']:m['context_end_token']]
                matches.append({
                    'sentence_index':       s['sentence_index'],
                    'sentence_text':        s['text'],
                    'structure_id':         m['structure_id'],
                    'category':             m['category'],
                    'guideword':            m['guideword'],
                    'lowest_level':         m['lowest_level'],
                    'lowest_level_numeric': m['lowest_level_numeric'],
                    'explanation':          m.get('explanation', ''),
                    'span_text':            m['span_text'],
                    'start_token':          m['start_token'],
                    'end_token':            m['end_token'],
                    'start_char':           span.start_char,
                    'end_char':             span.end_char,
                    'context_start_char':   ctx.start_char,
                    'context_end_char':     ctx.end_char,
                })
    return matches


# ── Richness computation (exact copy of notebook Cell 4) ─────────────────────

def _assigned_groups(matches):
    """Keep highest-level match per (token range, category, sentence)."""
    groups = {}
    for m in matches:
        key = (m['start_token'], m['end_token'], m['category'], m['sentence_text'])
        if key not in groups or m['lowest_level_numeric'] > groups[key]['lowest_level_numeric']:
            groups[key] = m
    return list(groups.values())


def compute_richness(matches, n_sentences):
    assigned = _assigned_groups(matches)

    if not assigned:
        return {
            'score': 0, 'label': 'Sparse', 'color': '#dc2626',
            'variety': 0.0, 'level': 0.0, 'density': 0.0,
            'distinct_categories': [], 'dims_present': [],
            'level_distribution': {}, 'top_match': None,
            'avg_level_str': '-', 'n_assigned': 0,
        }

    level_nums    = [m['lowest_level_numeric'] for m in assigned]
    avg_level     = sum(level_nums) / len(level_nums)
    level_score   = max(0.0, min(1.0, (avg_level - LEVEL_MIN) / (LEVEL_MAX - LEVEL_MIN)))
    distinct_cats = sorted({m['category'] for m in assigned})
    variety_score = min(len(distinct_cats) / VARIETY_CEILING, 1.0)
    dims_present  = sorted({DIMENSION_MAP.get(m['category'], '?') for m in assigned} - {'?'})
    density       = len(assigned) / n_sentences if n_sentences > 0 else 0.0
    raw           = LEVEL_WEIGHT * level_score + VARIETY_WEIGHT * variety_score
    score         = max(0, min(100, round(raw * 100)))

    if   score >= 70: label, color = 'Rich',     '#15803d'
    elif score >= 50: label, color = 'Moderate', '#d97706'
    elif score >= 30: label, color = 'Basic',    '#ea580c'
    else:             label, color = 'Sparse',   '#dc2626'

    lv_labels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    avg_str   = lv_labels[max(0, min(5, round(avg_level) - 1))]

    return {
        'score':               score,
        'label':               label,
        'color':               color,
        'variety':             variety_score,
        'level':               level_score,
        'density':             density,
        'distinct_categories': distinct_cats,
        'dims_present':        dims_present,
        'level_distribution':  dict(Counter(m['lowest_level'] for m in assigned)),
        'top_match':           max(assigned, key=lambda m: m['lowest_level_numeric']),
        'avg_level_str':       avg_str,
        'n_assigned':          len(assigned),
    }


# ── Lesson processor ──────────────────────────────────────────────────────────

def process_lesson(student, lesson):
    sentences_path = PREP / student / lesson / 'sentences.json'
    out_dir        = PROC / student / lesson / 'grammar'
    out_path       = out_dir / 'grammar_richness.json'

    if not sentences_path.exists():
        print(f'  SKIP {student}/{lesson}: no sentences.json')
        return

    print(f'  Loading {student}/{lesson}...')
    inp = json.loads(sentences_path.read_text('utf-8'))

    nlp     = spacy.load('en_core_web_sm')
    parsers = [
        Group1Parser(nlp, resolve=True),
        Group2Parser(nlp, resolve=True),
        Group3Parser(nlp, resolve=True),
        Group4Parser(nlp, resolve=True),
    ]

    paragraphs_out = []
    for para in inp['paragraphs']:
        if not para.get('conversation_boolean', True):
            continue
        pid       = para['paragraph_id']
        sentences = para['sentences']

        matches  = parse_paragraph(sentences, parsers, nlp)
        richness = compute_richness(matches, len(sentences))

        paragraphs_out.append({
            'paragraph_id':   pid,
            'label':          para.get('label', ''),
            'sentence_count': len(sentences),
            'word_start_id':  para.get('word_start_id'),
            'word_end_id':    para.get('word_end_id'),
            'sentences':      [{'sentence_index': s['sentence_index'], 'text': s['text']}
                                for s in sentences],
            'matches':        matches,
            'richness':       richness,
        })

        print(f'    para {pid}: {len(sentences)} sents, '
              f'{len(matches)} matches, richness={richness["score"]} ({richness["label"]})')

    output = {
        'source':           str(sentences_path.relative_to(ROOT)).replace('\\', '/'),
        'student':          inp['student'],
        'lesson':           inp['lesson'],
        'partition_method': inp.get('partition_method', ''),
        'paragraphs':       paragraphs_out,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), 'utf-8')
    print(f'    Wrote {out_path}')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    else:
        print('Usage: python preprocessing_scripts/build_grammar_processed.py <student> <lesson>')
        print('Example: python preprocessing_scripts/build_grammar_processed.py Student-1 lesson-2')
        sys.exit(1)
