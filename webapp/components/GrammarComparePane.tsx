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
    return <em style={{ color: "var(--on-surface-variant)", fontSize: "12px" }}>{clipped}</em>;
  }
  const pre = sentence.slice(0, idx);
  const mid = sentence.slice(idx, idx + spanText.length);
  const post = sentence.slice(idx + spanText.length);
  return (
    <em style={{ color: "var(--on-surface-variant)", fontSize: "12px" }}>
      {pre.length > 40 ? "…" + pre.slice(-25) : pre}
      <strong style={{ color: "var(--on-surface)", textDecoration: "underline dotted", textUnderlineOffset: "2px" }}>
        {mid}
      </strong>
      {post.length > 55 ? post.slice(0, 52) + "…" : post}
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
    <em style={{ color: "var(--on-surface-variant)", fontSize: "12px" }}>
      {pre.length > 50 ? "…" + pre.slice(-30) : pre}
      <span style={{ background: bg, borderBottom: `2px solid ${border}`, borderRadius: "2px", padding: "0 2px" }}>
        {mid}
      </span>
      {post.length > 50 ? post.slice(0, 50) + "…" : post}
    </em>
  );
}

// ── Structure row (only rendered when item is present) ─────────────────────────

interface StructRowProps {
  item: GrammarStructureItem;
  isHovered: boolean;
  onEnter: () => void;
  onLeave: () => void;
}

