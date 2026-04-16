"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import ChunkCard from "./ChunkCard";
import type { RealLessonData } from "@/lib/types";

const tabs = ["Vocabulary", "Grammar", "Fluency"] as const;
type Tab = (typeof tabs)[number];

interface LessonDetailProps {
  lesson: RealLessonData;
  lessonName: string;
}

export default function LessonDetail({ lesson, lessonName }: LessonDetailProps) {
  const [activeTab, setActiveTab] = useState<Tab>("Vocabulary");

  const totalNew = lesson.chunks.reduce(
    (acc, c) => acc + c.stats.newWordsCount,
    0
  );
  const totalAbove = lesson.chunks.reduce(
    (acc, c) => acc + c.stats.aboveLevelCount,
    0
  );

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col gap-8 px-8 py-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/#lessons"
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
            {lessonName}
          </motion.h1>
        </div>

        {/* Toggle buttons */}
        <div className="flex gap-1 rounded-2xl p-1">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="relative px-5 py-2 rounded-xl text-sm font-medium transition-colors duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
              style={{
                fontFamily: "var(--font-body)",
                color:
                  activeTab === tab
                    ? "var(--on-primary)"
                    : "var(--on-surface-variant)",
              }}
            >
              {activeTab === tab && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 rounded-xl"
                  style={{ background: "var(--primary)" }}
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span className="relative z-10">{tab}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Vocabulary tab — summary banner + chunks */}
      {activeTab === "Vocabulary" && (
        <motion.div
          key="vocabulary"
          className="flex flex-col gap-6"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {/* Summary banner */}
          <div className="flex items-center gap-4 flex-wrap">
            <span
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
              style={{
                background: "var(--primary)",
                color: "var(--on-primary)",
              }}
            >
              Level {lesson.studentLevel}
              <span className="text-xs font-normal opacity-80">
                ({lesson.studentScore.toFixed(1)})
              </span>
            </span>
            <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
              {lesson.lessonStats.totalWords} words
            </span>
            <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
              {lesson.lessonStats.uniqueWords} unique
            </span>
            <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
              Guiraud {lesson.lessonStats.lexicalDiversity.toFixed(1)}
            </span>
            {totalNew > 0 && (
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
                style={{
                  background: "rgba(64, 224, 208, 0.12)",
                  color: "var(--secondary-fixed)",
                }}
              >
                {totalNew} new words
              </span>
            )}
            {totalAbove > 0 && (
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
                style={{
                  background: "rgba(255, 107, 157, 0.10)",
                  color: "var(--primary)",
                }}
              >
                {totalAbove} above level
              </span>
            )}
            {lesson.lessonStats.trend && (
              <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
                Trend:{" "}
                <span
                  style={{
                    color:
                      lesson.lessonStats.trend === "positive"
                        ? "var(--secondary-fixed)"
                        : lesson.lessonStats.trend === "negative"
                          ? "var(--primary)"
                          : "var(--on-surface-variant)",
                  }}
                >
                  {lesson.lessonStats.trend}
                </span>
              </span>
            )}
          </div>

          {/* Chunks */}
          {lesson.chunks.map((chunk, i) => (
            <ChunkCard key={chunk.paragraphId} chunk={chunk} index={i} />
          ))}
        </motion.div>
      )}

      {/* Grammar / Fluency placeholders */}
      {activeTab !== "Vocabulary" && (
        <motion.div
          key={activeTab}
          className="rounded-2xl bg-surface-lowest p-12 text-center"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
            {activeTab} analysis coming soon.
          </p>
        </motion.div>
      )}
    </div>
  );
}
