import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// --- Types for raw JSON files ---

interface RawProgressData {
  student: string;
  lesson: string;
  flags: { is_baseline: boolean };
  tier1: {
    vocab_level: { score: number; cefr_label: string; content_words_scored: number };
    cefr_distribution: Record<string, { count: number; percent: number }>;
    interesting_words: Array<{
      word: string;
      cefr_level: string;
      occurrence_count: number;
      avg_confidence: number;
      context_quality: string;
    }>;
    word_count: { total_tokens: number; unique_words: number; unique_content_words: number };
    chunks: Array<{
      paragraph_id: number;
      label: string;
      vocab_level: { score: number; cefr_label: string; content_words_scored: number };
    }>;
  };
  tier2: {
    comparison: { trend: string; trend_magnitude: number } | null;
    new_vocabulary: {
      total_new: number;
      by_level: Record<string, number>;
      notable_new_words: Array<{ word: string; level: string; source: string }>;
    } | null;
  } | null;
}

interface RawHistoryData {
  student: string;
  lessons_analyzed: string[];
  cumulative_vocabulary: Record<
    string,
    {
      first_seen: string;
      last_seen: string;
      lessons_present: string[];
      levels_by_lesson: Record<string, string>;
      source_by_lesson: Record<string, string>;
    }
  >;
}

// --- Helpers ---

function readJSON<T>(filePath: string): T | null {
  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

const TARGET_POS = new Set(["n", "a", "s", "r"]);

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

function isContentWord(word: string, source: string, cefrLevel: string): boolean {
  const lower = word.toLowerCase();
  if (FUNCTION_WORDS.has(lower)) return false;
  if (lower.length <= 1) return false;
  if (source === "whitelist" || source === "digit") return false;
  if (source === "no_synset" || source === "none") return false;
  if (
    !source.startsWith("wsd:") &&
    word[0] === word[0].toUpperCase() &&
    word[0] !== word[0].toLowerCase() &&
    (cefrLevel === "C2" || cefrLevel === "C1" || cefrLevel === "UNKNOWN")
  ) {
    return false;
  }
  if (source.startsWith("wsd:")) {
    const synset = source.slice(4);
    const parts = synset.split(".");
    if (parts.length >= 2) {
      const pos = parts[parts.length - 2];
      return TARGET_POS.has(pos);
    }
  }
  if (COMMON_VERBS.has(lower)) return false;
  return true;
}

// --- Route handler ---

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ studentId: string }> }
) {
  const { studentId } = await params;
  const projectRoot = path.join(process.cwd(), "..");

  // Read history
  const history = readJSON<RawHistoryData>(
    path.join(projectRoot, "src", "vocabulary", "progress", `${studentId}_history.json`)
  );

  if (!history) {
    return NextResponse.json({ error: "History not found" }, { status: 404 });
  }

  const lessons = history.lessons_analyzed;

  // Read progress for each lesson
  const lessonProgress: Record<string, unknown> = {};
  for (const lesson of lessons) {
    const progress = readJSON<RawProgressData>(
      path.join(projectRoot, "src", "vocabulary", "progress", `${studentId}_${lesson}_progress.json`)
    );
    if (progress) {
      lessonProgress[lesson] = {
        lesson,
        isBaseline: progress.flags.is_baseline,
        vocabLevel: {
          score: progress.tier1.vocab_level.score,
          cefrLabel: progress.tier1.vocab_level.cefr_label,
          contentWordsScored: progress.tier1.vocab_level.content_words_scored,
        },
        cefrDistribution: progress.tier1.cefr_distribution,
        interestingWords: progress.tier1.interesting_words.map((w) => ({
          word: w.word,
          cefrLevel: w.cefr_level,
          occurrenceCount: w.occurrence_count,
          contextQuality: w.context_quality,
        })),
        wordCount: {
          totalTokens: progress.tier1.word_count.total_tokens,
          uniqueWords: progress.tier1.word_count.unique_words,
          uniqueContentWords: progress.tier1.word_count.unique_content_words,
        },
        newVocabulary: progress.tier2?.new_vocabulary
          ? {
              totalNew: progress.tier2.new_vocabulary.total_new,
              byLevel: progress.tier2.new_vocabulary.by_level,
              notableNewWords: progress.tier2.new_vocabulary.notable_new_words,
            }
          : null,
        comparison: progress.tier2?.comparison
          ? {
              trend: progress.tier2.comparison.trend,
              trendMagnitude: progress.tier2.comparison.trend_magnitude,
            }
          : null,
        chunks: (progress.tier1.chunks ?? []).map((c) => ({
          paragraphId: c.paragraph_id,
          label: c.label,
          score: c.vocab_level.score,
          cefrLabel: c.vocab_level.cefr_label,
          contentWordsScored: c.vocab_level.content_words_scored,
        })),
      };
    }
  }

  return NextResponse.json({
    student: studentId,
    lessons,
    lessonProgress,
  });
}
