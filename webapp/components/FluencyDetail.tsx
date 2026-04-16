"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MetricBar from "./MetricBar";
import type {
  FluencyLessonData,
  FluencyChunk,
  FluencySentenceRecord,
  FluencyWordData,
  FluencyDuplicate,
} from "@/lib/types";

// ── Colour helpers ─────────────────────────────────────────────────────────────

function scoreColor(score: number | null): { fg: string; bg: string } {
  if (score === null) return { fg: "#9CA3AF", bg: "#F3F4F6" };
  if (score >= 80) return { fg: "#059669", bg: "#D1FAE5" };
  if (score >= 60) return { fg: "#D97706", bg: "#FEF3C7" };
  return { fg: "#DC2626", bg: "#FEE2E2" };
}

function getSpeedStyle(
  speed: number | null,
  thresholds: { p25Ms: number; p75Ms: number; p90Ms: number }
) {
  if (speed === null) return { bg: "#F9FAFB", border: "#E5E7EB", color: "#9CA3AF" };
  const ms = speed * 1000;
  if (ms < thresholds.p25Ms) return { bg: "#D1FAE5", border: "#34D399", color: "#064E3B" };
  if (ms <= thresholds.p75Ms) return { bg: "#F3F4F6", border: "#D1D5DB", color: "#374151" };
  if (ms <= thresholds.p90Ms) return { bg: "#FEF3C7", border: "#FCD34D", color: "#78350F" };
  return { bg: "#FEE2E2", border: "#FCA5A5", color: "#991B1B" };
}

function gapColor(g: number) {
  if (g < 0.08) return "#34D399";
  if (g < 0.25) return "#FCD34D";
  return "#F87171";
}

function buildDupMap(
  dups: FluencyDuplicate[]
): Map<number, { isFirst: boolean; label: string; matchType: string }> {
  const dm = new Map<number, { isFirst: boolean; label: string; matchType: string }>();
  for (const d of dups) {
    const label = d.phrase.join(" ");
    for (let occ = 0; occ < d.startIndices.length; occ++) {
      const start = d.startIndices[occ];
      for (let p = 0; p < d.phrase.length; p++) {
        dm.set(start + p, { isFirst: occ === 0, label, matchType: d.matchType });
      }
    }
  }
  return dm;
}

// ── Inline sentence text (fillers + duplicates highlighted) ───────────────────

function SentenceInline({ sentence }: { sentence: FluencySentenceRecord }) {
  const dupMap = buildDupMap(sentence.duplicates);
  if (sentence.fillers.count === 0 && sentence.duplicates.length === 0) {
    return (
      <span style={{ fontFamily: "Georgia, serif", fontSize: "13px" }}>
        {sentence.text}
      </span>
    );
  }
  return (
    <span style={{ fontFamily: "Georgia, serif", fontSize: "13px" }}>
      {sentence.words.map((word: FluencyWordData, i: number) => {
        const dup = dupMap.get(i);
        if (word.isFiller) {
          return (
            <span
              key={i}
              className="rounded italic"
              style={{ padding: "1px 5px", background: "#FFF7ED", border: "1px solid #F97316", color: "#9A3412" }}
              title={word.fillerType ?? "filler"}
            >
              {word.punctuatedWord}
            </span>
          );
        }
        if (dup) {
          return dup.isFirst ? (
            <span
              key={i}
              className="rounded"
              style={{ padding: "1px 5px", background: "#FEF2F2", color: "#DC2626", borderBottom: "2px dotted #DC2626" }}
              title={`first: "${dup.label}"`}
            >
              {word.punctuatedWord}
            </span>
          ) : (
            <span
              key={i}
              className="rounded line-through"
              style={{ padding: "1px 5px", background: "#FEE2E2", color: "#991B1B" }}
              title={`repeat: "${dup.label}"`}
            >
              {word.punctuatedWord}
            </span>
          );
        }
        return <span key={i}>{word.punctuatedWord} </span>;
      })}
    </span>
  );
}

// ── Speed/gaps temporal detail ─────────────────────────────────────────────────