function StructRow({ item, isHovered, onEnter, onLeave }: StructRowProps) {
  return (
    <div
      className="py-2.5 px-3 rounded-xl mb-1.5 cursor-default transition-all"
      style={{
        background: isHovered ? "rgba(var(--primary-rgb, 99,91,255), 0.07)" : "var(--surface-lowest)",
        border: isHovered ? "1px solid rgba(var(--primary-rgb, 99,91,255), 0.25)" : "1px solid rgba(0,0,0,0.06)",
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
          style={{ background: "rgba(0,0,0,0.06)", color: "var(--on-surface-variant)" }}
        >
          {item.category}
        </span>
        <span
          className="text-[12px] text-on-surface flex-1 min-w-0 font-medium truncate font-[family-name:var(--font-body)]"
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
      <div className="pl-0.5 font-[family-name:var(--font-body)]">
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
      className="rounded-xl p-3 mb-2"
      style={{ background: bg, border: `1px solid ${border}` }}
    >
      {/* Header row */}
      <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
        <span
          className="shrink-0 w-2 h-2 rounded-full"
          style={{ background: dimColor }}
        />
        <span className="text-[12px] font-semibold flex-1 min-w-0 font-[family-name:var(--font-body)]" style={{ color: "var(--on-surface)" }}>
          {item.grammarCategory}
        </span>
        {isShared && (
          <span className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-bold text-white" style={{ background: "var(--primary)" }}>
            shared
          </span>
        )}
        <span
          className="shrink-0 px-1.5 py-0.5 rounded text-[10px] font-semibold"
          style={{ background: bg, border: `1px solid ${border}`, color: text }}
        >
          {SEV_LABEL[item.weight] ?? ""}
        </span>
        <span className="shrink-0 text-[11px] font-bold font-[family-name:var(--font-display)]" style={{ color: text }}>
          {item.count}×
        </span>
      </div>
      {/* Example */}
      <div className="mb-1 font-[family-name:var(--font-body)]">
        {highlightError(item.exampleSentence, item.exampleOffset, item.exampleLength, item.weight)}
      </div>
      {/* Message */}
      <div className="font-[family-name:var(--font-body)]" style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}>
        {item.exampleMessage}
      </div>
    </div>
  );
}

// ── Stats pills ────────────────────────────────────────────────────────────────

function StatsPills({ stats }: { stats: GrammarCompareSummary["stats"] }) {
  const richnessColor =
    stats.avgRichnessScore >= 70 ? "#15803d"
    : stats.avgRichnessScore >= 50 ? "#d97706"
    : stats.avgRichnessScore >= 30 ? "#ea580c"
    : "#dc2626";

  const pills = [
    { label: "sentences", value: stats.sentenceCount },
    { label: "structures", value: stats.structureCount },
    { label: "error types", value: stats.errorTypeCount },
    { label: "richness", value: stats.avgRichnessScore, color: richnessColor },
  ];
  return (
    <div className="flex gap-2 flex-wrap mb-3">
      {pills.map((p) => (
        <span
          key={p.label}
          className="px-2.5 py-1 rounded-lg text-[11px] font-[family-name:var(--font-body)]"
          style={{ background: "rgba(0,0,0,0.05)" }}
        >
          <strong style={{ color: p.color ?? "var(--on-surface)" }}>{p.value}</strong>{" "}
          <span style={{ color: "var(--on-surface-variant)" }}>{p.label}</span>
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

  // Only show structures detected in BOTH lessons (shared)
  const leftMap = new Map((left.data?.structures ?? []).map((s) => [s.structureId, s]));
  const rightMap = new Map((right.data?.structures ?? []).map((s) => [s.structureId, s]));

  const shared = [...leftMap.keys()]
    .filter((sid) => rightMap.has(sid))
    .sort((a, b) => {
      const la = leftMap.get(a)!;
      const lb = leftMap.get(b)!;
      return lb.lowestLevelNumeric - la.lowestLevelNumeric || lb.count - la.count;
    })
    .slice(0, 12);

  // Error shared categories
  const leftErrCats = new Set((left.data?.errors ?? []).map((e) => e.grammarCategory));
  const rightErrCats = new Set((right.data?.errors ?? []).map((e) => e.grammarCategory));

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
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
            Shared grammar structures
          </span>
          <span className="text-[11px] text-on-surface-variant font-[family-name:var(--font-body)]">
            — {shared.length} in common
          </span>
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Left column */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold text-on-surface-variant font-[family-name:var(--font-body)] uppercase tracking-widest">
                {leftName}
              </span>
            </div>
            {left.data && <StatsPills stats={left.data.stats} />}
            <div
              ref={leftScrollRef}
              className="overflow-y-auto rounded-xl"
              style={{
                maxHeight: "380px",
                border: "1px solid rgba(0,0,0,0.07)",
                padding: "8px",
                background: "var(--surface-lowest)",
              }}
            >
              {shared.length === 0 ? (
                <p className="text-xs text-on-surface-variant italic p-2 font-[family-name:var(--font-body)]">No shared structures.</p>
              ) : (
                shared.map((sid) => (
                  <StructRow
                    key={sid}
                    item={leftMap.get(sid)!}
                    isHovered={hoveredSid === sid}
                    onEnter={() => setHoveredSid(sid)}
                    onLeave={() => setHoveredSid(null)}
                  />
                ))
              )}
            </div>
          </div>

          {/* Right column */}
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold text-on-surface-variant font-[family-name:var(--font-body)] uppercase tracking-widest">
                {rightName}
              </span>
            </div>
            {right.data && <StatsPills stats={right.data.stats} />}
            <div
              ref={rightScrollRef}
              className="overflow-y-auto rounded-xl"
              style={{
                maxHeight: "380px",
                border: "1px solid rgba(0,0,0,0.07)",
                padding: "8px",
                background: "var(--surface-lowest)",
              }}
            >
              {shared.length === 0 ? (
                <p className="text-xs text-on-surface-variant italic p-2 font-[family-name:var(--font-body)]">No shared structures.</p>
              ) : (
                shared.map((sid) => (
                  <StructRow
                    key={sid}
                    item={rightMap.get(sid)!}
                    isHovered={hoveredSid === sid}
                    onEnter={() => setHoveredSid(sid)}
                    onLeave={() => setHoveredSid(null)}
                  />
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Recurring errors ── */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
            Most recurring errors
          </span>
        </div>
        <div className="grid grid-cols-2 gap-6">
          <div>
            {(left.data?.errors ?? []).length === 0 ? (
              <div className="rounded-xl bg-surface-lowest p-6 text-center">
                <p className="text-xs text-on-surface-variant italic font-[family-name:var(--font-body)]">No errors detected.</p>
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
                <p className="text-xs text-on-surface-variant italic font-[family-name:var(--font-body)]">No errors detected.</p>
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
