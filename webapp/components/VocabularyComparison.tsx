"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import CefrMirrorChart from "./CefrMirrorChart";
import VocabScoreCards from "./VocabScoreCards";
import ScoreEvolutionChart from "./ScoreEvolutionChart";
import type { VocabularyApiResponse } from "@/lib/vocabulary-types";

interface VocabularyComparisonProps {
  data: VocabularyApiResponse;
}

export default function VocabularyComparison({ data }: VocabularyComparisonProps) {
  const { lessons, lessonProgress } = data;

  const [lessonA, setLessonA] = useState(lessons.length >= 2 ? lessons[lessons.length - 2] : lessons[0]);
  const [lessonB, setLessonB] = useState(lessons[lessons.length - 1]);

  if (lessons.length < 2) {
    return (
      <div className="w-full max-w-6xl mx-auto px-8 py-12">
        <div className="rounded-2xl bg-surface-lowest p-12 text-center">
          <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
            At least 2 lessons are needed for comparison.
          </p>
        </div>
      </div>
    );
  }

  const progressA = lessonProgress[lessonA];
  const progressB = lessonProgress[lessonB];

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col gap-8 px-8 py-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/#charts"
            className="w-10 h-10 rounded-xl flex items-center justify-center text-on-surface-variant transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M12.5 15L7.5 10L12.5 5"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </Link>
          <motion.h1
            className="font-[family-name:var(--font-display)] text-[2rem] font-extrabold text-on-surface tracking-tight"
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
          >
            Vocabulary
          </motion.h1>
        </div>

        {/* Lesson selectors */}
        <div className="flex items-center gap-3">
          <select
            value={lessonA}
            onChange={(e) => setLessonA(e.target.value)}
            className="appearance-none rounded-xl bg-surface-low px-4 py-2 text-sm font-[family-name:var(--font-body)] text-on-surface outline-none cursor-pointer"
          >
            {lessons.map((l) => (
              <option key={l} value={l}>
                {l.replace("lesson-", "Lesson ")}
              </option>
            ))}
          </select>
          <span className="text-on-surface-variant text-sm">vs</span>
          <select
            value={lessonB}
            onChange={(e) => setLessonB(e.target.value)}
            className="appearance-none rounded-xl bg-surface-low px-4 py-2 text-sm font-[family-name:var(--font-body)] text-on-surface outline-none cursor-pointer"
          >
            {lessons.map((l) => (
              <option key={l} value={l}>
                {l.replace("lesson-", "Lesson ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Methodology note */}
      <p className="text-sm text-on-surface-variant font-[family-name:var(--font-body)] leading-relaxed max-w-3xl">
        Each word is classified into a CEFR level (A1–C2) using Word Sense Disambiguation.
        The chart below compares how vocabulary distributes across proficiency levels in each lesson.
      </p>

      {/* Score Summary Cards */}
      {progressA && progressB && (
        <VocabScoreCards
          lessonA={lessonA}
          lessonB={lessonB}
          progressA={progressA}
          progressB={progressB}
        />
      )}

      {/* CEFR Mirror Chart */}
      {progressA && progressB && (
        <CefrMirrorChart
          lessonA={lessonA}
          lessonB={lessonB}
          distributionA={progressA.cefrDistribution}
          distributionB={progressB.cefrDistribution}
        />
      )}

      {/* Score Evolution */}
      {progressA && progressB && (
        <ScoreEvolutionChart
          lessonA={lessonA}
          lessonB={lessonB}
          chunksA={progressA.chunks ?? []}
          chunksB={progressB.chunks ?? []}
          avgScoreA={progressA.vocabLevel.score}
          avgScoreB={progressB.vocabLevel.score}
        />
      )}
    </div>
  );
}