function SpeedGapsView({
  sentence,
  thresholds,
}: {
  sentence: FluencySentenceRecord;
  thresholds: { p25Ms: number; p75Ms: number; p90Ms: number };
}) {
  const elements = sentence.words.flatMap((word: FluencyWordData, i: number) => {
    const sStyle = word.isFiller
      ? { bg: "#FFF7ED", border: "#F97316", color: "#9A3412" }
      : getSpeedStyle(word.speed, thresholds);

    const chip = (
      <div key={"w-" + i} className="inline-flex flex-col items-center" style={{ margin: "0 2px" }}>
        <span
          className="rounded-md px-2 py-1 whitespace-nowrap"
          style={{
            background: sStyle.bg,
            border: "1px solid " + sStyle.border,
            color: sStyle.color,
            fontStyle: word.isFiller ? "italic" : "normal",
            fontFamily: "Georgia, serif",
            fontSize: "12px",
          }}
        >
          {word.punctuatedWord}
        </span>
        <span style={{ fontSize: "8px", color: word.isFiller ? "#F97316" : "#9CA3AF", marginTop: "1px" }}>
          {word.isFiller
            ? word.fillerType ?? "filler"
            : word.speed != null
              ? Math.round(word.speed * 1000) + "ms"
              : "—"}
        </span>
      </div>
    );

    if (i < sentence.words.length - 1) {
      const next = sentence.words[i + 1];
      const gap = next.start - word.end;
      const gCol = gap >= 0 ? gapColor(gap) : "#D1D5DB";
      const gLabel = gap >= 0 ? Math.round(gap * 1000) + "ms" : "—";
      return [
        chip,
        <div
          key={"g-" + i}
          className="inline-flex flex-col items-center"
          style={{ width: "22px", margin: "0 1px", verticalAlign: "middle" }}
        >
          <div style={{ width: "2px", height: "18px", background: gCol, margin: "0 auto" }} />
          <span style={{ fontSize: "7px", color: gCol, marginTop: "1px", display: "block", textAlign: "center" }}>
            {gLabel}
          </span>
        </div>,
      ];
    }
    return [chip];
  });

  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", lineHeight: "3.8", padding: "4px 0" }}>
      {elements}
    </div>
  );
}

// ── Single sentence row ────────────────────────────────────────────────────────

