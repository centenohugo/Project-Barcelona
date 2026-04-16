"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import type { GrammarCompareSummary, GrammarStructureItem, GrammarErrorItem } from "@/lib/types";

// ── Colour palettes ────────────────────────────────────────────────────────────

const CEFR_DOT: Record<string, string> = {
  A1: "#9CA3AF", A2: "#3B82F6",
  B1: "#10B981", B2: "#F59E0B",
  C1: "#EF4444", C2: "#8B5CF6",
};
const CEFR_TEXT: Record<string, string> = {
  A1: "#4B5563", A2: "#1D4ED8",
  B1: "#065F46", B2: "#92400E",
  C1: "#991B1B", C2: "#5B21B6",
};
const CEFR_BG: Record<string, string> = {
  A1: "#F3F4F6", A2: "#DBEAFE",
  B1: "#D1FAE5", B2: "#FEF3C7",
  C1: "#FEE2E2", C2: "#EDE9FE",
};

const SEV_BG: Record<number, string> = { 1: "#F0FDF4", 2: "#FFFBEB", 3: "#FEF2F2" };
const SEV_BORDER: Record<number, string> = { 1: "#4ADE80", 2: "#FCD34D", 3: "#F87171" };
const SEV_TEXT: Record<number, string> = { 1: "#166534", 2: "#78350F", 3: "#7F1D1D" };
const SEV_LABEL: Record<number, string> = { 1: "minor", 2: "medium", 3: "major" };

const DIM_COLOR: Record<string, string> = {
  A: "#3B82F6", B: "#F59E0B", C: "#10B981", D: "#8B5CF6",
};

// ── Helpers ────────────────────────────────────────────────────────────────────

function highlightSpan(sentence: string, spanText: string): React.ReactNode {
  const idx = sentence.toLowerCase().indexOf(spanText.toLowerCase());
  if (idx === -1) {
    const clipped = sentence.length > 90 ? sentence.slice(0, 90) + "…" : sentence;
    return <em style={{ color: "#555", fontSize: "12px" }}>{clipped}</em>;
  }
  const pre = sentence.slice(0, idx);
  const mid = sentence.slice(idx, idx + spanText.length);
  const post = sentence.slice(idx + spanText.length);
  const clipped = (pre + "·" + mid + "·" + post).length > 120;
  return (
    <em style={{ color: "#555", fontSize: "12px" }}>
      {clipped ? "…" : ""}{pre}
      <strong style={{ color: "#1a237e", textDecoration: "underline dotted", textUnderlineOffset: "2px" }}>
        {mid}
      </strong>
      {post.length > 60 ? post.slice(0, 57) + "…" : post}
    </em>
  );
}

function highlightError(sentence: string, offset: number, length: number, weight: number): React.ReactNode {
  const pre = sentence.slice(0, offset);
  const mid = sentence.slice(offset, offset + length);
  const post = sentence.slice(offset + length);
  const bg = SEV_BG[weight] ?? "#FFF";
  const border = SEV_BORDER[weight] ?? "#ccc";
  return (
    <em style={{ color: "#444", fontSize: "12px" }}>
      {pre.length > 50 ? "…" + pre.slice(-30) : pre}
      <span style={{ background: bg, borderBottom: `2px solid ${border}`, borderRadius: "2px", padding: "0 2px" }}>
        {mid}
      </span>
      {post.length > 50 ? post.slice(0, 50) + "…" : post}
    </em>
  );
}

// ── Structure row ──────────────────────────────────────────────────────────────

interface StructRowProps {
  item: GrammarStructureItem | null;
  isHovered: boolean;
  onEnter: () => void;
  onLeave: () => void;
}

