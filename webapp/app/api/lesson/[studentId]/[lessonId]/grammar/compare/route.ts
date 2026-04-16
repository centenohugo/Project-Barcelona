import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ studentId: string; lessonId: string }> }
) {
  const { studentId, lessonId } = await params;
  const projectRoot = path.join(process.cwd(), "..");
  const lessonKey = `lesson-${lessonId}`;

  const richnessPath = path.join(
    projectRoot, "data", "processed", studentId, lessonKey, "grammar", "grammar_richness.json"
  );
  const errorsPath = path.join(
    projectRoot, "data", "processed", studentId, lessonKey, "errors", "errors.json"
  );

  if (!fs.existsSync(richnessPath)) {
    return NextResponse.json({ error: "Grammar data not found" }, { status: 404 });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const richness: any = JSON.parse(fs.readFileSync(richnessPath, "utf-8"));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errors: any = fs.existsSync(errorsPath)
    ? JSON.parse(fs.readFileSync(errorsPath, "utf-8"))
    : null;

  // ── Aggregate structures by structure_id ─────────────────────────────────────
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const structMap: Record<string, any> = {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  for (const para of richness.paragraphs as any[]) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const m of (para.matches ?? []) as any[]) {
      const sid: string = m.structure_id;
      if (!structMap[sid]) {
        structMap[sid] = {
          structureId: sid,
          category: m.category,
          guideword: m.guideword,
          lowestLevel: m.lowest_level,
          lowestLevelNumeric: m.lowest_level_numeric,
          count: 0,
          exampleSentence: m.sentence_text,
          exampleSpan: m.span_text,
        };
      }
      structMap[sid].count++;
    }
  }

  // Sort: level desc → count desc, take top 20
  const structures = Object.values(structMap)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .sort((a: any, b: any) =>
      b.lowestLevelNumeric - a.lowestLevelNumeric || b.count - a.count
    )
    .slice(0, 20);

  // ── Aggregate errors by grammar_category ─────────────────────────────────────
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errorMap: Record<string, any> = {};
  if (errors) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const err of (errors.errors ?? []) as any[]) {
      const cat: string = err.grammar_category;
      if (!errorMap[cat]) {
        errorMap[cat] = {
          grammarCategory: cat,
          dimensionCode: err.dimension_code,
          dimensionLabel: err.dimension_label,
          weight: err.weight,
          count: 0,
          exampleSentence: err.sentence,
          exampleMatchedText: err.matched_text,
          exampleMessage: err.message,
          exampleOffset: err.offset,
          exampleLength: err.error_length,
        };
      }
      errorMap[cat].count++;
    }
  }

  const errorList = Object.values(errorMap)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    .sort((a: any, b: any) => b.count - a.count)
    .slice(0, 10);

  // ── Stats ─────────────────────────────────────────────────────────────────────
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const paragraphs = richness.paragraphs as any[];
  const sentenceCount = paragraphs.reduce(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (s: number, p: any) => s + (p.sentence_count as number ?? 0), 0
  );
  const avgRichnessScore =
    paragraphs.length > 0
      ? Math.round(
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          paragraphs.reduce((s: number, p: any) => s + (p.richness.score as number), 0) /
            paragraphs.length
        )
      : 0;

  return NextResponse.json({
    structures,
    errors: errorList,
    stats: {
      sentenceCount,
      structureCount: Object.keys(structMap).length,
      errorTypeCount: Object.keys(errorMap).length,
      avgRichnessScore,
    },
  });
}
