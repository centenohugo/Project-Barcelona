export interface InterestingWord {
  word: string;
  cefrLevel: string;
  occurrenceCount: number;
  contextQuality: string;
}

export interface NotableNewWord {
  word: string;
  level: string;
  source: string;
}

export interface LessonVocabSummary {
  lesson: string;
  isBaseline: boolean;
  vocabLevel: { score: number; cefrLabel: string; contentWordsScored: number };
  cefrDistribution: Record<string, { count: number; percent: number }>;
  interestingWords: InterestingWord[];
  wordCount: { totalTokens: number; uniqueWords: number; uniqueContentWords: number };
  newVocabulary: {
    totalNew: number;
    byLevel: Record<string, number>;
    notableNewWords: NotableNewWord[];
  } | null;
  comparison: { trend: string; trendMagnitude: number } | null;
  chunks: ChunkScore[];
}

export interface ChunkScore {
  paragraphId: number;
  label: string;
  score: number;
  cefrLabel: string;
  contentWordsScored: number;
}

export interface VocabularyApiResponse {
  student: string;
  lessons: string[];
  lessonProgress: Record<string, LessonVocabSummary>;
}
