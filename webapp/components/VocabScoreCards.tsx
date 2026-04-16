"use client";

import { motion } from "framer-motion";
import type { LessonVocabSummary } from "@/lib/vocabulary-types";

interface VocabScoreCardsProps {
  lessonA: string;
  lessonB: string;
  progressA: LessonVocabSummary;
  progressB: LessonVocabSummary;
}

const CEFR_COLORS: Record<string, string> = {
  A1: "#40E0D0",
  A2: "#1A9E8F",
  B1: "#FF6B9D",
  B2: "#E0457B",
  C1: "#4A4744",
  C2: "#121111",
};

const LEVEL_BG: Record<string, string> = {
  A1: "rgba(64, 224, 208, 0.15)",
  A2: "rgba(64, 224, 208, 0.25)",
  B1: "rgba(255, 107, 157, 0.15)",
  B2: "rgba(255, 107, 157, 0.25)",
  C1: "rgba(18, 17, 17, 0.10)",
  C2: "rgba(18, 17, 17, 0.18)",
};

function ScoreCard({
  lesson,
  progress,
  delay,
}: {
  lesson: string;
  progress: LessonVocabSummary;
  delay: number;
}) {
  const label = lesson.replace("lesson-", "Lesson ");
  const cefrColor = CEFR_COLORS[progress.vocabLevel.cefrLabel] ?? "#4A4744";
  const trend = progress.comparison;
  const newVocab = progress.newVocabulary;

  return (
    <motion.div
      className="rounded-2xl bg-surface-lowest p-6 flex flex-col gap-4"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
    >
      {/* Header: lesson name + score badge */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant font-[family-name:var(--font-body)]">
          {label}
        </span>
        <span
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-sm font-bold"
          style={{ background: cefrColor, color: "#fff" }}
        >
          {progress.vocabLevel.score.toFixed(1)}
          <span className="text-xs font-normal opacity-80">
            {progress.vocabLevel.cefrLabel}
          </span>
        </span>
      </div>

      {/* Metrics row */}
      <div className="flex items-center gap-4 flex-wrap">
        <Metric label="Total words" value={String(progress.wordCount.totalTokens)} />
        <Metric label="Unique" value={String(progress.wordCount.uniqueWords)} />
        <Metric
          label="Content"
          value={String(progress.vocabLevel.contentWordsScored)}
        />
      </div>

      {/* Trend */}
      {trend && (
        <div className="flex items-center gap-2">
          <span
            className="text-sm font-semibold"
            style={{
              color:
                trend.trend === "positive"
                  ? "var(--secondary-fixed)"
                  : trend.trend === "negative"
                    ? "var(--primary)"
                    : "var(--on-surface-variant)",
            }}
          >
            {trend.trend === "positive" ? "\u2191" : trend.trend === "negative" ? "\u2193" : "\u2192"}{" "}
            {trend.trend}
          </span>
          <span className="text-xs text-on-surface-variant opacity-60">
            ({trend.trendMagnitude > 0 ? "+" : ""}
            {trend.trendMagnitude.toFixed(2)})
          </span>
        </div>
      )}

      {/* New vocabulary */}
      {newVocab && newVocab.totalNew > 0 && (
        <div className="flex flex-col gap-1.5">
          <span className="text-[10px] font-medium uppercase tracking-wider text-on-surface-variant">
            {newVocab.totalNew} new words
          </span>
          <div className="flex gap-1 flex-wrap">
            {Object.entries(newVocab.byLevel)
              .filter(([, count]) => count > 0)
              .sort(([a], [b]) => {
                const order = ["A1", "A2", "B1", "B2", "C1", "C2"];
                return order.indexOf(a) - order.indexOf(b);
              })
              .map(([level, count]) => (
                <span
                  key={level}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold"
                  style={{
                    background: LEVEL_BG[level] ?? "rgba(0,0,0,0.06)",
                    color: CEFR_COLORS[level] ?? "#4A4744",
                  }}
                >
                  {level}
                  <span style={{ fontWeight: 400, opacity: 0.7 }}>{count}</span>
                </span>
              ))}
          </div>
        </div>
      )}

      {/* Baseline indicator */}
      {progress.isBaseline && (
        <span className="text-[10px] text-on-surface-variant opacity-50 uppercase tracking-wider">
          Baseline lesson
        </span>
      )}
    </motion.div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col">
      <span className="text-[10px] text-on-surface-variant opacity-60 uppercase tracking-wider">
        {label}
      </span>
      <span className="text-sm font-semibold text-on-surface font-[family-name:var(--font-display)] tabular-nums">
        {value}
      </span>
    </div>
  );
}

export default function VocabScoreCards({
  lessonA,
  lessonB,
  progressA,
  progressB,
}: VocabScoreCardsProps) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <ScoreCard lesson={lessonA} progress={progressA} delay={0} />
      <ScoreCard lesson={lessonB} progress={progressB} delay={0.1} />
    </div>
  );
}
