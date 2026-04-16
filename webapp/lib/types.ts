export type CefrLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";

// --- Enhanced word for display ---

export interface EnhancedWord {
  text: string;
  cefrLevel?: CefrLevel;
  isNew?: boolean;
  isAboveLevel?: boolean;
}

// --- Per-block data ---

export interface CefrDistribution {
  A1: number;
  A2: number;
  B1: number;
  B2: number;
  C1: number;
  C2: number;
}

export interface RealChunkStats {
  totalWords: number;
  uniqueWords: number;
  newWordsCount: number;
  aboveLevelCount: number;
}

export interface RealConversationChunk {
  topic: string;
  paragraphId: number;
  words: EnhancedWord[];
  cefrDistribution: CefrDistribution;
  stats: RealChunkStats;
}

// --- Full lesson response from API ---

export interface LessonInterestingWord {
  word: string;
  cefr_level: string;
  occurrence_count: number;
  context_quality: string;
}

export interface RealLessonData {
  studentLevel: CefrLevel;
  studentScore: number;
  chunks: RealConversationChunk[];
  lessonStats: {
    totalWords: number;
    uniqueWords: number;
    lexicalDiversity: number;
    interestingWords: LessonInterestingWord[];
    newWordsTotal: number;
    retentionRate: number | null;
    trend: string | null;
  };
}
