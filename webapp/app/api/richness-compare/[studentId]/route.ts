import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface RawParagraph {
  paragraph_id: number;
  label: string;
  sentence_count: number;
  stats: {
    total_words: number;
    matched_words: number;
    unique_types: number;
    ttr: number;
    lexical_density: number;
  };
  richness: {
    score: number;
    label: string;
    color: string;
    avg_level_str: string;
    level_score: number;
    variety_score: number;
    level_distribution: Record<string, number>;
  };
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

function stripA1(dist: Record<string, number>): Record<string, number> {
  const copy = { ...dist };
  delete copy["A1"];
  return copy;
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ studentId: string }> }
) {
  const { studentId } = await params;
  const projectRoot = path.join(process.cwd(), "..");
  const studentDir = path.join(projectRoot, "data", "processed", studentId);

  // Discover available lessons
  let lessonDirs: string[];
  try {
    lessonDirs = fs
      .readdirSync(studentDir)
      .filter((d) => d.startsWith("lesson-"))
      .sort();
  } catch {
    return NextResponse.json({ error: "Student not found" }, { status: 404 });
  }

  const lessons: Record<
    string,
    {
      summary: {
        score: number;
        label: string;
        color: string;
        avgLevelStr: string;
        totalWords: number;
        totalMatched: number;
        coverageRate: number;
        paragraphCount: number;
        levelDistribution: Record<string, number>;
      };
      paragraphs: Array<{
        paragraphId: number;
        label: string;
        totalWords: number;
        matchedWords: number;
        coveragePct: number;
        uniqueTypes: number;
        ttr: number;
        lexicalDensity: number;
        avgCefr: string;
        levelDistribution: Record<string, number>;
        score: number;
        scoreLabel: string;
        scoreColor: string;
      }>;
    }
  > = {};

  for (const lessonDir of lessonDirs) {
    const filePath = path.join(
      studentDir,
      lessonDir,
      "vocabulary",
      "vocabulary_richness.json"
    );
    let raw: RawRichnessData;
    try {
      raw = JSON.parse(fs.readFileSync(filePath, "utf-8")) as RawRichnessData;
    } catch {
      continue;
    }

    lessons[lessonDir] = {
      summary: {
        score: raw.summary.overall_richness.score,
        label: raw.summary.overall_richness.label,
        color: raw.summary.overall_richness.color,
        avgLevelStr: raw.summary.overall_richness.avg_level_str,
        totalWords: raw.summary.total_words,
        totalMatched: raw.summary.total_matched,
        coverageRate: raw.summary.coverage_rate,
        paragraphCount: raw.summary.paragraph_count,
        levelDistribution: stripA1(raw.summary.overall_richness.level_distribution),
      },
      paragraphs: raw.paragraphs.map((p) => {
        const covPct =
          p.stats.total_words > 0
            ? Math.round((p.stats.matched_words / p.stats.total_words) * 100)
            : 0;
        return {
          paragraphId: p.paragraph_id,
          label: p.label,
          totalWords: p.stats.total_words,
          matchedWords: p.stats.matched_words,
          coveragePct: covPct,
          uniqueTypes: p.stats.unique_types,
          ttr: p.stats.ttr,
          lexicalDensity: p.stats.lexical_density,
          avgCefr: p.richness.avg_level_str,
          levelDistribution: stripA1(p.richness.level_distribution),
          score: p.richness.score,
          scoreLabel: p.richness.label,
          scoreColor: p.richness.color,
        };
      }),
    };
  }

  return NextResponse.json({
    student: studentId,
    lessons: Object.keys(lessons),
    data: lessons,
  });
}
