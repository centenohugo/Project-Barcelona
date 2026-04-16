import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import type { CefrLevel, RichnessData } from "@/lib/types";

interface RawMatch {
  sentence_index: number;
  sentence_text: string;
  word: string;
  lemma: string;
  pos: string;
  cefr_level: string;
  cefr_numeric: number;
}

interface RawParagraph {
  paragraph_id: number;
  label: string;
  sentence_count: number;
  stats: {
    total_words: number;
    content_words: number;
    matched_words: number;
    unique_types: number;
    ttr: number;
    lexical_density: number;
  };
  richness: {
    score: number;
    label: string;
    color: string;
    level_score: number;
    variety_score: number;
    avg_level: number;
    avg_level_str: string;
    distinct_levels: string[];
    level_distribution: Record<string, number>;
    n_matched: number;
  };
  matches: RawMatch[];
}

interface RawRichnessData {
  student: string;
  lesson: string;
  summary: {
    paragraph_count: number;
    total_words: number;
    total_matched: number;
    coverage_rate: number;
    overall_richness: {
      score: number;
      label: string;
      color: string;
      avg_level_str: string;
      level_distribution: Record<string, number>;
    };
  };
  paragraphs: RawParagraph[];
}

const VALID_CEFR = new Set(["A1", "A2", "B1", "B2", "C1", "C2"]);

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ studentId: string; lessonId: string }> }
) {
  const { studentId, lessonId } = await params;
  const lessonKey = `lesson-${lessonId}`;
  const projectRoot = path.join(process.cwd(), "..");

  const filePath = path.join(
    projectRoot,
    "data",
    "processed",
    studentId,
    lessonKey,
    "vocabulary",
    "vocabulary_richness.json"
  );

  let raw: RawRichnessData;
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    raw = JSON.parse(content) as RawRichnessData;
  } catch {
    return NextResponse.json(
      { error: "Vocabulary richness data not found" },
      { status: 404 }
    );
  }

  // Remove A1 from summary level distribution
  const summaryDist = { ...raw.summary.overall_richness.level_distribution };
  delete summaryDist["A1"];

  const result: RichnessData = {
    summary: {
      score: raw.summary.overall_richness.score,
      label: raw.summary.overall_richness.label,
      color: raw.summary.overall_richness.color,
      avgLevelStr: raw.summary.overall_richness.avg_level_str,
      totalWords: raw.summary.total_words,
      totalMatched: raw.summary.total_matched,
      coverageRate: raw.summary.coverage_rate,
      paragraphCount: raw.summary.paragraph_count,
      levelDistribution: summaryDist,
    },
    paragraphs: raw.paragraphs.map((para) => {
      // Group matches by sentence, exclude A1
      const sentenceMap = new Map<
        string,
        { text: string; words: { word: string; cefrLevel: CefrLevel; pos: string }[] }
      >();

      for (const m of para.matches) {
        if (m.cefr_level === "A1") continue;
        if (!VALID_CEFR.has(m.cefr_level)) continue;

        const key = `${m.sentence_index}`;
        if (!sentenceMap.has(key)) {
          sentenceMap.set(key, { text: m.sentence_text, words: [] });
        }
        sentenceMap.get(key)!.words.push({
          word: m.word,
          cefrLevel: m.cefr_level as CefrLevel,
          pos: m.pos,
        });
      }

      // Also add sentences that have no non-A1 matches (from matches with A1 only)
      const allSentences = new Map<number, string>();
      for (const m of para.matches) {
        if (!allSentences.has(m.sentence_index)) {
          allSentences.set(m.sentence_index, m.sentence_text);
        }
      }
      for (const [idx, text] of allSentences) {
        const key = `${idx}`;
        if (!sentenceMap.has(key)) {
          sentenceMap.set(key, { text, words: [] });
        }
      }

      // Sort by sentence index
      const sentences = [...sentenceMap.entries()]
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([, v]) => v);

      // Remove A1 from paragraph level distribution
      const paraDist = { ...para.richness.level_distribution };
      delete paraDist["A1"];

      return {
        paragraphId: para.paragraph_id,
        label: para.label,
        sentenceCount: para.sentence_count,
        richness: {
          score: para.richness.score,
          label: para.richness.label,
          color: para.richness.color,
          avgLevelStr: para.richness.avg_level_str,
          levelScore: para.richness.level_score,
          varietyScore: para.richness.variety_score,
          levelDistribution: paraDist,
        },
        stats: {
          totalWords: para.stats.total_words,
          matchedWords: para.stats.matched_words,
          uniqueTypes: para.stats.unique_types,
          ttr: para.stats.ttr,
          lexicalDensity: para.stats.lexical_density,
        },
        sentences,
      };
    }),
  };

  return NextResponse.json(result);
}
