"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import CefrMirrorChart from "./CefrMirrorChart";
import type { VocabularyApiResponse, LessonVocabSummary } from "@/lib/vocabulary-types";

interface VocabCompareSummaryProps {
  studentId: string;
  leftId: number;
  rightId: number;
  leftName: string;
  rightName: string;
}

export default function VocabCompareSummary({
  studentId,
  leftId,
  rightId,
  leftName,
  rightName,
}: VocabCompareSummaryProps) {
  const [data, setData] = useState<VocabularyApiResponse | null>(null);

  useEffect(() => {
    fetch(`/api/vocabulary/${studentId}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((d: VocabularyApiResponse | null) => setData(d))
      .catch(() => setData(null));
  }, [studentId]);

  if (!data) return null;

  const leftKey = `lesson-${leftId}`;
  const rightKey = `lesson-${rightId}`;
  const left: LessonVocabSummary | undefined = data.lessonProgress[leftKey];
  const right: LessonVocabSummary | undefined = data.lessonProgress[rightKey];

  if (!left || !right) return null;

  return (
    <div className="flex flex-col gap-6">
      {/* Level badges side by side */}
      <div className="grid grid-cols-2 gap-6">
        <LevelCard lesson={leftName} summary={left} delay={0} />
        <LevelCard lesson={rightName} summary={right} delay={0.1} />
      </div>

      {/* CEFR Mirror Chart */}
      <CefrMirrorChart
        lessonA={leftKey}
        lessonB={rightKey}
        distributionA={left.cefrDistribution}
        distributionB={right.cefrDistribution}
      />
    </div>
  );
}

function LevelCard({
  lesson,
  summary,
  delay,
}: {
  lesson: string;
  summary: LessonVocabSummary;
  delay: number;
}) {
  const { vocabLevel, wordCount } = summary;

  return (
    <motion.div
      className="rounded-2xl bg-surface-lowest p-6 flex items-center gap-5"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
    >
      {/* Score circle */}
      <div
        className="w-14 h-14 rounded-full flex flex-col items-center justify-center shrink-0"
        style={{ background: "var(--primary)", color: "var(--on-primary)" }}
      >
        <span className="text-lg font-bold leading-none">{vocabLevel.score.toFixed(1)}</span>
        <span className="text-[9px] font-medium opacity-80">{vocabLevel.cefrLabel}</span>
      </div>

      <div className="flex flex-col gap-1 min-w-0">
        <span className="text-sm font-semibold text-on-surface font-[family-name:var(--font-display)] truncate">
          {lesson}
        </span>
        <span className="text-xs text-on-surface-variant font-[family-name:var(--font-body)]">
          {wordCount.totalTokens}w · {wordCount.uniqueWords} unique · {vocabLevel.contentWordsScored} scored
        </span>
        {summary.comparison && (
          <span
            className="text-xs font-medium"
            style={{
              color:
                summary.comparison.trend === "positive"
                  ? "var(--secondary-fixed)"
                  : summary.comparison.trend === "negative"
                    ? "var(--primary)"
                    : "var(--on-surface-variant)",
            }}
          >
            {summary.comparison.trend === "positive" ? "\u2191" : summary.comparison.trend === "negative" ? "\u2193" : "\u2192"}{" "}
            {summary.comparison.trend}
          </span>
        )}
      </div>
    </motion.div>
  );
}