function SentenceRow({
  sentence,
  thresholds,
}: {
  sentence: FluencySentenceRecord;
  thresholds: { p25Ms: number; p75Ms: number; p90Ms: number };
}) {
  const [open, setOpen] = useState(false);
  const score = sentence.fluency.score;
  const { fg, bg } = scoreColor(score);
  const nFillers = sentence.fillers.count;
  const nRepeats = sentence.duplicates.reduce((s, d) => s + d.occurrences - 1, 0);

  return (
    <div className="mb-3">
      <div className="flex items-start gap-2">
        <span
          className="shrink-0 text-[9px] text-on-surface-variant font-[family-name:var(--font-body)] mt-1"
          style={{ width: "22px" }}
        >
          s{sentence.sentenceId}
        </span>
        <div className="flex-1 min-w-0">
          <div style={{ lineHeight: 2 }}>
            <SentenceInline sentence={sentence} />
          </div>
          {/* Badges row */}
          <div className="flex gap-1 mt-1 flex-wrap">
            {score !== null && (
              <span
                className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full"
                style={{ background: bg, color: fg }}
              >
                {score}
              </span>
            )}
            {nFillers > 0 && (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded-full"
                style={{ background: "#FFF7ED", color: "#9A3412", border: "1px solid #F97316" }}
              >
                {nFillers} filler{nFillers > 1 ? "s" : ""}
              </span>
            )}
            {nRepeats > 0 && (
              <span
                className="text-[9px] px-1.5 py-0.5 rounded-full"
                style={{ background: "#FEE2E2", color: "#991B1B" }}
              >
                {nRepeats} repeat{nRepeats > 1 ? "s" : ""}
              </span>
            )}
            <button
              onClick={() => setOpen((v) => !v)}
              className="text-[9px] px-1.5 py-0.5 rounded-full cursor-pointer transition-colors"
              style={{
                background: open ? "var(--primary)" : "rgba(0,0,0,0.06)",
                color: open ? "var(--on-primary)" : "var(--on-surface-variant)",
              }}
            >
              {open ? "▲ timing" : "▼ timing"}
            </button>
          </div>
        </div>
      </div>

      {/* Expandable timing */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ overflow: "hidden" }}
          >
            <div
              className="mt-2 rounded-xl p-3"
              style={{ background: "var(--surface)", border: "1px solid var(--surface-variant)" }}
            >
              <div className="text-[9px] font-semibold uppercase tracking-widest text-on-surface-variant mb-2 font-[family-name:var(--font-body)]">
                Speed &amp; Inter-word Gaps
              </div>
              <SpeedGapsView sentence={sentence} thresholds={thresholds} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Per-chunk card ─────────────────────────────────────────────────────────────

function FluencyChunkCard({
  chunk,
  thresholds,
  index,
}: {
  chunk: FluencyChunk;
  thresholds: { p25Ms: number; p75Ms: number; p90Ms: number };
  index: number;
}) {
  const score = chunk.fluencyScore;
  const { fg, bg } = scoreColor(score);
  const ca = chunk.compAvgs;

  return (
    <motion.div
      className="w-full rounded-2xl bg-surface-lowest p-8 flex gap-8"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.45, ease: [0.34, 1.56, 0.64, 1] }}
    >
      {/* Left — sentence rows */}
      <div className="flex-1 min-w-0">
        <span className="inline-block text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant font-[family-name:var(--font-body)] mb-4">
          {chunk.label || `Chunk ${chunk.paragraphId}`}
        </span>

        {chunk.sentences.length === 0 ? (
          <p className="text-sm text-on-surface-variant font-[family-name:var(--font-body)] italic">
            No sentences mapped to this chunk.
          </p>
        ) : (
          chunk.sentences.map((sentence) => (
            <SentenceRow
              key={sentence.sentenceId}
              sentence={sentence}
              thresholds={thresholds}
            />
          ))
        )}

        {/* Summary chips */}
        <div className="flex gap-2 mt-2 flex-wrap">
          <span
            className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
            style={{ background: "rgba(0,0,0,0.05)", color: "var(--on-surface-variant)" }}
          >
            {chunk.sentences.length} sentences · {chunk.wordCount}w
          </span>
          {chunk.fillerCount > 0 && (
            <span
              className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium"
              style={{ background: "#FFF7ED", color: "#9A3412", border: "1px solid #F97316" }}
            >
              {chunk.fillerCount} fillers
            </span>
          )}
        </div>
      </div>

      {/* Right — component score bars */}
      <div className="w-[33%] shrink-0 flex flex-col gap-3 justify-start pt-1">
        {score !== null && (
          <div className="flex items-center gap-2 mb-1">
            <div
              className="rounded-lg px-3 py-2 text-center"
              style={{ background: bg, border: "2px solid " + fg }}
            >
              <div
                className="font-extrabold font-[family-name:var(--font-display)]"
                style={{ fontSize: "22px", color: fg, lineHeight: 1 }}
              >
                {score}
              </div>
              <div style={{ fontSize: "8px", color: fg, marginTop: "1px" }}>/ 100</div>
            </div>
            <span className="text-[10px] font-semibold text-on-surface-variant font-[family-name:var(--font-body)]">
              Fluency
            </span>
          </div>
        )}

        <span className="text-[10px] font-medium uppercase tracking-[0.08em] text-on-surface-variant font-[family-name:var(--font-body)]">
          Components
        </span>
        {ca.speed !== null && (
          <MetricBar label="Speed ×35%" value={Math.round(ca.speed)} delay={200 + index * 80} color="#34D399" />
        )}
        {ca.gaps !== null && (
          <MetricBar label="Thinking ×35%" value={Math.round(ca.gaps)} delay={260 + index * 80} color="#60A5FA" />
        )}
        {ca.fillers !== null && (
          <MetricBar label="Fillers ×15%" value={Math.round(ca.fillers)} delay={320 + index * 80} color="#F97316" />
        )}
        {ca.dups !== null && (
          <MetricBar label="Duplicates ×15%" value={Math.round(ca.dups)} delay={380 + index * 80} color="#A78BFA" />
        )}
      </div>
    </motion.div>
  );
}

// ── Main FluencyDetail ─────────────────────────────────────────────────────────

export default function FluencyDetail({ data }: { data: FluencyLessonData }) {
  const { speedThresholds: thr, chunks } = data;

  return (
    <motion.div
      key="fluency"
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
          Fluency {data.avgFluency}
        </span>
        <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
          {data.totalSentences} sentences
        </span>
        <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
          {data.totalWords} words
        </span>
        {data.fillerCount > 0 && (
          <span
            className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium"
            style={{ background: "#FFF7ED", color: "#9A3412", border: "1px solid #F97316" }}
          >
            {data.fillerCount} fillers ({data.fillerRate}%)
          </span>
        )}
        <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
          Avg gap {data.avgGapMs}ms
        </span>
        <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
          Conf {data.avgAccuracy}%
        </span>
      </div>

      {/* Per-chunk cards */}
      {chunks && chunks.length > 0 ? (
        chunks.map((chunk, i) => (
          <FluencyChunkCard
            key={chunk.paragraphId}
            chunk={chunk}
            thresholds={thr}
            index={i}
          />
        ))
      ) : (
        <div className="rounded-2xl bg-surface-lowest p-8 text-center">
          <p className="text-on-surface-variant font-[family-name:var(--font-body)] text-sm">
            No fluency data available.
          </p>
        </div>
      )}
    </motion.div>
  );
}