function StructRow({ item, isHovered, onEnter, onLeave }: StructRowProps) {
  if (!item) {
    return (
      <div
        className="py-2 px-3 rounded-lg mb-1.5"
        style={{ border: "1px dashed rgba(0,0,0,0.12)", opacity: 0.35 }}
      >
        <span style={{ fontSize: "11px", color: "#9CA3AF", fontStyle: "italic" }}>— not detected —</span>
      </div>
    );
  }

  return (
    <div
      className="py-2 px-3 rounded-lg mb-1.5 cursor-default transition-all"
      style={{
        background: isHovered ? "#FFF9C4" : "transparent",
        border: isHovered ? "1px solid #F9A825" : "1px solid transparent",
      }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
    >
      {/* Level badge + category chip + guideword + count */}
      <div className="flex items-center gap-1.5 mb-1 flex-wrap">
        <span
          className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold"
          style={{ background: CEFR_BG[item.lowestLevel] ?? "#F3F4F6", color: CEFR_TEXT[item.lowestLevel] ?? "#374151" }}
        >
          {item.lowestLevel}
        </span>
        <span
          className="shrink-0 px-1.5 py-0.5 rounded text-[10px]"
          style={{ background: "#ECEFF1", color: "#37474F" }}
        >
          {item.category}
        </span>
        <span
          className="text-[12px] text-on-surface flex-1 min-w-0 font-medium truncate"
          title={item.guideword}
        >
          {item.guideword}
        </span>
        <span
          className="shrink-0 text-[11px] font-semibold font-[family-name:var(--font-display)] ml-auto"
          style={{ color: CEFR_DOT[item.lowestLevel] ?? "#6B7280" }}
        >
          {item.count}×
        </span>
      </div>
      {/* Example sentence */}
      <div className="pl-0.5">
        {highlightSpan(item.exampleSentence, item.exampleSpan)}
      </div>
    </div>
  );
}

// ── Error card ─────────────────────────────────────────────────────────────────

function ErrorCard({ item, isShared }: { item: GrammarErrorItem; isShared: boolean }) {
  const bg = SEV_BG[item.weight] ?? "#F9FAFB";
  const border = SEV_BORDER[item.weight] ?? "#D1D5DB";
  const text = SEV_TEXT[item.weight] ?? "#374151";
  const dimColor = DIM_COLOR[item.dimensionCode] ?? "#6B7280";

  return (
    <div
      className="rounded-xl p-3 mb-2.5"
      style={{ background: bg, border: `1px solid ${border}` }}
    >
      {/* Header row */}
      <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
        <span
          className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold text-white"
          style={{ background: dimColor }}
        >
          {item.dimensionCode}
        </span>
        <span className="text-[12px] font-semibold flex-1 min-w-0" style={{ color: "#263238" }}>
          {item.grammarCategory}
        </span>
        {isShared && (
          <span className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold text-white" style={{ background: "#F97316" }}>
            shared
          </span>
        )}
        <span
          className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold"
          style={{ background: bg, border: `1px solid ${border}`, color: text }}
        >
          {SEV_LABEL[item.weight] ?? ""}
        </span>
        <span className="shrink-0 text-[11px] font-bold" style={{ color: text }}>
          {item.count}×
        </span>
      </div>
      {/* Example */}
      <div className="mb-1">
        {highlightError(item.exampleSentence, item.exampleOffset, item.exampleLength, item.weight)}
      </div>
      {/* Message */}
      <div style={{ fontSize: "11px", color: "#78909C" }}>{item.exampleMessage}</div>
    </div>
  );
}

// ── Stats pills ────────────────────────────────────────────────────────────────

function StatsPills({ stats, richnessColor }: { stats: GrammarCompareSummary["stats"]; richnessColor: string }) {
  const pills = [
    { label: "sentences", value: stats.sentenceCount, color: "#37474F" },
    { label: "structures", value: stats.structureCount, color: "#1565C0" },
    { label: "error types", value: stats.errorTypeCount, color: "#C62828" },
    { label: "richness", value: stats.avgRichnessScore, color: richnessColor },
  ];
  return (
    <div className="flex gap-2 flex-wrap mb-3">
      {pills.map((p) => (
        <span
          key={p.label}
          className="px-2.5 py-1 rounded-lg text-[12px]"
          style={{ background: "rgba(0,0,0,0.05)" }}
        >
          <strong style={{ color: p.color }}>{p.value}</strong>{" "}
          <span style={{ color: "#607D8B" }}>{p.label}</span>
        </span>
      ))}
    </div>
  );
}

// ── Main compare pane ──────────────────────────────────────────────────────────

interface GrammarComparePaneProps {
  studentId: string;
  leftId: number;
  rightId: number;
  leftName: string;
  rightName: string;
}

function useCompareFetch(studentId: string, lessonId: number) {
  const [data, setData] = useState<GrammarCompareSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setLoading(true);
    setError(null);
    fetch(`/api/lesson/${studentId}/${lessonId}/grammar/compare`)
      .then((r) => { if (!r.ok) throw new Error(`${r.status}`); return r.json(); })
      .then((d: GrammarCompareSummary) => { setData(d); setLoading(false); })
      .catch((e) => { setError(e.message); setLoading(false); });
  }, [studentId, lessonId]);

  return { data, loading, error };
}

