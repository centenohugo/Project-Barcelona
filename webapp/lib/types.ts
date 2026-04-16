export type CefrLevel = "A1" | "A2" | "B1" | "B2" | "C1" | "C2";

// --- Enhanced word for display ---

export interface EnhancedWord {
  text: string;
  cefrLevel?: CefrLevel;
  isNew?: boolean;
  isAboveLevel?: boolean;
}

// --- Grammar types ---

export interface GrammarMatch {
  sentenceIndex: number;
  sentenceText: string;
  category: string;
  guideword: string;
  lowestLevel: string;
  explanation: string;
  spanText: string;
  startChar: number;
  endChar: number;
  contextStartChar: number;
  contextEndChar: number;
  dimension: string;
}

export interface GrammarError {
  sentenceIndex: number;
  sentence: string;
  paragraphId: number;
  grammarCategory: string;
  dimensionCode: string;
  dimensionLabel: string;
  weight: number;
  matchedText: string;
  message: string;
  replacements: string[];
  offset: number;
  errorLength: number;
}

export interface GrammarParagraph {
  paragraphId: number;
  label: string;
  sentences: { index: number; text: string }[];
  matches: GrammarMatch[];
  errors: GrammarError[];
  richness: {
    score: number;
    label: string;
    color: string;
    levelDistribution: Record<string, number>;
    distinctCategories: string[];
    dimsPresent: string[];
    nAssigned: number;
    density: number;
    avgLevelStr: string;
    levelScore: number;
    varietyScore: number;
  };
  errorStats: {
    count: number;
    weightedSum: number;
    qualityScore: number;
    qualityLevel: string;
    qualityColor: string;
    dimensionCounts: Record<string, number>;
  };
}

export interface GrammarLessonData {
  lessonSummary: {
    avgRichnessScore: number;
    richnessLabel: string;
    richnessColor: string;
    qualityScore: number;
    qualityLevel: string;
    qualityColor: string;
    totalErrors: number;
    dimensionErrorCounts: Record<string, number>;
    topCategories: { category: string; count: number }[];
  };
  paragraphs: GrammarParagraph[];
}

// --- Fluency types ---

export interface FluencyWordData {
  word: string;
  punctuatedWord: string;
  start: number;
  end: number;
  confidence: number;
  speed: number | null;
  isFiller: boolean;
  fillerType: string | null;
  fillerPattern: string | null;
}

export interface FluencyDuplicate {
  phrase: string[];
  occurrences: number;
  matchType: string;
  startIndices: number[];
}

export interface FluencySentenceRecord {
  sentenceId: number;
  text: string;
  wordCount: number;
  gaps: { count: number; mean: number | null };
  fillers: { count: number; rate: number; types: Record<string, number> };
  duplicates: FluencyDuplicate[];
  accuracy: { mean: number | null };
  fluency: { score: number | null; components: { speed: number | null; gaps: number | null; fillers: number | null; dups: number | null } };
  words: FluencyWordData[];
}

export interface FluencyChunk {
  paragraphId: number;
  label: string;
  sentences: FluencySentenceRecord[];
  fluencyScore: number | null;
  compAvgs: { speed: number | null; gaps: number | null; fillers: number | null; dups: number | null };
  fillerCount: number;
  wordCount: number;
}

export interface FluencyLessonData {
  totalSentences: number;
  totalWords: number;
  avgFluency: number;
  fillerCount: number;
  fillerRate: number;
  avgGapMs: number;
  avgAccuracy: number;
  speedThresholds: { p25Ms: number; p75Ms: number; p90Ms: number };
  speedBuckets: { fast: number; normal: number; slow: number; verySlow: number; total: number };
  fillerTypes: Record<string, number>;
  scoreDist: number[];
  compAvgs: { speed: number; gaps: number; fillers: number; dups: number };
  sentences: FluencySentenceRecord[];
  chunks?: FluencyChunk[];
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
