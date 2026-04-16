"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import type { RealLessonData, CefrDistribution } from "@/lib/types";

// A1 is excluded; remaining levels rescaled to 100
const LEVELS = ["A2", "B1", "B2", "C1", "C2"] as const;
type Level = (typeof LEVELS)[number];

const BAR_COLOR: Record<Level, string> = {
  A2: "#1D4ED8",
  B1: "#065F46",
  B2: "#92400E",
  C1: "#991B1B",
  C2: "#5B21B6",
};
const BAR_BG: Record<Level, string> = {
  A2: "#DBEAFE",
  B1: "#D1FAE5",
  B2: "#FEF3C7",
  C1: "#FEE2E2",
  C2: "#EDE9FE",
};

function aggregateCefr(chunks: RealLessonData["chunks"]): CefrDistribution {
  const totalWords = chunks.reduce((s, c) => s + c.stats.totalWords, 0);
  if (totalWords === 0) return { A1: 0, A2: 0, B1: 0, B2: 0, C1: 0, C2: 0 };
  const agg: CefrDistribution = { A1: 0, A2: 0, B1: 0, B2: 0, C1: 0, C2: 0 };
  for (const chunk of chunks) {
    const w = chunk.stats.totalWords / totalWords;
    for (const lvl of Object.keys(agg) as (keyof CefrDistribution)[]) {
      agg[lvl] += (chunk.cefrDistribution[lvl] ?? 0) * w;
    }
  }
  return agg;
}

function rescale(dist: CefrDistribution): Record<Level, number> {
  const sum = LEVELS.reduce((s, l) => s + (dist[l] ?? 0), 0);
  const out = {} as Record<Level, number>;
  for (const l of LEVELS) {
    out[l] = sum > 0 ? Math.round(((dist[l] ?? 0) / sum) * 100) : 0;
  }
  return out;
}

function BarChart({ dist }: { dist: CefrDistribution }) {
  const scaled = rescale(dist);
  const maxVal = Math.max(...Object.values(scaled), 1);

  return (
    <div className="flex flex-col gap-3 w-full">
      {LEVELS.map((lvl, i) => (
        <motion.div
          key={lvl}
          className="flex items-center gap-3"
          initial={{ opacity: 0, x: -8 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.35, delay: i * 0.06 }}
        >
          {/* Level badge */}
          <span
            className="w-8 shrink-0 text-center text-[11px] font-bold rounded py-0.5"
            style={{ background: BAR_BG[lvl], color: BAR_COLOR[lvl] }}
          >
            {lvl}
          </span>

          {/* Bar track */}
          <div className="flex-1 rounded-full overflow-hidden" style={{ height: "10px", background: "rgba(0,0,0,0.06)" }}>
            <motion.div
              className="h-full rounded-full"
              style={{ background: BAR_BG[lvl], outline: `1.5px solid ${BAR_COLOR[lvl]}33` }}
              initial={{ width: 0 }}
              animate={{ width: `${(scaled[lvl] / maxVal) * 100}%` }}
              transition={{ duration: 0.6, delay: i * 0.06, ease: "easeOut" }}
            />
          </div>

          {/* Percentage */}
          <span
            className="w-10 shrink-0 text-right text-[12px] font-semibold font-[family-name:var(--font-display)]"
            style={{ color: BAR_COLOR[lvl] }}
          >
            {scaled[lvl]}%
          </span>
        </motion.div>
      ))}
    </div>
  );
}

interface CefrDistributionPaneProps {
  studentId: string;
  lessonId: number;
}

export default function CefrDistributionPane({ studentId, lessonId }: CefrDistributionPaneProps) {
  const [data, setData] = useState<RealLessonData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setData(null);
    setLoading(true);
    fetch(`/api/lesson/${studentId}/${lessonId}`)
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then((d: RealLessonData) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [studentId, lessonId]);

  if (loading) {
    return (
      <div className="flex flex-col gap-3 animate-pulse">
        {LEVELS.map((l) => (
          <div key={l} className="flex items-center gap-3">
            <div className="w-8 h-5 rounded bg-surface-variant shrink-0" />
            <div className="flex-1 h-2.5 rounded-full bg-surface-variant" />
            <div className="w-10 h-4 rounded bg-surface-variant" />
          </div>
        ))}
      </div>
    );
  }

  if (!data) {
    return (
      <p className="text-sm text-on-surface-variant italic font-[family-name:var(--font-body)]">
        No data available.
      </p>
    );
  }

  const dist = aggregateCefr(data.chunks);

  return (
    <div className="flex flex-col gap-5">
      <BarChart dist={dist} />
      {/* Summary chips */}
      <div className="flex gap-2 flex-wrap">
        <span
          className="px-3 py-1 rounded-full text-xs font-semibold"
          style={{ background: "var(--primary)", color: "var(--on-primary)" }}
        >
          Level {data.studentLevel} · {data.studentScore.toFixed(1)}
        </span>
        <span className="text-xs text-on-surface-variant self-center font-[family-name:var(--font-body)]">
          {data.lessonStats.uniqueWords} unique words · Guiraud {data.lessonStats.lexicalDiversity.toFixed(1)}
        </span>
      </div>
    </div>
  );
}
