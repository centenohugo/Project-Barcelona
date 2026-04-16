"use client";

import { use, useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import Navbar from "@/components/Navbar";
import GrammarComparePane from "@/components/GrammarComparePane";
import FluencyCompareSummary from "@/components/FluencyCompareSummary";
import VocabCompareSummary from "@/components/VocabCompareSummary";
import WordFamilyCloud from "@/components/WordFamilyCloud";
import { useStudent } from "@/lib/student-context";
import { realStudentsData } from "@/lib/real-data";
import type { FluencyLessonData } from "@/lib/types";

type Metric = "vocabulary" | "grammar" | "fluency";

const METRIC_LABELS: Record<Metric, string> = {
  vocabulary: "Vocabulary",
  grammar: "Grammar",
  fluency: "Fluency",
};

const METRIC_COLORS: Record<Metric, string> = {
  vocabulary: "var(--secondary)",
  grammar: "var(--primary)",
  fluency: "#8B5CF6",
};

// ── Skeleton loader ────────────────────────────────────────────────────────────

function PaneSkeleton() {
  return (
    <div className="flex flex-col gap-6">
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          className="w-full rounded-2xl bg-surface-lowest p-8 flex gap-8 animate-pulse"
        >
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
  );
}

// ── Fluency pane ───────────────────────────────────────────────────────────────

function FluencyPane({ studentId, lessonId }: { studentId: string; lessonId: number }) {
  const [data, setData] = useState<FluencyLessonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setLoading(true);
    setError(null);
    fetch(`/api/lesson/${studentId}/${lessonId}/fluency`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((d: FluencyLessonData) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [studentId, lessonId]);

  if (loading) return <PaneSkeleton />;
  if (error || !data) {
    return (
      <div className="rounded-2xl bg-surface-lowest p-8 text-center">
        <p className="text-on-surface-variant font-[family-name:var(--font-body)] text-sm">
          Fluency data not available.
        </p>
      </div>
    );
  }

  return <FluencyCompareSummary data={data} />;
}

// ── Lesson selector ────────────────────────────────────────────────────────────

interface LessonSelectorProps {
  lessons: { id: number; name: string }[];
  value: number;
  onChange: (id: number) => void;
  color: string;
}

function LessonSelector({ lessons, value, onChange, color }: LessonSelectorProps) {
  return (
    <div className="flex gap-2 flex-wrap">
      {lessons.map((l) => (
        <button
          key={l.id}
          onClick={() => onChange(l.id)}
          className="px-4 py-2 rounded-xl text-sm font-medium cursor-pointer transition-all"
          style={{
            background: value === l.id ? color : "rgba(0,0,0,0.06)",
            color: value === l.id ? "#fff" : "var(--on-surface-variant)",
            fontFamily: "var(--font-body)",
          }}
        >
          {l.name}
        </button>
      ))}
    </div>
  );
}

// ── Main page ──────────────────────────────────────────────────────────────────

interface PageProps {
  params: Promise<{ metric: string }>;
}

export default function ComparePage({ params }: PageProps) {
  const { metric: rawMetric } = use(params);
  const metric = (rawMetric as Metric) in METRIC_LABELS ? (rawMetric as Metric) : "vocabulary";

  const { student } = useStudent();
  const lessons = realStudentsData[student]?.lessons ?? [];
  const lessonIds = lessons.map((l) => l.id);

  const [leftId, setLeftId] = useState(lessonIds[0] ?? 1);
  const [rightId, setRightId] = useState(lessonIds[1] ?? 2);

  useEffect(() => {
    const ids = realStudentsData[student]?.lessons.map((l) => l.id) ?? [];
    setLeftId(ids[0] ?? 1);
    setRightId(ids[1] ?? ids[0] ?? 1);
  }, [student]);

  const color = METRIC_COLORS[metric];
  const label = METRIC_LABELS[metric];

  const leftLesson = lessons.find((l) => l.id === leftId);
  const rightLesson = lessons.find((l) => l.id === rightId);

  return (
    <div className="flex flex-col flex-1 bg-surface">
      <Navbar />
      <div className="w-full max-w-[1400px] mx-auto px-8 py-12 flex flex-col gap-8">
        {/* Header */}
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
          <div>
            <motion.h1
              className="font-[family-name:var(--font-display)] text-[2rem] font-extrabold text-on-surface tracking-tight"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
            >
              {label} — Lesson Comparison
            </motion.h1>
            <motion.p
              className="text-sm text-on-surface-variant font-[family-name:var(--font-body)] mt-0.5"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.15, duration: 0.4 }}
            >
            </motion.p>
          </div>
        </div>

        {/* Lesson selectors row */}
        <div className="grid grid-cols-2 gap-6">
          <div className="flex flex-col gap-2">
            <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
              Left — {leftLesson?.name ?? `Lesson ${leftId}`}
            </span>
            <LessonSelector lessons={lessons} value={leftId} onChange={setLeftId} color={color} />
          </div>
          <div className="flex flex-col gap-2">
            <span className="text-xs font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
              Right — {rightLesson?.name ?? `Lesson ${rightId}`}
            </span>
            <LessonSelector lessons={lessons} value={rightId} onChange={setRightId} color={color} />
          </div>
        </div>

        {/* ── Content ── */}
        {metric === "grammar" ? (
          <GrammarComparePane
            key={`${leftId}-${rightId}-${student}`}
            studentId={student}
            leftId={leftId}
            rightId={rightId}
            leftName={leftLesson?.name ?? `Lesson ${leftId}`}
            rightName={rightLesson?.name ?? `Lesson ${rightId}`}
          />
        ) : metric === "vocabulary" ? (
          <>
            {/* CEFR mirror chart */}
            <VocabCompareSummary
              key={`summary-${leftId}-${rightId}-${student}`}
              studentId={student}
              leftId={leftId}
              rightId={rightId}
              leftName={leftLesson?.name ?? `Lesson ${leftId}`}
              rightName={rightLesson?.name ?? `Lesson ${rightId}`}
            />

            {/* Word family clouds */}
            <div className="flex flex-col gap-4">
              <div style={{ height: "1px", background: "var(--surface-variant)" }} />
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
                  Largest word family
                </span>
                <span className="text-[11px] text-on-surface-variant font-[family-name:var(--font-body)]">
                  — showing vocabulary variety per lesson
                </span>
              </div>
              <div className="grid grid-cols-2 gap-6">
                <WordFamilyCloud
                  key={`wc-left-${student}-${leftId}`}
                  studentId={student}
                  lessonId={leftId}
                  lessonName={leftLesson?.name ?? `Lesson ${leftId}`}
                />
                <WordFamilyCloud
                  key={`wc-right-${student}-${rightId}`}
                  studentId={student}
                  lessonId={rightId}
                  lessonName={rightLesson?.name ?? `Lesson ${rightId}`}
                />
              </div>
            </div>
          </>
        ) : (
          /* Fluency — two-column */
          <div className="grid grid-cols-2 gap-6 items-start">
            <motion.div
              key={`left-${leftId}-${student}`}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35 }}
            >
              <FluencyPane studentId={student} lessonId={leftId} />
            </motion.div>
            <motion.div
              key={`right-${rightId}-${student}`}
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.35 }}
            >
              <FluencyPane studentId={student} lessonId={rightId} />
            </motion.div>
          </div>
        )}
      </div>
    </div>
  );
}
