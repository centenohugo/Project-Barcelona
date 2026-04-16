import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import type { FluencyLessonData, FluencySentenceRecord, FluencyWordData, FluencyChunk } from "@/lib/types";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type RawWord = Record<string, any>;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type RawSentence = Record<string, any>;

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ studentId: string; lessonId: string }> }
) {
  const { studentId, lessonId } = await params;
  const projectRoot = path.join(process.cwd(), "..");
  const fluencyPath = path.join(
    projectRoot,
    "data",
    "processed",
    studentId,
    `lesson-${lessonId}`,
    "fluency.json"
  );

  if (!fs.existsSync(fluencyPath)) {
    return NextResponse.json({ error: "Fluency data not found" }, { status: 404 });
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const raw: any = JSON.parse(fs.readFileSync(fluencyPath, "utf-8"));
  const rawSentences: RawSentence[] = raw.sentences ?? [];

  // Collect all non-filler word speeds for percentile thresholds
  const allSpeeds: number[] = [];
  for (const sentence of rawSentences) {
    for (const word of (sentence.words ?? []) as RawWord[]) {
      if (word.speed != null && !word.is_filler) {
        allSpeeds.push(word.speed as number);
      }
    }
  }
  allSpeeds.sort((a, b) => a - b);

  const n = allSpeeds.length || 1;
  const p25 = allSpeeds[Math.floor(n * 0.25)] ?? 0.06;
  const p75 = allSpeeds[Math.floor(n * 0.75)] ?? 0.12;
  const p90 = allSpeeds[Math.floor(n * 0.9)] ?? 0.2;

  // Flatten all words
  const allWords: RawWord[] = rawSentences.flatMap((s) => (s.words ?? []) as RawWord[]);
  const fillerCount = allWords.filter((w) => w.is_filler).length;
  const fillerRate =
    allWords.length > 0
      ? Math.round((fillerCount / allWords.length) * 1000) / 10
      : 0;

  // Fluency score averages
  const fluencyScores = rawSentences
    .map((s) => s.fluency?.score as number | undefined)
    .filter((v): v is number => v != null);
  const avgFluency = fluencyScores.length
    ? Math.round((fluencyScores.reduce((a, b) => a + b, 0) / fluencyScores.length) * 10) / 10
    : 0;

  // Accuracy
  const accValues = rawSentences
    .map((s) => s.accuracy?.mean as number | undefined)
    .filter((v): v is number => v != null);
  const avgAccuracy = accValues.length
    ? Math.round((accValues.reduce((a, b) => a + b, 0) / accValues.length) * 1000) / 10
    : 0;

  // Average inter-word gap
  const allGaps: number[] = [];
  for (const sentence of rawSentences) {
    const ws: RawWord[] = sentence.words ?? [];
    for (let i = 0; i < ws.length - 1; i++) {
      const gap = (ws[i + 1].start as number) - (ws[i].end as number);
      if (gap >= 0) allGaps.push(gap);
    }
  }
  const avgGapMs = allGaps.length
    ? Math.round((allGaps.reduce((a, b) => a + b, 0) / allGaps.length) * 1000)
    : 0;

  // Speed buckets (based on percentile thresholds)
  const speedBuckets = { fast: 0, normal: 0, slow: 0, verySlow: 0, total: 0 };
  for (const word of allWords) {
    const sp = word.speed as number | null;
    if (sp == null) continue;
    speedBuckets.total++;
    if (sp < p25) speedBuckets.fast++;
    else if (sp <= p75) speedBuckets.normal++;
    else if (sp <= p90) speedBuckets.slow++;
    else speedBuckets.verySlow++;
  }

  // Filler type counts
  const fillerTypes: Record<string, number> = {};
  for (const word of allWords) {
    if (word.is_filler && word.filler_type) {
      const ft = word.filler_type as string;
      fillerTypes[ft] = (fillerTypes[ft] ?? 0) + 1;
    }
  }

  // Fluency score distribution: 5 buckets [0-20, 20-40, 40-60, 60-80, 80-100]
  const scoreDist = [0, 0, 0, 0, 0];
  for (const sc of fluencyScores) {
    scoreDist[Math.min(Math.floor(sc / 20), 4)]++;
  }

  // Component score averages
  const compSums = { speed: 0, gaps: 0, fillers: 0, dups: 0 };
  const compCounts = { speed: 0, gaps: 0, fillers: 0, dups: 0 };
  for (const sentence of rawSentences) {
    const comps = sentence.fluency?.components ?? {};
    for (const k of ["speed", "gaps", "fillers", "dups"] as const) {
      const v = comps[k] as number | undefined;
      if (v != null) {
        compSums[k] += v;
        compCounts[k]++;
      }
    }
  }
  const compAvgs = {
    speed: compCounts.speed
      ? Math.round((compSums.speed / compCounts.speed) * 10) / 10
      : 0,
    gaps: compCounts.gaps
      ? Math.round((compSums.gaps / compCounts.gaps) * 10) / 10
      : 0,
    fillers: compCounts.fillers
      ? Math.round((compSums.fillers / compCounts.fillers) * 10) / 10
      : 0,
    dups: compCounts.dups
      ? Math.round((compSums.dups / compCounts.dups) * 10) / 10
      : 0,
  };

  // Build per-sentence records
  const sentences: FluencySentenceRecord[] = rawSentences.map((s) => {
    const words: FluencyWordData[] = ((s.words ?? []) as RawWord[]).map((w) => ({
      word: w.word as string,
      punctuatedWord: w.punctuated_word as string,
      start: w.start as number,
      end: w.end as number,
      confidence: w.confidence as number,
      speed: (w.speed as number | null) ?? null,
      isFiller: Boolean(w.is_filler),
      fillerType: (w.filler_type as string | null) ?? null,
      fillerPattern: (w.filler_pattern as string | null) ?? null,
    }));

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const dups = (s.duplicates ?? []) as any[];

    return {
      sentenceId: s.sentence_id as number,
      text: s.text as string,
      wordCount: s.word_count as number,
      gaps: {
        mean: (s.gaps?.mean as number | null) ?? null,
        count: (s.gaps?.count as number) ?? 0,
      },
      fillers: {
        count: (s.fillers?.count as number) ?? 0,
        rate: (s.fillers?.rate as number) ?? 0,
        types: (s.fillers?.types as Record<string, number>) ?? {},
      },
      duplicates: dups.map((d) => ({
        phrase: (d.phrase as string[]) ?? [],
        occurrences: (d.occurrences as number) ?? 0,
        matchType: (d.match_type as string) ?? "exact",
        startIndices: (d.start_indices as number[]) ?? [],
      })),
      accuracy: { mean: (s.accuracy?.mean as number | null) ?? null },
      fluency: {
        score: (s.fluency?.score as number | null) ?? null,
        components: {
          speed: (s.fluency?.components?.speed as number | null) ?? null,
          gaps: (s.fluency?.components?.gaps as number | null) ?? null,
          fillers: (s.fluency?.components?.fillers as number | null) ?? null,
          dups: (s.fluency?.components?.dups as number | null) ?? null,
        },
      },
      words,
    };
  });

  // Group sentences into grammar chunks if grammar_richness.json exists
  let chunks: FluencyChunk[] | undefined;
  const grammarPath = path.join(
    projectRoot, "data", "processed", studentId, `lesson-${lessonId}`, "grammar", "grammar_richness.json"
  );
  if (fs.existsSync(grammarPath)) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const gRaw: any = JSON.parse(fs.readFileSync(grammarPath, "utf-8"));
    const chunkRanges: { paragraphId: number; wordStart: number; wordEnd: number; label: string }[] =
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (gRaw.paragraphs ?? []).map((p: any) => ({
        paragraphId: p.paragraph_id as number,
        wordStart: p.word_start_id as number,
        wordEnd: p.word_end_id as number,
        label: (p.label as string) ?? "",
      }));

    const chunkSentencesMap = new Map<number, FluencySentenceRecord[]>(
      chunkRanges.map((c) => [c.paragraphId, []])
    );

    let cum = 0;
    for (const sentence of sentences) {
      const startWord = cum + 1;
      cum += sentence.wordCount;
      for (const cr of chunkRanges) {
        if (cr.wordStart <= startWord && startWord <= cr.wordEnd) {
          chunkSentencesMap.get(cr.paragraphId)!.push(sentence);
          break;
        }
      }
    }

    chunks = chunkRanges.map((cr) => {
      const sents = chunkSentencesMap.get(cr.paragraphId) ?? [];
      const scores = sents.map((s) => s.fluency.score).filter((s): s is number => s !== null);
      const fluencyScore =
        scores.length > 0
          ? Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 10) / 10
          : null;
      const wc = sents.reduce((s, sent) => s + sent.wordCount, 0);
      const fc = sents.reduce((s, sent) => s + sent.fillers.count, 0);
      const ca: FluencyChunk["compAvgs"] = { speed: null, gaps: null, fillers: null, dups: null };
      for (const key of ["speed", "gaps", "fillers", "dups"] as const) {
        const vals = sents.map((s) => s.fluency.components[key]).filter((v): v is number => v !== null);
        ca[key] = vals.length > 0 ? Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10) / 10 : null;
      }
      return { paragraphId: cr.paragraphId, label: cr.label, sentences: sents, fluencyScore, compAvgs: ca, fillerCount: fc, wordCount: wc };
    });
  }

  const data: FluencyLessonData = {
    totalWords: raw.total_words as number,
    totalSentences: raw.total_sentences as number,
    avgFluency,
    fillerRate,
    avgAccuracy,
    avgGapMs,
    fillerCount,
    speedThresholds: {
      p25Ms: Math.round(p25 * 1000),
      p75Ms: Math.round(p75 * 1000),
      p90Ms: Math.round(p90 * 1000),
    },
    speedBuckets,
    fillerTypes,
    scoreDist,
    compAvgs,
    sentences,
    chunks,
  };

  return NextResponse.json(data);
}
