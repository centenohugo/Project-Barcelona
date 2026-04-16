import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import type {
  CefrLevel,
  CefrDistribution,
  EnhancedWord,
  RealConversationChunk,
  RealLessonData,
} from "@/lib/types";
import { isAboveLevel, CEFR_LEVELS } from "@/lib/cefr-utils";

interface RawWord {
  word: string;
  confidence: number;
  cefr_level: string;
  source: string;
}

interface RawParagraph {
  paragraph_id: number;
  label: string;
  total_words: number;
  unique_words: number;
  cefr_distribution: Record<string, { count: number; percent: number }>;
}

interface ContextualOutput {
  words: RawWord[];
  paragraphs: RawParagraph[];
  stats: {
    total_words: number;
    unique_words: number;
    cefr_distribution: Record<string, { count: number; percent: number }>;
    lexical_diversity: { ttr: number };
  };
}

interface ProgressData {
  flags: { is_baseline: boolean };
  tier1: {
    vocab_level: { score: number; cefr_label: string };
    lexical_diversity: { ttr: number; root_ttr: number };
    word_count: { total_tokens: number; unique_words: number };
    interesting_words: Array<{
      word: string;
      cefr_level: string;
      occurrence_count: number;
      context_quality: string;
    }>;
  };
  tier2: {
    comparison: { trend: string } | null;
    new_vocabulary: { total_new: number } | null;
    retention: { overall_rate: number } | null;
  } | null;
}

interface HistoryData {
  cumulative_vocabulary: Record<
    string,
    {
      first_seen: string;
      last_seen: string;
      lessons_present: string[];
    }
  >;
}

