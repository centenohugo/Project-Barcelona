"use client";

import { motion } from "framer-motion";
import MetricBar from "./MetricBar";
import type { RealConversationChunk, CefrLevel } from "@/lib/types";
import {
  cefrBgColors,
  cefrTextColors,
  cefrBarGradients,
  CEFR_LEVELS,
} from "@/lib/cefr-utils";

interface ChunkCardProps {
  chunk: RealConversationChunk;
  index: number;
}

export default function ChunkCard({ chunk, index }: ChunkCardProps) {
  return (
    <motion.div
      className="w-full rounded-2xl bg-surface-lowest p-8 flex gap-8"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: index * 0.12,
        duration: 0.5,
        ease: [0.34, 1.56, 0.64, 1],
      }}
    >
      {/* Left — conversation text */}
      <div className="flex-1 min-w-0">
        <span className="inline-block text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant font-[family-name:var(--font-body)] mb-3">
          {chunk.topic}
        </span>
        <p className="text-base leading-7 font-[family-name:var(--font-body)] text-on-surface">
          {chunk.words.map((word, i) => {
            const level = word.cefrLevel;
            const highlighted = word.isAboveLevel && level;

            if (highlighted) {
              return (
                <span
                  key={i}
                  className="inline-block rounded-md px-1 py-0.5 mx-0.5 text-sm font-medium relative group/word cursor-default"
                  style={{
                    backgroundColor: cefrBgColors[level as CefrLevel],
                    color: cefrTextColors[level as CefrLevel],
                  }}
                >
                  {word.isNew && (
                    <span
                      className="absolute -top-0.5 -left-0.5 w-[6px] h-[6px] rounded-full"
                      style={{ background: "var(--secondary)" }}
                    />
                  )}
                  {word.text}
                  {/* Tooltip */}
                  <span
                    className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] font-bold text-white px-1.5 py-0.5 rounded opacity-0 group-hover/word:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10"
                    style={{
                      background: cefrTextColors[level as CefrLevel],
                    }}
                  >
                    {level}
                    {word.isNew ? " · NEW" : ""}
                  </span>
                </span>
              );
            }

            if (word.isNew) {
              return (
                <span
                  key={i}
                  className="inline-block relative mx-0.5 cursor-default group/word"
                  style={{
                    borderBottom: "2px solid var(--secondary)",
                    paddingBottom: "1px",
                  }}
                >
                  <span
                    className="absolute -top-0.5 -left-0.5 w-[6px] h-[6px] rounded-full"
                    style={{ background: "var(--secondary)" }}
                  />
                  {word.text}
                  <span
                    className="absolute -top-7 left-1/2 -translate-x-1/2 text-[10px] font-bold text-white px-1.5 py-0.5 rounded opacity-0 group-hover/word:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10"
                    style={{ background: "var(--secondary-fixed)" }}
                  >
                    {word.cefrLevel ?? "?"} · NEW
                  </span>
                </span>
              );
            }

            return <span key={i}>{word.text} </span>;
          })}
        </p>

        {/* Summary chips */}
        <div className="flex gap-3 mt-4">
          {chunk.stats.aboveLevelCount > 0 && (
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: "rgba(255, 107, 157, 0.10)",
                color: "var(--primary)",
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path
                  d="M6 2L7.5 5H10.5L8 7L9 10L6 8L3 10L4 7L1.5 5H4.5L6 2Z"
                  fill="currentColor"
                />
              </svg>
              {chunk.stats.aboveLevelCount} above level
            </span>
          )}
          {chunk.stats.newWordsCount > 0 && (
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
              style={{
                background: "rgba(64, 224, 208, 0.12)",
                color: "var(--secondary-fixed)",
              }}
            >
              <span
                className="w-2 h-2 rounded-full"
                style={{ background: "var(--secondary)" }}
              />
              {chunk.stats.newWordsCount} new words
            </span>
          )}
        </div>
      </div>

      {/* Right — CEFR distribution bars */}
      <div className="w-[35%] shrink-0 flex flex-col gap-3 justify-center">
        <span className="text-[10px] font-medium uppercase tracking-[0.08em] text-on-surface-variant font-[family-name:var(--font-body)] mb-1">
          CEFR Distribution
        </span>
        {CEFR_LEVELS.map((level, i) => (
          <MetricBar
            key={level}
            label={level}
            value={Math.round(chunk.cefrDistribution[level] * 10) / 10}
            delay={300 + index * 100 + i * 60}
            color={cefrBarGradients[level]}
          />
        ))}
      </div>
    </motion.div>
  );
}
