"""
Copies raw ASR JSON files to data/raw/ adding a sequential word_id
to every channel-0 word (learner speech), numbered 1..N per lesson.

Files are processed in sorted order (01.json, 02.json, ...).
Words are numbered in the order they appear in each file's
  results.channels[0].alternatives[0].words
Counter continues across files so IDs are unique within the lesson.
"""

import json
from pathlib import Path

ROOT    = Path(__file__).parent.parent
RAW_IN  = ROOT / 'raw_data' / 'TheEuropaHack_PublicDataSample'
RAW_OUT = ROOT / 'data' / 'raw'


def process_lesson(student_name: str, lesson_name: str):
    in_dir  = RAW_IN  / student_name / lesson_name
    out_dir = RAW_OUT / student_name / lesson_name
    out_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(in_dir.glob('[0-9]*.json'))
    if not json_files:
        return

    counter = 1
    for jf in json_files:
        data  = json.loads(jf.read_text('utf-8'))
        words = data['results']['channels'][0]['alternatives'][0]['words']
        for word in words:
            word['word_id'] = counter
            counter += 1
        (out_dir / jf.name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), 'utf-8'
        )

    print(f'  {student_name}/{lesson_name}: {counter - 1} ch0 words across '
          f'{len(json_files)} files')


if __name__ == '__main__':
    print('Building data/raw/ with channel-0 word_id...')
    for student_dir in sorted(RAW_IN.iterdir()):
        if not student_dir.is_dir():
            continue
        for lesson_dir in sorted(student_dir.iterdir()):
            if not lesson_dir.is_dir():
                continue
            process_lesson(student_dir.name, lesson_dir.name)
    print('Done.')
