"use client";

import { motion } from "framer-motion";
import type { ChunkScore } from "@/lib/vocabulary-types";

interface ScoreEvolutionChartProps {
  lessonA: string;
  lessonB: string;
  chunksA: ChunkScore[];
  chunksB: ChunkScore[];
  avgScoreA: number;
  avgScoreB: number;
}

const MIN_SCORE = 1;
const MAX_SCORE = 4.5;

const CEFR_LINES = [
  { label: "A1", value: 1, color: "var(--secondary)" },
  { label: "A2", value: 2, color: "var(--secondary)" },
  { label: "B1", value: 3, color: "var(--primary)" },
  { label: "B2", value: 4, color: "var(--primary)" },
];

function normalize(score: number): number {
  return ((score - MIN_SCORE) / (MAX_SCORE - MIN_SCORE)) * 100;
}

function LessonLine({
  label,
  chunks,
  avgScore,
  color,
  delay,
}: {
  label: string;
  chunks: ChunkScore[];
  avgScore: number;
  color: string;
  delay: number;
}) {
  if (chunks.length === 0) return null;

  const svgWidth = 100;
  const svgHeight = 100;
  const padX = 0;
  const padY = 4;
  const usableW = svgWidth - padX * 2;
  const usableH = svgHeight - padY * 2;

  const points = chunks.map((c, i) => {
    const x = padX + (i / Math.max(chunks.length - 1, 1)) * usableW;
    const y = padY + usableH - ((c.score - MIN_SCORE) / (MAX_SCORE - MIN_SCORE)) * usableH;
    return { x, y, chunk: c };
  });

  const avgY = padY + usableH - ((avgScore - MIN_SCORE) / (MAX_SCORE - MIN_SCORE)) * usableH;

  // Build SVG path
  const pathD = points
    .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");

  // Area under the line
  const areaD = `${pathD} L ${points[points.length - 1].x.toFixed(1)} ${svgHeight} L ${points[0].x.toFixed(1)} ${svgHeight} Z`;

  return (
    <div className="flex-1 min-w-0">
      <p className="text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant mb-2">
        {label}
      </p>
      <svg
        viewBox={`0 0 ${svgWidth} ${svgHeight}`}
        preserveAspectRatio="none"
        className="w-full h-32"
        style={{ overflow: "visible" }}
      >
        {/* CEFR reference lines */}
        {CEFR_LINES.map((line) => {
          const y = padY + usableH - ((line.value - MIN_SCORE) / (MAX_SCORE - MIN_SCORE)) * usableH;
          return (
            <g key={line.label}>
              <line
                x1={0}
                y1={y}
                x2={svgWidth}
                y2={y}
                stroke="var(--surface-variant)"
                strokeWidth={0.3}
              />
              <text
                x={-1}
                y={y + 1}
                fontSize={3.5}
                fill="var(--on-surface-variant)"
                opacity={0.4}
                textAnchor="end"
                dominantBaseline="central"
              >
                {line.label}
              </text>
            </g>
          );
        })}

        {/* Average line */}
        <line
          x1={0}
          y1={avgY}
          x2={svgWidth}
          y2={avgY}
          stroke={color}
          strokeWidth={0.4}
          strokeDasharray="2 1.5"
          opacity={0.5}
        />

        {/* Area fill */}
        <motion.path
          d={areaD}
          fill={color}
          opacity={0.08}
          initial={{ opacity: 0 }}
          animate={{ opacity: 0.08 }}
          transition={{ delay, duration: 0.6 }}
        />

        {/* Line */}
        <motion.path
          d={pathD}
          fill="none"
          stroke={color}
          strokeWidth={1}
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0 }}
          animate={{ pathLength: 1 }}
          transition={{ delay, duration: 0.8, ease: "easeOut" }}
        />

        {/* Dots */}
        {points.map((p, i) => (
          <motion.circle
            key={i}
            cx={p.x}
            cy={p.y}
            r={1.5}
            fill={color}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: delay + 0.3 + i * 0.04, duration: 0.3 }}
          >
            <title>
              P{p.chunk.paragraphId}: {p.chunk.score.toFixed(1)} ({p.chunk.cefrLabel})
              {p.chunk.label && p.chunk.label !== "None" ? ` — ${p.chunk.label}` : ""}
            </title>
          </motion.circle>
        ))}
      </svg>

      {/* Avg label */}
      <div className="flex items-center gap-2 mt-1">
        <span className="text-[10px] text-on-surface-variant opacity-50">avg</span>
        <span className="text-xs font-semibold text-on-surface tabular-nums">
          {avgScore.toFixed(1)}
        </span>
        <span className="text-[10px] text-on-surface-variant opacity-50">(dashed)</span>
      </div>
    </div>
  );
}

export default function ScoreEvolutionChart({
  lessonA,
  lessonB,
  chunksA,
  chunksB,
  avgScoreA,
  avgScoreB,
}: ScoreEvolutionChartProps) {
  return (
    <div className="rounded-2xl bg-surface-lowest p-8">
      <h3 className="font-[family-name:var(--font-display)] text-lg font-bold text-on-surface tracking-tight mb-1">
        Score Evolution
      </h3>
      <p className="text-xs text-on-surface-variant opacity-60 mb-6">
        Vocabulary level across conversation paragraphs — hover dots for details
      </p>
      <div className="flex gap-8">
        <LessonLine
          label={lessonA.replace("lesson-", "Lesson ")}
          chunks={chunksA}
          avgScore={avgScoreA}
          color="var(--primary)"
          delay={0}
        />
        <LessonLine
          label={lessonB.replace("lesson-", "Lesson ")}
          chunks={chunksB}
          avgScore={avgScoreB}
          color="var(--secondary-fixed, #1A9E8F)"
          delay={0.3}
        />
      </div>
    </div>
  );
}
