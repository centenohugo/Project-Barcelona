"use client";

import { useState } from "react";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import type { GrammarParagraph, GrammarError } from "@/lib/types";

// ── CEFR level colours (for richness mode) ─────────────────────────────────────

const CEFR_BG: Record<string, string> = {
  A1: "#F3F4F6", A2: "#DBEAFE",
  B1: "#D1FAE5", B2: "#FEF3C7",
  C1: "#FEE2E2", C2: "#EDE9FE",
};
const CEFR_TEXT: Record<string, string> = {
  A1: "#4B5563", A2: "#1D4ED8",
  B1: "#065F46", B2: "#92400E",
  C1: "#991B1B", C2: "#5B21B6",
};
const CEFR_DOT: Record<string, string> = {
  A1: "#9CA3AF", A2: "#3B82F6",
  B1: "#10B981", B2: "#F59E0B",
  C1: "#EF4444", C2: "#8B5CF6",
};
const CEFR_ORDER = ["A1", "A2", "B1", "B2", "C1", "C2"];

// ── Dimension colours (for error mode) ────────────────────────────────────────

const DIM_BG: Record<string, string> = {
  A: "#DBEAFE", B: "#FEF3C7", C: "#D1FAE5", D: "#EDE9FE",
};
const DIM_TEXT: Record<string, string> = {
  A: "#1D4ED8", B: "#92400E", C: "#065F46", D: "#5B21B6",
};
const DIM_LABEL: Record<string, string> = {
  A: "Sentence Architecture", B: "Tense & Aspect", C: "Nominal Precision", D: "Modal & Function",
};

// Score constants (match build_grammar_processed.py)
const LEVEL_WEIGHT = 0.60;
const VARIETY_WEIGHT = 0.40;
const VARIETY_CEILING = 15;

// ── Processed span type ────────────────────────────────────────────────────────

interface ProcessedSpan {
  key: string;
  start: number;
  end: number;
  contextStart: number;
  contextEnd: number;
  level: string;   // CEFR level (richness mode)
  dim: string;     // dimension code (error mode)
  tooltip: string;
  weight?: number; // error weight (error mode)
}

// ── Sentence text renderer ─────────────────────────────────────────────────────

function renderSentenceText(
  text: string,
  spans: ProcessedSpan[],
  activeKey: string | null,
  onHover: (key: string | null) => void,
  isErrorMode: boolean
): ReactNode {
  if (spans.length === 0) return <>{text}</>;

  // Sort + resolve overlapping spans (keep first)
  const sorted = [...spans].sort((a, b) => a.start - b.start);
  const resolved: ProcessedSpan[] = [];
  let cur = 0;
  for (const s of sorted) {
    if (s.start >= cur) { resolved.push(s); cur = s.end; }
  }

  // Character-level paint pass
  type PaintType = "plain" | "context" | "match";
  const paintType = new Array(text.length).fill("plain") as PaintType[];
  const paintSpan = new Array(text.length).fill(null) as (ProcessedSpan | null)[];

  // Mark context of active span
  const activeSpan = activeKey ? resolved.find((s) => s.key === activeKey) : null;
  if (activeSpan) {
    const cs = Math.max(0, activeSpan.contextStart);
    const ce = Math.min(text.length, activeSpan.contextEnd);
    for (let i = cs; i < ce; i++) paintType[i] = "context";
  }

  // Mark matches (override context)
  for (const s of resolved) {
    const ms = Math.max(0, s.start);
    const me = Math.min(text.length, s.end);
    for (let i = ms; i < me; i++) {
      paintType[i] = "match";
      paintSpan[i] = s;
    }
  }

  // Collapse into runs
  interface Run { type: PaintType; text: string; span: ProcessedSpan | null }
  const runs: Run[] = [];
  let i = 0;
  while (i < text.length) {
    const t = paintType[i];
    const s = paintSpan[i];
    let j = i + 1;
    while (j < text.length && paintType[j] === t && paintSpan[j] === s) j++;
    runs.push({ type: t, text: text.slice(i, j), span: s });
    i = j;
  }

  return (
    <>
      {runs.map((run, idx) => {
        if (run.type === "plain") return <span key={idx}>{run.text}</span>;

        if (run.type === "context") {
          return (
            <span
              key={idx}
              style={{
                textDecoration: "underline",
                textDecorationColor: "rgba(100, 120, 200, 0.28)",
                textDecorationStyle: "dotted",
                textUnderlineOffset: "3px",
              }}
            >
              {run.text}
            </span>
          );
        }

        // "match" run
        const sp = run.span!;
        const isActive = sp.key === activeKey;
        const opacity =
          sp.weight === undefined ? 1 : sp.weight === 1 ? 0.55 : sp.weight === 2 ? 0.78 : 1;

        const bg = isErrorMode ? (DIM_BG[sp.dim] ?? "#F3F4F6") : (CEFR_BG[sp.level] ?? "#F3F4F6");
        const fg = isErrorMode ? (DIM_TEXT[sp.dim] ?? "#374151") : (CEFR_TEXT[sp.level] ?? "#374151");

        return (
          <span
            key={idx}
            className="relative inline cursor-default"
            onMouseEnter={() => onHover(sp.key)}
            onMouseLeave={() => onHover(null)}
          >
            <mark
              style={{
                background: bg,
                color: fg,
                opacity,
                borderRadius: "4px",
                padding: "1px 4px",
                fontWeight: 500,
              }}
            >
              {run.text}
            </mark>

            {/* Tooltip — only on active span */}
            {isActive && (
              <span
                style={{
                  position: "absolute",
                  bottom: "calc(100% + 10px)",
                  left: "50%",
                  transform: "translateX(-50%)",
                  background: fg,
                  color: "#fff",
                  fontSize: "12.5px",
                  fontWeight: 400,
                  lineHeight: 1.5,
                  padding: "10px 14px",
                  borderRadius: "10px",
                  zIndex: 50,
                  pointerEvents: "none",
                  maxWidth: "340px",
                  whiteSpace: "normal",
                  wordBreak: "break-word",
                  boxShadow: "0 4px 16px rgba(0,0,0,0.20)",
                  minWidth: "160px",
                }}
              >
                {sp.tooltip}
              </span>
            )}
          </span>
        );
      })}
    </>
  );
}

