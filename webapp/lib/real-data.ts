/**
 * Real metric scores extracted from data/processed/{student}/{lesson}/metrics/overall_metrics.json
 * All scores are 0–100. Values are final and won't change.
 * Import this file anywhere — zero I/O, instant access.
 *
 * Score definitions (per overall_metrics.json formula):
 *   overall   = content_score × (fluency_score / 100)   — weighted composite
 *   grammar   = grammar_score  (level 40% + variety 20% + errors 40%)
 *   vocabulary = vocab_score   — CEFR raw normalised: (cefr_raw − 1) / 5 × 100
 *   fluency   = fluency_score  — 0–100 sentence-level fluency average
 */

export interface LessonScore {
  /** Short label used in charts, e.g. "L1" */
  lesson: string;
  /** Weighted composite 0–100 */
  overall: number;
  /** Grammar richness & accuracy 0–100 */
  grammar: number;
  /** Vocabulary CEFR level normalised 0–100 */
  vocabulary: number;
  /** Fluency score 0–100 */
  fluency: number;
}

export interface RealStudentData {
  lessons: { id: number; name: string }[];
  scores: LessonScore[];
}

export const realStudentsData: Record<string, RealStudentData> = {
  "Student-1": {
    lessons: [
      { id: 1, name: "Lesson 1" },
      { id: 2, name: "Lesson 2" },
      { id: 3, name: "Lesson 3" },
    ],
    scores: [
      { lesson: "L1", overall: 15.81, grammar: 37.50, vocabulary: 20.00, fluency: 55.00 },
      { lesson: "L2", overall: 17.14, grammar: 39.99, vocabulary: 20.00, fluency: 57.17 },
      { lesson: "L3", overall: 23.33, grammar: 49.78, vocabulary: 27.33, fluency: 60.31 },
    ],
  },
  "Student-2": {
    lessons: [
      { id: 1, name: "Lesson 1" },
      { id: 2, name: "Lesson 2" },
    ],
    scores: [
      { lesson: "L1", overall: 27.54, grammar: 49.82, vocabulary: 32.82, fluency: 66.60 },
      { lesson: "L2", overall: 25.95, grammar: 45.55, vocabulary: 31.17, fluency: 67.51 },
    ],
  },
};
