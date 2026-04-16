"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import ChunkCard from "./ChunkCard";
import GrammarChunkCard from "./GrammarChunkCard";
import FluencyDetail from "./FluencyDetail";
import type { RealLessonData, GrammarLessonData, FluencyLessonData } from "@/lib/types";

const tabs = ["Vocabulary", "Grammar", "Fluency"] as const;
type Tab = (typeof tabs)[number];

interface LessonDetailProps {
  lesson: RealLessonData;
  lessonName: string;
  studentId: string;
  lessonId: number;
}

export default function LessonDetail({ lesson, lessonName, studentId, lessonId }: LessonDetailProps) {
  const [activeTab, setActiveTab] = useState<Tab>("Vocabulary");

  // Grammar state
  const [grammarData, setGrammarData] = useState<GrammarLessonData | null>(null);
  const [grammarLoading, setGrammarLoading] = useState(false);
  const [grammarError, setGrammarError] = useState<string | null>(null);
  const [showErrors, setShowErrors] = useState(false);

  // Fluency state
  const [fluencyData, setFluencyData] = useState<FluencyLessonData | null>(null);
  const [fluencyLoading, setFluencyLoading] = useState(false);
  const [fluencyError, setFluencyError] = useState<string | null>(null);

  // Fetch grammar when tab selected
  useEffect(() => {
    if (activeTab !== "Grammar" || grammarData || grammarLoading) return;
    setGrammarLoading(true);
    setGrammarError(null);
    fetch(`/api/lesson/${studentId}/${lessonId}/grammar`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((d: GrammarLessonData) => { setGrammarData(d); setGrammarLoading(false); })
      .catch((e) => { setGrammarError(e.message); setGrammarLoading(false); });
  }, [activeTab, studentId, lessonId, grammarData, grammarLoading]);

  // Fetch fluency when tab selected
  useEffect(() => {
    if (activeTab !== "Fluency" || fluencyData || fluencyLoading) return;
    setFluencyLoading(true);
    setFluencyError(null);
    fetch(`/api/lesson/${studentId}/${lessonId}/fluency`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((d: FluencyLessonData) => { setFluencyData(d); setFluencyLoading(false); })
      .catch((e) => { setFluencyError(e.message); setFluencyLoading(false); });
  }, [activeTab, studentId, lessonId, fluencyData, fluencyLoading]);

  const totalNew = lesson.chunks.reduce((acc, c) => acc + c.stats.newWordsCount, 0);
  const totalAbove = lesson.chunks.reduce((acc, c) => acc + c.stats.aboveLevelCount, 0);

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
          <div>
            <motion.h1
              className="font-[family-name:var(--font-display)] text-[2rem] font-extrabold text-on-surface tracking-tight"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
            >
              {lessonName}
            </motion.h1>
            <motion.p
              className="text-sm text-on-surface-variant font-[family-name:var(--font-body)] mt-0.5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.15, duration: 0.4 }}
            >
              How was this lesson evaluated?
            </motion.p>
          </div>
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

      {/* ── Vocabulary tab ── */}
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
              style={{ background: "var(--primary)", color: "var(--on-primary)" }}
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
                style={{ background: "rgba(64, 224, 208, 0.12)", color: "var(--secondary-fixed)" }}
              >
                {totalNew} new words
              </span>
            )}
            {totalAbove > 0 && (
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
                style={{ background: "rgba(255, 107, 157, 0.10)", color: "var(--primary)" }}
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
          {lesson.chunks.map((chunk, i) => (
            <ChunkCard key={chunk.paragraphId} chunk={chunk} index={i} />
          ))}
        </motion.div>
      )}

      {/* ── Grammar tab ── */}
      {activeTab === "Grammar" && (
        <motion.div
          key="grammar"
          className="flex flex-col gap-6"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {grammarLoading && (
            <div className="flex flex-col gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="w-full rounded-2xl bg-surface-lowest p-8 flex gap-8 animate-pulse">
                  <div className="flex-1 space-y-3">
                    <div className="h-3 w-32 rounded bg-surface-variant" />
                    <div className="h-4 w-full rounded bg-surface-variant" />
                    <div className="h-4 w-3/4 rounded bg-surface-variant" />
                  </div>
                  <div className="w-[35%] space-y-4">
                    {[1, 2, 3].map((j) => (
                      <div key={j} className="space-y-2">
                        <div className="h-2 w-8 rounded bg-surface-variant" />
                        <div className="h-3 rounded-full bg-surface-variant" />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {grammarError && (
            <div className="rounded-2xl bg-surface-lowest p-12 text-center">
              <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
                Grammar data not available for this lesson.
              </p>
            </div>
          )}

          {grammarData && (
            <>
              {/* Summary banner */}
              <div className="flex items-center gap-4 flex-wrap">
                <span
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
                  style={{ background: grammarData.lessonSummary.richnessColor + "22", color: grammarData.lessonSummary.richnessColor, border: `1px solid ${grammarData.lessonSummary.richnessColor}44` }}
                >
                  Richness {grammarData.lessonSummary.avgRichnessScore}
                </span>
                <span
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
                  style={{ background: grammarData.lessonSummary.qualityColor + "22", color: grammarData.lessonSummary.qualityColor, border: `1px solid ${grammarData.lessonSummary.qualityColor}44` }}
                >
                  Quality {grammarData.lessonSummary.qualityScore} · {grammarData.lessonSummary.qualityLevel}
                </span>
                <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
                  {grammarData.lessonSummary.totalErrors} errors
                </span>
                {/* Toggle errors / structures */}
                <button
                  onClick={() => setShowErrors((v) => !v)}
                  className="ml-auto px-4 py-2 rounded-xl text-sm font-medium cursor-pointer transition-colors"
                  style={{
                    background: showErrors ? "var(--primary)" : "rgba(0,0,0,0.06)",
                    color: showErrors ? "var(--on-primary)" : "var(--on-surface-variant)",
                  }}
                >
                  {showErrors ? "Show Structures" : "Show Errors"}
                </button>
              </div>
              {grammarData.paragraphs.map((paragraph, i) => (
                <GrammarChunkCard
                  key={paragraph.paragraphId}
                  paragraph={paragraph}
                  showErrors={showErrors}
                  index={i}
                />
              ))}
            </>
          )}
        </motion.div>
      )}

      {/* ── Fluency tab ── */}
      {activeTab === "Fluency" && (
        <>
          {fluencyLoading && (
            <motion.div
              key="fluency-loading"
              className="flex flex-col gap-6"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              {[1, 2, 3].map((i) => (
                <div key={i} className="w-full rounded-2xl bg-surface-lowest p-8 flex gap-8 animate-pulse">
                  <div className="flex-1 space-y-3">
                    <div className="h-3 w-32 rounded bg-surface-variant" />
                    <div className="h-4 w-full rounded bg-surface-variant" />
                    <div className="h-4 w-3/4 rounded bg-surface-variant" />
                  </div>
                  <div className="w-[33%] space-y-4">
                    {[1, 2, 3, 4].map((j) => (
                      <div key={j} className="space-y-2">
                        <div className="h-2 w-8 rounded bg-surface-variant" />
                        <div className="h-3 rounded-full bg-surface-variant" />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </motion.div>
          )}

          {fluencyError && (
            <motion.div
              key="fluency-error"
              className="rounded-2xl bg-surface-lowest p-12 text-center"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
                Fluency data not available for this lesson.
              </p>
            </motion.div>
          )}

          {fluencyData && <FluencyDetail data={fluencyData} />}
        </>
      )}
    </div>
  );
}