// ── Inline score bar ────────────────────────────────────────────────────────────

function MiniBar({ value, max, color }: { value: number; max: number; color: string }) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div className="flex-1 h-2 rounded-full overflow-hidden" style={{ background: "rgba(0,0,0,0.08)" }}>
      <div
        className="h-full rounded-full transition-all"
        style={{ width: `${pct}%`, background: color, transition: "width 600ms cubic-bezier(0.34,1.56,0.64,1)" }}
      />
    </div>
  );
}

// ── Right panel — richness score breakdown ─────────────────────────────────────

function RichnessPanel({ r, e }: { r: GrammarParagraph["richness"]; e: GrammarParagraph["errorStats"] }) {
  const levPts = Math.round(r.levelScore * LEVEL_WEIGHT * 100);
  const varPts = Math.round(r.varietyScore * VARIETY_WEIGHT * 100);
  const maxLev = Math.round(LEVEL_WEIGHT * 100);
  const maxVar = Math.round(VARIETY_WEIGHT * 100);

  // CEFR levels present in this paragraph
  const presentLevels = CEFR_ORDER.filter((lvl) => (r.levelDistribution[lvl] ?? 0) > 0);
  const totalStructures = Object.values(r.levelDistribution).reduce((a, b) => a + b, 0);

  return (
    <div className="flex flex-col gap-4">
      {/* Score pill */}
      <div className="flex items-center gap-2">
        <div
          className="rounded-lg px-3 py-2 text-center shrink-0"
          style={{ background: r.color + "20", border: `2px solid ${r.color}` }}
        >
          <div
            className="font-extrabold font-[family-name:var(--font-display)]"
            style={{ fontSize: "22px", color: r.color, lineHeight: 1 }}
          >
            {r.score}
          </div>
          <div style={{ fontSize: "8px", color: r.color, marginTop: "1px" }}>/ 100</div>
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-semibold text-on-surface font-[family-name:var(--font-body)]" style={{ color: r.color }}>
            {r.label}
          </span>
          <span className="text-[10px] text-on-surface-variant font-[family-name:var(--font-body)]">
            {r.nAssigned} structures · {r.density.toFixed(1)}/sent
          </span>
        </div>
      </div>

      {/* Score breakdown */}
      <div className="flex flex-col gap-2.5">
        <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-on-surface-variant font-[family-name:var(--font-body)]">
          Score breakdown
        </span>

        {/* Level row */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-on-surface font-[family-name:var(--font-body)]">
              Level <span className="text-[10px] text-on-surface-variant">(60%)</span>
            </span>
            <span className="text-[11px] font-semibold font-[family-name:var(--font-display)]" style={{ color: CEFR_TEXT[r.avgLevelStr] ?? "#374151" }}>
              avg {r.avgLevelStr} → {levPts}/{maxLev} pts
            </span>
          </div>
          <div className="flex items-center gap-2">
            <MiniBar value={levPts} max={maxLev} color={CEFR_DOT[r.avgLevelStr] ?? "#6B7280"} />
          </div>
        </div>

        {/* Variety row */}
        <div className="flex flex-col gap-1">
          <div className="flex items-center justify-between">
            <span className="text-[11px] font-medium text-on-surface font-[family-name:var(--font-body)]">
              Variety <span className="text-[10px] text-on-surface-variant">(40%)</span>
            </span>
            <span className="text-[11px] font-semibold font-[family-name:var(--font-display)]" style={{ color: "#374151" }}>
              {r.distinctCategories.length}/{VARIETY_CEILING} cats → {varPts}/{maxVar} pts
            </span>
          </div>
          <div className="flex items-center gap-2">
            <MiniBar value={varPts} max={maxVar} color="#8B5CF6" />
          </div>
        </div>

        {/* Error row */}
        {e.count > 0 && (
          <div className="flex items-center justify-between pt-1 border-t" style={{ borderColor: "rgba(0,0,0,0.06)" }}>
            <span className="text-[11px] font-medium text-on-surface font-[family-name:var(--font-body)]">Errors</span>
            <span className="text-[11px] font-semibold" style={{ color: e.qualityColor }}>
              {e.count} errors · −{e.weightedSum.toFixed(1)} pts · {e.qualityLevel}
            </span>
          </div>
        )}
      </div>

      {/* CEFR legend */}
      {presentLevels.length > 0 && (
        <div className="flex flex-col gap-1.5 pt-1 border-t" style={{ borderColor: "rgba(0,0,0,0.06)" }}>
          <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-on-surface-variant font-[family-name:var(--font-body)]">
            Colour legend
          </span>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {presentLevels.map((lvl) => {
              const count = r.levelDistribution[lvl] ?? 0;
              const pct = totalStructures > 0 ? Math.round((count / totalStructures) * 100) : 0;
              return (
                <div key={lvl} className="flex items-center gap-1">
                  <span
                    className="w-2.5 h-2.5 rounded-full shrink-0"
                    style={{ background: CEFR_DOT[lvl] }}
                  />
                  <span
                    className="text-[11px] font-semibold font-[family-name:var(--font-display)]"
                    style={{ color: CEFR_TEXT[lvl] }}
                  >
                    {lvl}
                  </span>
                  <span className="text-[10px] text-on-surface-variant font-[family-name:var(--font-body)]">
                    {pct}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Right panel — error quality ────────────────────────────────────────────────

function ErrorPanel({ e, errors }: { e: GrammarParagraph["errorStats"]; errors: GrammarError[] }) {
  // Group grammar categories by dimension
  const catsByDim: Record<string, Record<string, number>> = {};
  for (const err of errors) {
    const dim = err.dimensionCode;
    if (!catsByDim[dim]) catsByDim[dim] = {};
    catsByDim[dim][err.grammarCategory] = (catsByDim[dim][err.grammarCategory] ?? 0) + 1;
  }

  const dimEntries = Object.entries(e.dimensionCounts)
    .filter(([, c]) => c > 0)
    .sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="flex flex-col gap-3">
      {/* Quality pill */}
      <div className="flex items-center gap-2">
        <div
          className="rounded-lg px-3 py-2 text-center shrink-0"
          style={{ background: e.qualityColor + "20", border: `2px solid ${e.qualityColor}` }}
        >
          <div
            className="font-extrabold font-[family-name:var(--font-display)]"
            style={{ fontSize: "22px", color: e.qualityColor, lineHeight: 1 }}
          >
            {e.qualityScore}
          </div>
          <div style={{ fontSize: "8px", color: e.qualityColor, marginTop: "1px" }}>/ 100</div>
        </div>
        <div className="flex flex-col">
          <span className="text-xs font-semibold font-[family-name:var(--font-body)]" style={{ color: e.qualityColor }}>
            {e.qualityLevel}
          </span>
          <span className="text-[10px] text-on-surface-variant font-[family-name:var(--font-body)]">
            {e.count} errors · weight {e.weightedSum.toFixed(1)}
          </span>
        </div>
      </div>

      {/* Per-dimension category breakdown */}
      {dimEntries.length > 0 && (
        <div className="flex flex-col gap-2.5">
          <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-on-surface-variant font-[family-name:var(--font-body)]">
            By dimension
          </span>
          {dimEntries.map(([dim, count]) => {
            const cats = Object.entries(catsByDim[dim] ?? {})
              .sort(([, a], [, b]) => b - a)
              .slice(0, 3)
              .map(([cat]) => cat);
            const totalCats = Object.keys(catsByDim[dim] ?? {}).length;
            return (
              <div key={dim} className="flex flex-col gap-0.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full shrink-0" style={{ background: DIM_TEXT[dim] }} />
                    <span className="text-[10px] font-semibold font-[family-name:var(--font-body)]" style={{ color: DIM_TEXT[dim] }}>
                      {DIM_LABEL[dim] ?? dim}
                    </span>
                  </div>
                  <span className="text-[10px] font-semibold font-[family-name:var(--font-display)]" style={{ color: DIM_TEXT[dim] }}>
                    {count}
                  </span>
                </div>
                {cats.length > 0 && (
                  <div
                    className="pl-3.5 font-[family-name:var(--font-body)]"
                    style={{ fontSize: "10px", color: "var(--on-surface-variant)", lineHeight: 1.5 }}
                  >
                    {cats.join(", ")}{totalCats > 3 ? ", …" : ""}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

interface GrammarChunkCardProps {
  paragraph: GrammarParagraph;
  showErrors: boolean;
  index: number;
}

export default function GrammarChunkCard({ paragraph, showErrors, index }: GrammarChunkCardProps) {
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);

  const r = paragraph.richness;
  const e = paragraph.errorStats;

  return (
    <motion.div
      className="w-full rounded-2xl bg-surface-lowest p-8 flex gap-8"
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.45, ease: [0.34, 1.56, 0.64, 1] }}
    >
      {/* Left — sentences as flowing text */}
      <div className="flex-1 min-w-0">
        <span className="inline-block text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant font-[family-name:var(--font-body)] mb-3">
          {paragraph.label || `Paragraph ${paragraph.paragraphId}`}
        </span>

        {/* All sentences inline as one flowing block */}
        <div
          className="font-[family-name:var(--font-body)] text-on-surface"
          style={{ fontSize: "13.5px", lineHeight: "2.1" }}
        >
          {paragraph.sentences.map((sentence) => {
            const spans: ProcessedSpan[] = showErrors
              ? paragraph.errors
                  .filter((err) => err.sentenceIndex === sentence.index)
                  .map((err, i) => ({
                    key: `s${sentence.index}-e${i}-${err.offset}`,
                    start: err.offset,
                    end: err.offset + err.errorLength,
                    contextStart: err.offset,
                    contextEnd: err.offset + err.errorLength,
                    level: "",
                    dim: err.dimensionCode,
                    tooltip:
                      err.message +
                      (err.replacements.length > 0 ? ` → "${err.replacements[0]}"` : ""),
                    weight: err.weight,
                  }))
              : paragraph.matches
                  .filter((m) => m.sentenceIndex === sentence.index)
                  .map((m, i) => ({
                    key: `s${sentence.index}-m${i}-${m.startChar}`,
                    start: m.startChar,
                    end: m.endChar,
                    contextStart: m.contextStartChar,
                    contextEnd: m.contextEndChar,
                    level: m.lowestLevel,
                    dim: m.dimension,
                    tooltip:
                      `${m.guideword}  ·  ${m.lowestLevel}` +
                      (m.explanation ? `\n${m.explanation}` : ""),
                  }));

            return (
              <span key={sentence.index}>
                {renderSentenceText(
                  sentence.text,
                  spans,
                  activeTooltip,
                  setActiveTooltip,
                  showErrors
                )}
                {" "}
              </span>
            );
          })}
        </div>

        {/* Summary chips */}
        <div className="flex gap-2 mt-3 flex-wrap">
          {!showErrors ? (
            <>
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
                style={{ background: "rgba(0,0,0,0.05)", color: "var(--on-surface-variant)" }}
              >
                {r.nAssigned} structures
              </span>
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
                style={{ background: "rgba(0,0,0,0.05)", color: "var(--on-surface-variant)" }}
              >
                avg {r.avgLevelStr}
              </span>
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
                style={{ background: "rgba(0,0,0,0.05)", color: "var(--on-surface-variant)" }}
              >
                {r.density.toFixed(1)}/sent
              </span>
            </>
          ) : (
            <>
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
                style={{ background: "rgba(0,0,0,0.05)", color: "var(--on-surface-variant)" }}
              >
                {e.count} errors
              </span>
              <span
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium"
                style={{ background: e.qualityColor + "20", color: e.qualityColor }}
              >
                quality {e.qualityScore}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Right — metric sidebar */}
      <div className="w-[33%] shrink-0 pt-1">
        {!showErrors ? (
          <RichnessPanel r={r} e={e} />
        ) : (
          <ErrorPanel e={e} errors={paragraph.errors} />
        )}
      </div>
    </motion.div>
  );
}
