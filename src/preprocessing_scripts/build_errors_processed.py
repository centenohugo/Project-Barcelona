"""
Generates data/processed/{student}/{lesson}/errors/errors.json from:
  - data/preprocessed/{student}/{lesson}/sentences.json

Only paragraphs with conversation_boolean=true are processed.

For each paragraph, runs ErrorChecker on its sentences, then computes:
  - Per-error: all LanguageTool fields + paragraph_id + global sentence index
  - Per-paragraph: quality score, dimension breakdown, weighted error sum
  - Overall summary: totals by dimension and grammar_category

Output is the single source of truth for all error-related notebooks:
  errors_demo.ipynb, paragraph_error_valoration.ipynb, etc.
"""

import json
import sys
from pathlib import Path

# ── Path setup ───────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.parent
PREP = ROOT / 'data' / 'preprocessed'
PROC = ROOT / 'data' / 'processed'

GRAMMAR_SRC = ROOT / 'src' / 'grammar'
if str(GRAMMAR_SRC) not in sys.path:
    sys.path.insert(0, str(GRAMMAR_SRC))

from grammar_errors.error_checker import ErrorChecker

# ── Quality score (same formula as paragraph_error_valoration.ipynb) ─────────
ERROR_PENALTY_FACTOR = 5.0

QUALITY_LEVELS = [
    (80, 'Good',     '#15803d'),
    (60, 'Moderate', '#d97706'),
    (40, 'Weak',     '#ea580c'),
    ( 0, 'Poor',     '#dc2626'),
]

def quality_score(total_weight, total_words):
    if total_words == 0:
        return 100, 'Good', '#15803d'
    score = max(0, round(100 * (1 - ERROR_PENALTY_FACTOR * total_weight / total_words)))
    for threshold, label, color in QUALITY_LEVELS:
        if score >= threshold:
            return score, label, color
    return 0, 'Poor', '#dc2626'


# ── Lesson processor ──────────────────────────────────────────────────────────

def process_lesson(student, lesson):
    sentences_path = PREP / student / lesson / 'sentences.json'
    out_dir        = PROC / student / lesson / 'errors'
    out_path       = out_dir / 'errors.json'

    if not sentences_path.exists():
        print(f'  SKIP {student}/{lesson}: no sentences.json')
        return

    print(f'  Loading {student}/{lesson}...')
    inp = json.loads(sentences_path.read_text('utf-8'))

    checker = ErrorChecker()
    try:
        all_errors     = []
        paragraphs_out = []
        global_sent_idx = 1   # 1-based global sentence counter across all paragraphs

        for para in inp['paragraphs']:
            if not para.get('conversation_boolean', True):
                continue

            pid       = para['paragraph_id']
            sentences = para['sentences']   # [{'sentence_index': int, 'text': str}]
            texts     = [s['text'] for s in sentences]

            # Map local sentence_index → global sentence index
            local_to_global = {
                s['sentence_index']: global_sent_idx + i
                for i, s in enumerate(sentences)
            }
            sent_start = global_sent_idx
            global_sent_idx += len(sentences)

            # Run LanguageTool
            raw_errors = checker.check_sentences(texts, start_index=1)

            # Attach paragraph_id and remap to global sentence indices
            para_errors = []
            for err in raw_errors:
                err['paragraph_id']    = pid
                local_idx              = err['sentence_index']
                err['sentence_index']  = local_to_global.get(local_idx, sent_start + local_idx - 1)
                para_errors.append(err)
                all_errors.append(err)

            # Per-paragraph stats
            total_words  = sum(len(t.split()) for t in texts)
            total_weight = sum(e['weight'] for e in para_errors)
            dim_counts   = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
            for e in para_errors:
                dc = e.get('dimension_code', '')
                if dc in dim_counts:
                    dim_counts[dc] += 1

            score, level, color = quality_score(total_weight, total_words)

            paragraphs_out.append({
                'paragraph_id':       pid,
                'label':              para.get('label', ''),
                'sentence_count':     len(sentences),
                'word_count':         total_words,
                'sentence_start_idx': sent_start,
                'sentence_end_idx':   global_sent_idx - 1,
                'error_count':        len(para_errors),
                'weighted_error_sum': total_weight,
                'quality_score':      score,
                'quality_level':      level,
                'quality_color':      color,
                'dimension_counts':   dim_counts,
            })

            print(f'    para {pid}: {len(sentences)} sents, '
                  f'{len(para_errors)} errors, score={score} ({level})')

        # Overall summary
        dim_totals  = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
        cat_counts  = {}
        total_w     = 0
        for e in all_errors:
            dc = e.get('dimension_code', '')
            if dc in dim_totals:
                dim_totals[dc] += 1
            cat = e.get('grammar_category', 'unknown')
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            total_w += e.get('weight', 0)

        total_words_all = sum(p['word_count'] for p in paragraphs_out)
        overall_score, overall_level, overall_color = quality_score(total_w, total_words_all)

        output = {
            'source':           str(sentences_path.relative_to(ROOT)).replace('\\', '/'),
            'student':          inp['student'],
            'lesson':           inp['lesson'],
            'partition_method': inp.get('partition_method', ''),
            'summary': {
                'paragraph_count':       len(paragraphs_out),
                'sentence_count':        global_sent_idx - 1,
                'total_words':           total_words_all,
                'total_errors':          len(all_errors),
                'weighted_error_sum':    total_w,
                'overall_quality_score': overall_score,
                'overall_quality_level': overall_level,
                'overall_quality_color': overall_color,
                'dimension_counts':      dim_totals,
                'grammar_category_counts': dict(sorted(cat_counts.items(),
                                                       key=lambda x: -x[1])),
            },
            'paragraphs': paragraphs_out,
            'errors':     all_errors,
        }

        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), 'utf-8')
        print(f'    Wrote {out_path}')
        print(f'    Total: {len(all_errors)} errors, overall score={overall_score} ({overall_level})')

    finally:
        checker.close()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    else:
        print('Usage: python preprocessing_scripts/build_errors_processed.py <student> <lesson>')
        print('Example: python preprocessing_scripts/build_errors_processed.py Student-1 lesson-2')
        sys.exit(1)
