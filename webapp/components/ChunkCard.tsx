"use client";

import { motion } from "framer-motion";
import MetricBar from "./MetricBar";
import type { ConversationChunk, CefrLevel } from "@/lib/mock-data";

const cefrColors: Record<CefrLevel, string> = {
  A1: "rgba(64, 224, 208, 0.15)",
  A2: "rgba(64, 224, 208, 0.25)",
  B1: "rgba(255, 107, 157, 0.15)",
  B2: "rgba(255, 107, 157, 0.25)",
  C1: "rgba(18, 17, 17, 0.10)",
  C2: "rgba(18, 17, 17, 0.18)",
};

const cefrTextColors: Record<CefrLevel, string> = {
  A1: "var(--secondary-fixed)",
  A2: "var(--secondary-fixed)",
  B1: "var(--primary)",
  B2: "var(--primary)",
  C1: "var(--tertiary)",
  C2: "var(--tertiary)",
};

interface ChunkCardProps {
  chunk: ConversationChunk;
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
          {chunk.words.map((word, i) => (
            word.highlight ? (
              <span
                key={i}
                className="inline-block rounded-md px-1 py-0.5 mx-0.5 text-sm font-medium relative group/word cursor-default"
                style={{
                  backgroundColor: cefrColors[word.highlight],
                  color: cefrTextColors[word.highlight],
                }}
              >
                {word.text}
                <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-[10px] font-bold text-on-primary px-1.5 py-0.5 rounded opacity-0 group-hover/word:opacity-100 transition-opacity pointer-events-none whitespace-nowrap"
                  style={{ background: "var(--primary)" }}
                >
                  {word.highlight}
                </span>
              </span>
            ) : (
              <span key={i}>{word.text} </span>
            )
          ))}
        </p>
      </div>

      {/* Right — metric bars */}
      <div className="w-[35%] shrink-0 flex flex-col gap-4 justify-center">
        {chunk.metrics.map((m, i) => (
          <MetricBar
            key={m.label}
            label={m.label}
            value={m.value}
            delay={300 + index * 100 + i * 80}
          />
        ))}
      </div>
    </motion.div>
  );
}
