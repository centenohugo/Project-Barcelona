"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";

const CEFR_DISPLAY = ["A2", "B1", "B2", "C1", "C2"] as const;

const CEFR_BG: Record<string, string> = {
  A2: "rgba(64, 224, 208, 0.25)",
  B1: "rgba(255, 107, 157, 0.15)",
  B2: "rgba(255, 107, 157, 0.25)",
  C1: "rgba(18, 17, 17, 0.10)",
  C2: "rgba(18, 17, 17, 0.18)",
};

const CEFR_TXT: Record<string, string> = {
  A2: "var(--secondary-fixed)",
  B1: "var(--primary)",
  B2: "var(--primary)",
  C1: "var(--tertiary, #4A4744)",
  C2: "var(--on-surface)",
};

interface LessonRichness {
  summary: {
    score: number;
    label: string;
    color: string;
    avgLevelStr: string;
    totalWords: number;
    totalMatched: number;
    coverageRate: number;
    paragraphCount: number;
    levelDistribution: Record<string, number>;
  };
  paragraphs: Array<{
    paragraphId: number;
    label: string;
    totalWords: number;
    matchedWords: number;
    coveragePct: number;
    uniqueTypes: number;
    ttr: number;
    lexicalDensity: number;
    avgCefr: string;
    levelDistribution: Record<string, number>;
    score: number;
    scoreLabel: string;
    scoreColor: string;
  }>;
}

interface CompareApiResponse {
  student: string;
  lessons: string[];
  data: Record<string, LessonRichness>;
}

interface RichnessCompareTableProps {
  studentId: string;
  currentLessonId: string;
}

function CefrBadges({ dist }: { dist: Record<string, number> }) {
  return (
    <span className="inline-flex gap-0.5">
      {CEFR_DISPLAY.map((lv) => {
        const n = dist[lv] ?? 0;
        if (!n) return null;
        return (
          <span
            key={lv}
            className="inline-flex items-center gap-0.5 px-1.5 py-0 rounded text-[10px] font-bold"
            style={{ background: CEFR_BG[lv], color: CEFR_TXT[lv] }}
          >
            {lv}
            <span style={{ opacity: 0.6, fontWeight: 400 }}>{n}</span>
          </span>
        );
      })}
    </span>
  );
}

function ScoreBadge({
  score,
  label,
  color,
}: {
  score: number;
  label: string;
  color: string;
}) {
  return (
    <span
      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-bold"
      style={{ background: color, color: "#fff" }}
    >
      {score}
      <span style={{ fontWeight: 400, opacity: 0.8 }}>{label}</span>
    </span>
  );
}

function LessonTable({
  lesson,
  data,
  delay,
}: {
  lesson: string;
  data: LessonRichness;
  delay: number;
}) {
  const label = lesson.replace("lesson-", "Lesson ");

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, duration: 0.4 }}
      className="flex-1 min-w-0"
    >
      {/* Lesson header */}
      <div className="flex items-center gap-3 mb-3">
        <span className="text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant">
          {label}
        </span>
        <ScoreBadge
          score={data.summary.score}
          label={data.summary.label}
          color={data.summary.color}
        />
        <span className="text-[11px] text-on-surface-variant opacity-60">
          avg {data.summary.avgLevelStr}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-[11px] border-collapse">
          <thead>
            <tr className="border-b border-surface-variant">
              <th className="text-left py-1.5 px-2 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                P#
              </th>
              <th className="text-left py-1.5 px-2 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                Topic
              </th>
              <th className="text-center py-1.5 px-1 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                Words
              </th>
              <th className="text-center py-1.5 px-1 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                Cov%
              </th>
              <th className="text-center py-1.5 px-1 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                TTR
              </th>
              <th className="text-center py-1.5 px-1 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                Avg
              </th>
              <th className="py-1.5 px-1 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                CEFR
              </th>
              <th className="py-1.5 px-2 font-medium text-on-surface-variant uppercase tracking-wider text-[10px]">
                Score
              </th>
            </tr>
          </thead>
          <tbody>
            {data.paragraphs.map((p) => (
              <tr
                key={p.paragraphId}
                className="border-b border-surface-low hover:bg-surface-low/50 transition-colors"
              >
                <td className="py-1.5 px-2 font-semibold text-on-surface">
                  {String(p.paragraphId).padStart(2, "0")}
                </td>
                <td className="py-1.5 px-2 text-on-surface max-w-[180px] truncate">
                  {p.label.length > 45 ? p.label.slice(0, 45) + "..." : p.label}
                </td>
                <td className="py-1.5 px-1 text-center text-on-surface-variant">
                  {p.totalWords}
                </td>
                <td className="py-1.5 px-1 text-center text-on-surface-variant">
                  {p.coveragePct}%
                </td>
                <td className="py-1.5 px-1 text-center text-on-surface-variant tabular-nums">
                  {p.ttr.toFixed(2)}
                </td>
                <td className="py-1.5 px-1 text-center font-semibold text-on-surface">
                  {p.avgCefr}
                </td>
                <td className="py-1.5 px-1">
                  <CefrBadges dist={p.levelDistribution} />
                </td>
                <td className="py-1.5 px-2">
                  <ScoreBadge
                    score={p.score}
                    label={p.scoreLabel}
                    color={p.scoreColor}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer stats */}
      <div className="flex items-center gap-3 mt-3 text-[11px] text-on-surface-variant">
        <span>
          {data.summary.totalWords} words · {data.summary.totalMatched} matched ·{" "}
          {(data.summary.coverageRate * 100).toFixed(0)}% coverage
        </span>
      </div>
    </motion.div>
  );
}

