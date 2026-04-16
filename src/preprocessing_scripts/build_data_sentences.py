"""
Generates data/preprocessed/{student}/{lesson}/sentences.json from:
  - data/preprocessed/{student}/{lesson}/chunker-output.json  (paragraph boundaries as ch0 word IDs)
  - data/raw/{student}/{lesson}/*.json                        (ASR files with ch0 word_id assigned)

Algorithm
---------
1. Read raw files in sorted order (01.json, 02.json, ...).
   Collect all ch0 words in that order, each carrying its word_id (assigned by build_data_raw.py).

2. For each paragraph in chunker-output (ch0 range [word_start_id, word_end_id]):
   a. Filter the ch0 word list to words whose word_id falls in that range.
   b. Build joined text from punctuated_word, tracking char offsets per word.
   c. Run spaCy sentence segmenter on the joined text.
   d. Map each sentence's char range → ch0 word IDs → word_start_id / word_end_id / text.

Output format
-------------
{
  "source": "data/preprocessed/Student-1/lesson-2/",
  "student": "Student-1",
  "lesson": "lesson-2",
  "partition_method": "...",
  "paragraphs": [
    {
      "paragraph_id": 1,
      "label": "...",
      "conversation_boolean": true,
      "word_start_id": <ch0>,
      "word_end_id":   <ch0>,
      "sentences": [
        {
          "sentence_index": 1,
          "word_start_id":  <ch0>,
          "word_end_id":    <ch0>,
          "text": "..."
        },
        ...
      ]
    },
    ...
  ]
}
"""

import json
import sys
from pathlib import Path

import spacy

ROOT         = Path(__file__).parent.parent.parent
RAW_ROOT     = ROOT / 'data' / 'raw'
PREP_ROOT    = ROOT / 'data' / 'preprocessed'

NLP = spacy.load('en_core_web_sm', disable=['ner', 'lemmatizer', 'attribute_ruler'])


# ── Helpers ──────────────────────────────────────────────────────────────────

def load_ch0_words(student: str, lesson: str) -> list:
    """
    Returns list of dicts (one per ch0 word, in file order):
        {'word_id': int, 'punctuated_word': str}
    Files are read in sorted order (01.json, 02.json, ...).
    """
    raw_dir    = RAW_ROOT / student / lesson
    json_files = sorted(raw_dir.glob('*.json'))
    if not json_files:
        raise FileNotFoundError(f'No raw JSON files found in {raw_dir}')

    ch0_words = []
    for jf in json_files:
        data  = json.loads(jf.read_text('utf-8'))
        words = data['results']['channels'][0]['alternatives'][0]['words']
        for w in words:
            ch0_words.append({
                'word_id':         w['word_id'],
                'punctuated_word': w.get('punctuated_word', w.get('word', '')),
            })
    return ch0_words


def segment_sentences(words_with_ids: list) -> list:
    """
    words_with_ids: list of (ch0_id, punctuated_word) in time order.
    Returns list of dicts:
        {sentence_index, word_start_id, word_end_id, text}
    using spaCy for sentence boundary detection.
    """
    if not words_with_ids:
        return []

    # Build text and track char offset of each word
    text_parts = []
    offsets    = []   # (char_start, char_end) for each word in words_with_ids
    cursor     = 0
    for ch0_id, pw in words_with_ids:
        offsets.append((cursor, cursor + len(pw)))
        text_parts.append(pw)
        cursor += len(pw) + 1  # +1 for the space separator

    full_text = ' '.join(text_parts)
    doc       = NLP(full_text)

    sentences = []
    for sent_idx, sent in enumerate(doc.sents, start=1):
        s_char_start = sent.start_char
        s_char_end   = sent.end_char

        # Words whose char range overlaps with this sentence
        covered = [
            ch0_id
            for i, (ch0_id, _) in enumerate(words_with_ids)
            if offsets[i][0] < s_char_end and offsets[i][1] > s_char_start
        ]
        if not covered:
            continue

        word_start = min(covered)
        word_end   = max(covered)
        # Reconstruct text from the covered words (preserves original tokens)
        sent_words = [
            pw
            for i, (ch0_id, pw) in enumerate(words_with_ids)
            if offsets[i][0] < s_char_end and offsets[i][1] > s_char_start
        ]
        sentences.append({
            'sentence_index': sent_idx,
            'word_start_id':  word_start,
            'word_end_id':    word_end,
            'text':           ' '.join(sent_words),
        })

    return sentences


# ── Core processor ───────────────────────────────────────────────────────────

def process_lesson(student: str, lesson: str):
    prep_dir     = PREP_ROOT / student / lesson
    chunker_path = prep_dir / 'chunker-output.json'
    out_path     = prep_dir / 'sentences.json'

    if not chunker_path.exists():
        print(f'  SKIP {student}/{lesson}: no chunker-output.json')
        return

    print(f'  Processing {student}/{lesson}...')
    chunker   = json.loads(chunker_path.read_text('utf-8'))
    ch0_words = load_ch0_words(student, lesson)

    paragraphs_out = []
    for para in chunker['paragraphs']:
        gs = para['word_start_id']
        ge = para['word_end_id']

        in_range = [w for w in ch0_words if gs <= w['word_id'] <= ge]
        if not in_range:
            paragraphs_out.append({
                'paragraph_id':        para['paragraph_id'],
                'label':               para.get('label', ''),
                'conversation_boolean': para.get('conversation_boolean', True),
                'word_start_id':       None,
                'word_end_id':         None,
                'sentences':           [],
            })
            continue

        words_list = [(w['word_id'], w['punctuated_word']) for w in in_range]
        para_start = in_range[0]['word_id']
        para_end   = in_range[-1]['word_id']

        sentences  = segment_sentences(words_list)

        paragraphs_out.append({
            'paragraph_id':        para['paragraph_id'],
            'label':               para.get('label', ''),
            'conversation_boolean': para.get('conversation_boolean', True),
            'word_start_id':       para_start,
            'word_end_id':         para_end,
            'sentences':           sentences,
        })

        print(f'    para {para["paragraph_id"]}: ch0 words {para_start}–{para_end}, '
              f'{len(sentences)} sentences')

    output = {
        'source':           f'data/preprocessed/{student}/{lesson}/',
        'student':          student,
        'lesson':           lesson,
        'partition_method': chunker.get('partition_method', ''),
        'paragraphs':       paragraphs_out,
    }
    prep_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), 'utf-8')
    print(f'    Wrote {out_path}')


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    # Default: process all lessons that have a chunker-output.json
    # Optional args: python build_data_sentences.py Student-1 lesson-2
    if len(sys.argv) == 3:
        process_lesson(sys.argv[1], sys.argv[2])
    else:
        print('Generating sentences.json for all preprocessed lessons...')
        for student_dir in sorted(PREP_ROOT.iterdir()):
            if not student_dir.is_dir():
                continue
            for lesson_dir in sorted(student_dir.iterdir()):
                if not lesson_dir.is_dir():
                    continue
                process_lesson(student_dir.name, lesson_dir.name)
        print('Done.')
