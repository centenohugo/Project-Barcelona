import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import type { GrammarLessonData, GrammarMatch, GrammarParagraph } from "@/lib/types";

const DIMENSION_MAP: Record<string, string> = {
  CLAUSES: "A", QUESTIONS: "A", "REPORTED SPEECH": "A",
  CONJUNCTIONS: "A", "DISCOURSE MARKERS": "A",
  PAST: "B", PRESENT: "B", FUTURE: "B", PASSIVES: "B", VERBS: "B", NEGATION: "B",
  PRONOUNS: "C", DETERMINERS: "C", NOUNS: "C",
  ADJECTIVES: "C", ADVERBS: "C", PREPOSITIONS: "C",
  MODALITY: "D", FOCUS: "D",
};

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

  if (!fs.existsSync(richnessPath) || !fs.existsSync(errorsPath)) {
    return NextResponse.json({ error: "Grammar data not found" }, { status: 404 });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const richness: any = JSON.parse(fs.readFileSync(richnessPath, "utf-8"));
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errors: any = JSON.parse(fs.readFileSync(errorsPath, "utf-8"));

  // Build per-paragraph error lookup
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errorsByParagraph: Record<number, any[]> = {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  for (const err of errors.errors as any[]) {
    const pid = err.paragraph_id as number;
    if (!errorsByParagraph[pid]) errorsByParagraph[pid] = [];
    errorsByParagraph[pid].push(err);
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errorParaByPid: Record<number, any> = {};
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  for (const ep of errors.paragraphs as any[]) {
    errorParaByPid[ep.paragraph_id] = ep;
  }

  // Assemble paragraphs
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const paragraphs: GrammarParagraph[] = (richness.paragraphs as any[]).map((rp: any) => {
    const pid: number = rp.paragraph_id;
    const ep = errorParaByPid[pid];

    const matches: GrammarMatch[] = (rp.matches ?? []).map(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (m: any): GrammarMatch => ({
        sentenceIndex: m.sentence_index,
        sentenceText: m.sentence_text,
        category: m.category,
        guideword: m.guideword,
        lowestLevel: m.lowest_level,
        explanation: m.explanation ?? "",
        spanText: m.span_text,
        startChar: m.start_char,
        endChar: m.end_char,
        contextStartChar: m.context_start_char,
        contextEndChar: m.context_end_char,
        dimension: DIMENSION_MAP[m.category] ?? "?",
      })
    );

    const paraErrors = (errorsByParagraph[pid] ?? []).map(
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (e: any) => ({
        sentenceIndex: e.sentence_index,
        sentence: e.sentence,
        paragraphId: e.paragraph_id,
        grammarCategory: e.grammar_category,
        dimensionCode: e.dimension_code,
        dimensionLabel: e.dimension_label,
        weight: e.weight,
        matchedText: e.matched_text,
        message: e.message,
        replacements: e.replacements ?? [],
        offset: e.offset,
        errorLength: e.error_length,
      })
    );

    const r = rp.richness;
    return {
      paragraphId: pid,
      label: rp.label ?? "",
      sentences: (rp.sentences ?? []).map(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (s: any) => ({ index: s.sentence_index, text: s.text })
      ),
      matches,
      errors: paraErrors,
      richness: {
        score: r.score,
        label: r.label,
        color: r.color,
        levelDistribution: r.level_distribution ?? {},
        distinctCategories: r.distinct_categories ?? [],
        dimsPresent: r.dims_present ?? [],
        nAssigned: r.n_assigned,
        density: r.density,
        avgLevelStr: r.avg_level_str,
        levelScore: r.level ?? 0,
        varietyScore: r.variety ?? 0,
      },
      errorStats: ep
        ? {
            count: ep.error_count,
            weightedSum: ep.weighted_error_sum,
            qualityScore: ep.quality_score,
            qualityLevel: ep.quality_level,
            qualityColor: ep.quality_color,
            dimensionCounts: ep.dimension_counts,
          }
        : { count: 0, weightedSum: 0, qualityScore: 100, qualityLevel: "Good", qualityColor: "#15803d", dimensionCounts: { A: 0, B: 0, C: 0, D: 0 } },
    };
  });

  // Lesson-level summary
  const avgRichnessScore =
    paragraphs.length > 0
      ? Math.round(paragraphs.reduce((s, p) => s + p.richness.score, 0) / paragraphs.length)
      : 0;
  const topRichnessP = paragraphs.reduce(
    (best, p) => (p.richness.score > best.richness.score ? p : best),
    paragraphs[0]
  );

  const categoryCounts: Record<string, number> = errors.summary.grammar_category_counts ?? {};
  const topCategories = Object.entries(categoryCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 4)
    .map(([category, count]) => ({ category, count }));

  const data: GrammarLessonData = {
    lessonSummary: {
      avgRichnessScore,
      richnessLabel: topRichnessP?.richness.label ?? "",
      richnessColor: topRichnessP?.richness.color ?? "#6B7280",
      qualityScore: errors.summary.overall_quality_score,
      qualityLevel: errors.summary.overall_quality_level,
      qualityColor: errors.summary.overall_quality_color,
      totalErrors: errors.summary.total_errors,
      dimensionErrorCounts: errors.summary.dimension_counts,
      topCategories,
    },
    paragraphs,
  };

  return NextResponse.json(data);
}