function readJSON<T>(filePath: string): T | null {
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

function buildCefrDistribution(
  raw: Record<string, { count: number; percent: number }>
): CefrDistribution {
  return {
    A1: raw.A1?.percent ?? 0,
    A2: raw.A2?.percent ?? 0,
    B1: raw.B1?.percent ?? 0,
    B2: raw.B2?.percent ?? 0,
    C1: raw.C1?.percent ?? 0,
    C2: raw.C2?.percent ?? 0,
  };
}

function isCefrLevel(level: string): level is CefrLevel {
  return CEFR_LEVELS.includes(level as CefrLevel);
}

// --- POS filtering: only highlight nouns, adjectives, adverbs ---

const TARGET_POS = new Set(["n", "a", "s", "r"]); // noun, adj, adj-satellite, adverb

const FUNCTION_WORDS = new Set([
  "the", "a", "an", "is", "are", "was", "were", "am",
  "be", "been", "being", "have", "has", "had", "do",
  "does", "did", "will", "would", "shall", "should",
  "may", "might", "can", "could", "must",
  "i", "you", "he", "she", "it", "we", "they",
  "me", "him", "her", "us", "them",
  "my", "your", "his", "its", "our", "their",
  "mine", "yours", "hers", "ours", "theirs",
  "myself", "yourself", "himself", "herself", "itself",
  "ourselves", "themselves",
  "this", "that", "these", "those",
  "and", "but", "or", "nor", "for", "yet", "so",
  "in", "on", "at", "to", "from", "by", "with", "of",
  "about", "up", "out", "off", "over", "under",
  "into", "onto", "upon", "through", "between", "among",
  "before", "after", "during", "since", "until",
  "not", "no", "if", "then", "than",
  "when", "where", "who", "what", "which", "how",
  "there", "here", "very", "just", "also", "too",
  "as", "all", "each", "every", "both", "some", "any",
  "much", "many", "more", "most", "such",
  "oh", "yeah", "yes", "ok", "okay", "um", "uh", "ah",
  "well", "right", "like", "so", "now", "then",
]);

const COMMON_VERBS = new Set([
  "go", "get", "make", "know", "think", "take", "see", "come", "want",
  "look", "use", "find", "give", "tell", "work", "call", "try", "ask",
  "need", "feel", "become", "leave", "put", "mean", "keep", "let",
  "begin", "seem", "help", "show", "hear", "play", "run", "move",
  "live", "believe", "hold", "bring", "happen", "write", "provide",
  "sit", "stand", "lose", "pay", "meet", "include", "continue",
  "set", "learn", "change", "lead", "understand", "watch", "follow",
  "stop", "create", "speak", "read", "allow", "add", "spend", "grow",
  "open", "walk", "win", "offer", "remember", "love", "consider",
  "appear", "buy", "wait", "serve", "die", "send", "expect", "build",
  "stay", "fall", "cut", "reach", "kill", "remain", "say", "said",
  "going", "doing", "getting", "making", "coming", "looking",
  "working", "trying", "asking", "telling", "speaking", "reading",
  "learning", "playing", "listening", "talking", "using", "started",
  "wanted", "needed", "helped", "called", "asked", "told", "gave",
  "took", "went", "came", "got", "made", "saw", "knew", "thought",
  "done", "gone", "seen", "taken", "given", "left", "found",
  "talk", "listen", "start", "prepare", "practice", "teach", "teaches",
  "taught", "study", "studied", "cook", "enjoy", "miss", "drive",
  "saying", "taking", "giving", "knowing", "thinking", "seeing",
  "putting", "keeping", "letting", "leaving", "running", "sitting",
  "standing", "paying", "meeting", "setting", "spending", "growing",
  "walking", "winning", "offering", "remembering", "buying", "waiting",
  "sending", "building", "staying", "falling", "reaching",
]);

/**
 * Determine if a word is a content word (noun, adjective, adverb).
 * Uses WSD synset POS when available; falls back to exclusion lists.
 */
function isContentWord(word: string, source: string, cefrLevel: string): boolean {
  const lower = word.toLowerCase();

  // Always exclude function words, single chars, digits
  if (FUNCTION_WORDS.has(lower)) return false;
  if (lower.length <= 1) return false;
  if (source === "whitelist" || source === "digit") return false;
  if (source === "no_synset" || source === "none") return false;

  // Filter likely proper nouns: capitalized + non-WSD source + high level
  // Proper nouns get classified as C2/UNKNOWN by cefrpy but aren't real vocabulary
  if (
    !source.startsWith("wsd:") &&
    word[0] === word[0].toUpperCase() &&
    word[0] !== word[0].toLowerCase() &&
    (cefrLevel === "C2" || cefrLevel === "C1" || cefrLevel === "UNKNOWN")
  ) {
    return false;
  }

  // WSD source: extract POS from synset name (e.g., "wsd:beautiful.s.01")
  if (source.startsWith("wsd:")) {
    const synset = source.slice(4);
    const parts = synset.split(".");
    if (parts.length >= 2) {
      const pos = parts[parts.length - 2];
      return TARGET_POS.has(pos);
    }
  }

  // cefrpy / lemma_fallback: exclude known verbs, keep the rest
  if (COMMON_VERBS.has(lower)) return false;

  return true;
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ studentId: string; lessonId: string }> }
) {
  const { studentId, lessonId } = await params;
  const lessonKey = `lesson-${lessonId}`;
  const projectRoot = path.join(process.cwd(), "..");

  // Read all required JSON files
  const contextual = readJSON<ContextualOutput>(
    path.join(projectRoot, "src", "vocabulary", "output", `${studentId}_${lessonKey}_contextual.json`)
  );
  if (!contextual) {
    return NextResponse.json(
      { error: "Contextual output not found" },
      { status: 404 }
    );
  }

  const progress = readJSON<ProgressData>(
    path.join(projectRoot, "src", "vocabulary", "progress", `${studentId}_${lessonKey}_progress.json`)
  );
  if (!progress) {
    return NextResponse.json(
      { error: "Progress data not found" },
      { status: 404 }
    );
  }

  const history = readJSON<HistoryData>(
    path.join(projectRoot, "src", "vocabulary", "progress", `${studentId}_history.json`)
  );

  // Student level from progress
  const studentLevelStr = progress.tier1.vocab_level.cefr_label;
  const studentLevel: CefrLevel = isCefrLevel(studentLevelStr)
    ? studentLevelStr
    : "A1";
  const studentScore = progress.tier1.vocab_level.score;

  // Build a set of new words for this lesson (first_seen === lessonKey)
  // Skip for baseline lesson — all words are "new" by definition, which isn't useful
  const isBaseline = progress.flags.is_baseline;
  const newWordsSet = new Set<string>();
  if (!isBaseline && history) {
    for (const [word, entry] of Object.entries(history.cumulative_vocabulary)) {
      if (entry.first_seen === lessonKey) {
        newWordsSet.add(word);
      }
    }
  }

  // Slice flat words array by paragraph boundaries
  const chunks: RealConversationChunk[] = [];
  let offset = 0;

  for (const para of contextual.paragraphs) {
    const paraWords = contextual.words.slice(offset, offset + para.total_words);
    offset += para.total_words;

    let newWordsCount = 0;
    let aboveLevelCount = 0;

    const words: EnhancedWord[] = paraWords.map((w) => {
      const cefrLevel = isCefrLevel(w.cefr_level) ? w.cefr_level : undefined;
      const wordLower = w.word.toLowerCase();
      const content = isContentWord(w.word, w.source, w.cefr_level);

      // Only mark content words (nouns, adjectives, adverbs) as highlighted
      const isNew = content && newWordsSet.has(wordLower);
      const above =
        content &&
        cefrLevel !== undefined &&
        isAboveLevel(cefrLevel, studentLevel);

      if (isNew) newWordsCount++;
      if (above) aboveLevelCount++;

      return {
        text: w.word,
        cefrLevel: content ? cefrLevel : undefined,
        isNew,
        isAboveLevel: above,
      };
    });

    chunks.push({
      topic: para.label,
      paragraphId: para.paragraph_id,
      words,
      cefrDistribution: buildCefrDistribution(para.cefr_distribution),
      stats: {
        totalWords: para.total_words,
        uniqueWords: para.unique_words,
        newWordsCount,
        aboveLevelCount,
      },
    });
  }

  // Build lesson-level stats
  const tier2 = progress.tier2;
  const lessonData: RealLessonData = {
    studentLevel,
    studentScore,
    chunks,
    lessonStats: {
      totalWords: progress.tier1.word_count.total_tokens,
      uniqueWords: progress.tier1.word_count.unique_words,
      lexicalDiversity: progress.tier1.lexical_diversity.root_ttr,
      interestingWords: progress.tier1.interesting_words.map((w) => ({
        word: w.word,
        cefr_level: w.cefr_level,
        occurrence_count: w.occurrence_count,
        context_quality: w.context_quality,
      })),
      newWordsTotal: tier2?.new_vocabulary?.total_new ?? 0,
      retentionRate: tier2?.retention?.overall_rate ?? null,
      trend: tier2?.comparison?.trend ?? null,
    },
  };

  return NextResponse.json(lessonData);
}