export default function GrammarComparePane({ studentId, leftId, rightId, leftName, rightName }: GrammarComparePaneProps) {
  const left = useCompareFetch(studentId, leftId);
  const right = useCompareFetch(studentId, rightId);

  const [hoveredSid, setHoveredSid] = useState<string | null>(null);
  const leftScrollRef = useRef<HTMLDivElement>(null);
  const rightScrollRef = useRef<HTMLDivElement>(null);
  const syncingRef = useRef(false);

  // Synced scroll
  useEffect(() => {
    const l = leftScrollRef.current;
    const r = rightScrollRef.current;
    if (!l || !r) return;
    const onLeft = () => {
      if (syncingRef.current) return;
      syncingRef.current = true;
      r.scrollTop = l.scrollTop;
      syncingRef.current = false;
    };
    const onRight = () => {
      if (syncingRef.current) return;
      syncingRef.current = true;
      l.scrollTop = r.scrollTop;
      syncingRef.current = false;
    };
    l.addEventListener("scroll", onLeft);
    r.addEventListener("scroll", onRight);
    return () => { l.removeEventListener("scroll", onLeft); r.removeEventListener("scroll", onRight); };
  }, [left.data, right.data]);

  const loading = left.loading || right.loading;

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-6">
        {[0, 1].map((i) => (
          <div key={i} className="flex flex-col gap-3">
            {[1, 2, 3, 4, 5].map((j) => (
              <div key={j} className="rounded-xl bg-surface-lowest p-4 animate-pulse">
                <div className="h-3 w-2/3 rounded bg-surface-variant mb-2" />
                <div className="h-3 w-full rounded bg-surface-variant" />
              </div>
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (!left.data && !right.data) {
    return (
      <div className="rounded-2xl bg-surface-lowest p-12 text-center">
        <p className="text-on-surface-variant font-[family-name:var(--font-body)]">Grammar data not available.</p>
      </div>
    );
  }

  // Build union of structure IDs ordered as: shared (level desc) → left-only → right-only
  const leftMap = new Map((left.data?.structures ?? []).map((s) => [s.structureId, s]));
  const rightMap = new Map((right.data?.structures ?? []).map((s) => [s.structureId, s]));

  const shared = [...leftMap.keys()]
    .filter((sid) => rightMap.has(sid))
    .sort((a, b) => {
      const la = leftMap.get(a)!;
      const lb = leftMap.get(b)!;
      return lb.lowestLevelNumeric - la.lowestLevelNumeric || lb.count - la.count;
    });
  const leftOnly = [...leftMap.keys()]
    .filter((sid) => !rightMap.has(sid))
    .sort((a, b) => leftMap.get(b)!.lowestLevelNumeric - leftMap.get(a)!.lowestLevelNumeric);
  const rightOnly = [...rightMap.keys()]
    .filter((sid) => !leftMap.has(sid))
    .sort((a, b) => rightMap.get(b)!.lowestLevelNumeric - rightMap.get(a)!.lowestLevelNumeric);

  // Interleave for the union row list:
  // Each entry in union has a sid; left column shows leftMap.get(sid) or null; right shows rightMap.get(sid) or null
  const maxExtra = Math.max(leftOnly.length, rightOnly.length);
  const extraRows: string[] = [];
  for (let i = 0; i < maxExtra; i++) {
    if (i < leftOnly.length) extraRows.push(leftOnly[i]);
    if (i < rightOnly.length) extraRows.push(rightOnly[i]);
  }
  const union = [...shared, ...extraRows].slice(0, 18);

  // Error shared categories
  const leftErrCats = new Set((left.data?.errors ?? []).map((e) => e.grammarCategory));
  const rightErrCats = new Set((right.data?.errors ?? []).map((e) => e.grammarCategory));

  // Richness colors (fallback)
  const leftRichnessColor = left.error ? "#6B7280" : (left.data ? (left.data.stats.avgRichnessScore >= 70 ? "#15803d" : left.data.stats.avgRichnessScore >= 50 ? "#d97706" : left.data.stats.avgRichnessScore >= 30 ? "#ea580c" : "#dc2626") : "#6B7280");
  const rightRichnessColor = right.error ? "#6B7280" : (right.data ? (right.data.stats.avgRichnessScore >= 70 ? "#15803d" : right.data.stats.avgRichnessScore >= 50 ? "#d97706" : right.data.stats.avgRichnessScore >= 30 ? "#ea580c" : "#dc2626") : "#6B7280");

  return (
    <motion.div
      key={`${leftId}-${rightId}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col gap-8"
    >
      {/* ── Top structures ── */}
      <div>
        <div className="grid grid-cols-2 gap-6">
          {/* Column headers */}
          <div>
            <div
              className="rounded-t-xl px-4 py-2.5 font-[family-name:var(--font-display)] font-bold text-white text-sm"
              style={{ background: "#1565C0" }}
            >
              {leftName}
            </div>
            {left.data && (
              <div className="pt-2 pb-1">
                <StatsPills stats={left.data.stats} richnessColor={leftRichnessColor} />
              </div>
            )}
          </div>
          <div>
            <div
              className="rounded-t-xl px-4 py-2.5 font-[family-name:var(--font-display)] font-bold text-white text-sm"
              style={{ background: "#2E7D32" }}
            >
              {rightName}
            </div>
            {right.data && (
              <div className="pt-2 pb-1">
                <StatsPills stats={right.data.stats} richnessColor={rightRichnessColor} />
              </div>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
            Top grammar structures
          </span>
          <span className="text-[11px] text-on-surface-variant font-[family-name:var(--font-body)]">
            — {shared.length} shared · {leftOnly.length} only in {leftName} · {rightOnly.length} only in {rightName}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Left structures list */}
          <div
            ref={leftScrollRef}
            className="overflow-y-auto rounded-b-xl"
            style={{
              maxHeight: "420px",
              border: "1px solid rgba(0,0,0,0.08)",
              borderTop: "none",
              padding: "10px",
              background: "var(--surface-lowest)",
            }}
          >
            {union.length === 0 && (
              <p className="text-xs text-on-surface-variant italic p-2">No structures detected.</p>
            )}
            {union.map((sid) => (
              <StructRow
                key={sid}
                item={leftMap.get(sid) ?? null}
                isHovered={hoveredSid === sid}
                onEnter={() => setHoveredSid(sid)}
                onLeave={() => setHoveredSid(null)}
              />
            ))}
          </div>

          {/* Right structures list */}
          <div
            ref={rightScrollRef}
            className="overflow-y-auto rounded-b-xl"
            style={{
              maxHeight: "420px",
              border: "1px solid rgba(0,0,0,0.08)",
              borderTop: "none",
              padding: "10px",
              background: "var(--surface-lowest)",
            }}
          >
            {union.length === 0 && (
              <p className="text-xs text-on-surface-variant italic p-2">No structures detected.</p>
            )}
            {union.map((sid) => (
              <StructRow
                key={sid}
                item={rightMap.get(sid) ?? null}
                isHovered={hoveredSid === sid}
                onEnter={() => setHoveredSid(sid)}
                onLeave={() => setHoveredSid(null)}
              />
            ))}
          </div>
        </div>
      </div>

      {/* ── Recurring errors ── */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
            Most recurring errors
          </span>
        </div>
        <div className="grid grid-cols-2 gap-6">
          <div>
            {(left.data?.errors ?? []).length === 0 ? (
              <div className="rounded-xl bg-surface-lowest p-6 text-center">
                <p className="text-xs text-on-surface-variant italic">No errors detected.</p>
              </div>
            ) : (
              (left.data?.errors ?? []).map((e) => (
                <ErrorCard key={e.grammarCategory} item={e} isShared={rightErrCats.has(e.grammarCategory)} />
              ))
            )}
          </div>
          <div>
            {(right.data?.errors ?? []).length === 0 ? (
              <div className="rounded-xl bg-surface-lowest p-6 text-center">
                <p className="text-xs text-on-surface-variant italic">No errors detected.</p>
              </div>
            ) : (
              (right.data?.errors ?? []).map((e) => (
                <ErrorCard key={e.grammarCategory} item={e} isShared={leftErrCats.has(e.grammarCategory)} />
              ))
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