export default function RichnessCompareTable({
  studentId,
  currentLessonId,
}: RichnessCompareTableProps) {
  const [apiData, setApiData] = useState<CompareApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lessonA, setLessonA] = useState<string>("");
  const [lessonB, setLessonB] = useState<string>("");

  useEffect(() => {
    setLoading(true);
    fetch(`/api/richness-compare/${studentId}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data: CompareApiResponse | null) => {
        setApiData(data);
        if (data && data.lessons.length >= 2) {
          const currentKey = `lesson-${currentLessonId}`;
          // Default: current lesson as B, previous as A
          if (data.lessons.includes(currentKey)) {
            setLessonB(currentKey);
            const idx = data.lessons.indexOf(currentKey);
            setLessonA(data.lessons[idx > 0 ? idx - 1 : 0]);
          } else {
            setLessonA(data.lessons[data.lessons.length - 2]);
            setLessonB(data.lessons[data.lessons.length - 1]);
          }
        } else if (data && data.lessons.length === 1) {
          setLessonA(data.lessons[0]);
          setLessonB(data.lessons[0]);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [studentId, currentLessonId]);

  if (loading) {
    return (
      <div className="rounded-2xl bg-surface-lowest p-8 animate-pulse">
        <div className="h-4 w-48 rounded bg-surface-variant mb-6" />
        <div className="grid grid-cols-2 gap-8">
          {[0, 1].map((i) => (
            <div key={i} className="space-y-3">
              {[1, 2, 3, 4, 5].map((j) => (
                <div key={j} className="h-3 rounded bg-surface-variant" />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (!apiData || apiData.lessons.length === 0) {
    return (
      <div className="rounded-2xl bg-surface-lowest p-12 text-center">
        <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
          No vocabulary richness data available.
        </p>
      </div>
    );
  }

  const dataA = apiData.data[lessonA];
  const dataB = apiData.data[lessonB];
  const isStudent2 = studentId === "Student-2";

  return (
    <div className="rounded-2xl bg-surface-lowest p-8">
      {/* Header with selectors */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <h3 className="font-[family-name:var(--font-display)] text-lg font-bold text-on-surface tracking-tight">
            Vocabulary Richness
          </h3>
          {isStudent2 && (
            <span
              className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider"
              style={{
                background: "rgba(255, 107, 157, 0.15)",
                color: "var(--primary)",
              }}
            >
              Student 2
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          <select
            value={lessonA}
            onChange={(e) => setLessonA(e.target.value)}
            className="appearance-none rounded-xl bg-surface-low px-4 py-2 text-sm font-[family-name:var(--font-body)] text-on-surface outline-none cursor-pointer"
          >
            {apiData.lessons.map((l) => (
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
            {apiData.lessons.map((l) => (
              <option key={l} value={l}>
                {l.replace("lesson-", "Lesson ")}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Two tables side by side */}
      <div className="grid grid-cols-2 gap-8">
        {dataA && <LessonTable lesson={lessonA} data={dataA} delay={0} />}
        {dataB && <LessonTable lesson={lessonB} data={dataB} delay={0.15} />}
      </div>
    </div>
  );
}
