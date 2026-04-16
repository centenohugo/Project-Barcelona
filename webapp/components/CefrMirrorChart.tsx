"use client";

import { motion } from "framer-motion";

const CEFR_LEVELS = ["A2", "B1", "B2", "C1", "C2"];

const levelColors: Record<string, string> = {
  A2: "var(--secondary)",
  B1: "var(--primary)",
  B2: "var(--primary)",
  C1: "var(--tertiary, #4A4744)",
  C2: "var(--tertiary, #4A4744)",
};

interface CefrMirrorChartProps {
  lessonA: string;
  lessonB: string;
  distributionA: Record<string, { count: number; percent: number }>;
  distributionB: Record<string, { count: number; percent: number }>;
}

function redistributeWithoutA1(
  dist: Record<string, { count: number; percent: number }>
): Record<string, number> {
  const a1 = dist.A1?.percent ?? 0;
  const rest = CEFR_LEVELS.reduce((s, l) => s + (dist[l]?.percent ?? 0), 0);
  if (rest === 0) return Object.fromEntries(CEFR_LEVELS.map((l) => [l, 0]));
  const scale = (rest + a1) / rest;
  return Object.fromEntries(
    CEFR_LEVELS.map((l) => [l, Math.round((dist[l]?.percent ?? 0) * scale * 10) / 10])
  );
}

export default function CefrMirrorChart({
  lessonA,
  lessonB,
  distributionA,
  distributionB,
}: CefrMirrorChartProps) {
  const labelA = lessonA.replace("lesson-", "Lesson ");
  const labelB = lessonB.replace("lesson-", "Lesson ");

  const adjA = redistributeWithoutA1(distributionA);
  const adjB = redistributeWithoutA1(distributionB);

  const maxPercent = Math.max(
    ...CEFR_LEVELS.map((l) => adjA[l] ?? 0),
    ...CEFR_LEVELS.map((l) => adjB[l] ?? 0),
    1
  );

  return (
    <div className="rounded-2xl bg-surface-lowest p-8">
      {/* Column headers */}
      <div className="grid grid-cols-[1fr_60px_1fr] items-center mb-6">
        <p className="text-right font-[family-name:var(--font-display)] text-sm font-bold text-on-surface tracking-tight pr-4">
          {labelA}
        </p>
        <p className="text-center font-[family-name:var(--font-display)] text-xs font-semibold text-on-surface-variant uppercase tracking-[0.08em]">
          CEFR
        </p>
        <p className="text-left font-[family-name:var(--font-display)] text-sm font-bold text-on-surface tracking-tight pl-4">
          {labelB}
        </p>
      </div>

      {/* Bars */}
      <div className="flex flex-col gap-2.5">
        {CEFR_LEVELS.map((level, i) => {
          const pctA = adjA[level] ?? 0;
          const pctB = adjB[level] ?? 0;
          const widthA = (pctA / maxPercent) * 100;
          const widthB = (pctB / maxPercent) * 100;
          const color = levelColors[level];

          return (
            <div key={level} className="grid grid-cols-[1fr_60px_1fr] items-center gap-0">
              {/* Left bar (lesson A) — grows from right to left */}
              <div className="flex items-center justify-end gap-2">
                <span className="text-[11px] font-medium text-on-surface-variant tabular-nums min-w-[36px] text-right">
                  {pctA.toFixed(1)}%
                </span>
                <div className="h-7 flex-1 flex justify-end">
                  <motion.div
                    className="h-full rounded-l-lg"
                    style={{ background: color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${widthA}%` }}
                    transition={{ duration: 0.7, delay: i * 0.06, ease: [0.34, 1.56, 0.64, 1] }}
                  />
                </div>
              </div>

              {/* Center label */}
              <div className="flex items-center justify-center">
                <span className="text-xs font-bold text-on-surface">{level}</span>
              </div>

              {/* Right bar (lesson B) — grows from left to right */}
              <div className="flex items-center gap-2">
                <div className="h-7 flex-1 flex justify-start">
                  <motion.div
                    className="h-full rounded-r-lg"
                    style={{ background: color }}
                    initial={{ width: 0 }}
                    animate={{ width: `${widthB}%` }}
                    transition={{ duration: 0.7, delay: i * 0.06, ease: [0.34, 1.56, 0.64, 1] }}
                  />
                </div>
                <span className="text-[11px] font-medium text-on-surface-variant tabular-nums min-w-[36px] text-left">
                  {pctB.toFixed(1)}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
