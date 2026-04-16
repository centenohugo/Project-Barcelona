import fs from "fs";
import path from "path";

export interface ChunkVocabScore {
  paragraphId: number;
  label: string;
  score: number;
  cefrLabel: string;
}

export interface LessonVocabProgress {
  lesson: string;
  vocabScore: number;
  chunks: ChunkVocabScore[];
}

export type VocabProgress = Record<string, LessonVocabProgress[]>;

export function loadVocabProgress(): VocabProgress {
  const progressDir = path.join(process.cwd(), "..", "progress");
  const files = fs.readdirSync(progressDir).filter(f => f.endsWith("_progress.json"));

  const result: VocabProgress = {};

  for (const file of files) {
    const raw = fs.readFileSync(path.join(progressDir, file), "utf-8");
    const data = JSON.parse(raw);
    const student: string = data.student;
    const lessonNum = data.lesson.replace("lesson-", "");
    const score: number = data.tier1.vocab_level.score;
    const normalized = Math.round((score / 6) * 100);

    const chunks: ChunkVocabScore[] = (data.tier1.chunks ?? []).map(
      (c: { paragraph_id: number; label: string; vocab_level: { score: number; cefr_label: string } }) => ({
        paragraphId: c.paragraph_id,
        label: c.label,
        score: Math.round((c.vocab_level.score / 6) * 100),
        cefrLabel: c.vocab_level.cefr_label,
      })
    );

    if (!result[student]) result[student] = [];
    result[student].push({ lesson: `L${lessonNum}`, vocabScore: normalized, chunks });
  }

  for (const s of Object.keys(result)) {
    result[s].sort((a, b) => a.lesson.localeCompare(b.lesson));
  }

  return result;
}
