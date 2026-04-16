"use client";

import { useEffect, useState } from "react";
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
    <CefrMirrorChart
      lessonA={leftKey}
      lessonB={rightKey}
      distributionA={left.cefrDistribution}
      distributionB={right.cefrDistribution}
    />
  );
}
