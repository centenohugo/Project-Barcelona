"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import type { GrammarCompareSummary, GrammarStructureItem } from "@/lib/types";

// ── CEFR colours (structures only) ────────────────────────────────────────────

const CEFR_TEXT: Record<string, string> = {
  A1: "#4B5563", A2: "#1D4ED8", B1: "#065F46",
  B2: "#92400E", C1: "#991B1B", C2: "#5B21B6",
};
const CEFR_BG: Record<string, string> = {
  A1: "#F3F4F6", A2: "#DBEAFE", B1: "#D1FAE5",
  B2: "#FEF3C7", C1: "#FEE2E2", C2: "#EDE9FE",
};

const SEV_LABEL: Record<number, string> = { 1: "Minor", 2: "Medium", 3: "Major" };

// ── Helpers ────────────────────────────────────────────────────────────────────

function highlightSpan(sentence: string, spanText: string): React.ReactNode {
  const idx = sentence.toLowerCase().indexOf(spanText.toLowerCase());
  const clipped = (s: string, maxPre: number, maxPost: number) =>
    (s.length > maxPre ? "…" + s.slice(-maxPre) : s);
  if (idx === -1) {
    const text = sentence.length > 90 ? sentence.slice(0, 90) + "…" : sentence;
    return <em style={{ color: "var(--on-surface-variant)", fontSize: "12px" }}>{text}</em>;
  }
  const pre = sentence.slice(0, idx);
  const mid = sentence.slice(idx, idx + spanText.length);
  const post = sentence.slice(idx + spanText.length);
  return (
    <em style={{ color: "var(--on-surface-variant)", fontSize: "12px" }}>
      {clipped(pre, 35, 0)}
      <strong style={{ color: "var(--on-surface)", textDecoration: "underline dotted", textUnderlineOffset: "2px" }}>
        {mid}
      </strong>
      {post.length > 55 ? post.slice(0, 52) + "…" : post}
    </em>
  );
}

function highlightError(sentence: string, offset: number, length: number): React.ReactNode {
  const pre = sentence.slice(0, offset);
  const mid = sentence.slice(offset, offset + length);
  const post = sentence.slice(offset + length);
  return (
    <em style={{ color: "var(--on-surface-variant)", fontSize: "12px" }}>
      {pre.length > 50 ? "…" + pre.slice(-30) : pre}
      <span style={{
        color: "var(--on-surface)",
        textDecoration: "underline",
        textDecorationStyle: "wavy",
        textDecorationColor: "var(--primary)",
        textUnderlineOffset: "3px",
      }}>
        {mid}
      </span>
      {post.length > 50 ? post.slice(0, 50) + "…" : post}
    </em>
  );
}

// ── Structure row ──────────────────────────────────────────────────────────────

function StructRow({
  item,
  isHovered,
  onEnter,
  onLeave,
}: {
  item: GrammarStructureItem;
  isHovered: boolean;
  onEnter: () => void;
  onLeave: () => void;
}) {
  return (
    <div
      className="py-2.5 px-3 rounded-xl mb-1.5 cursor-default transition-all"
      style={{
        background: isHovered ? "rgba(0,0,0,0.04)" : "var(--surface-lowest)",
        border: isHovered
          ? "1px solid rgba(0,0,0,0.12)"
          : "1px solid rgba(0,0,0,0.06)",
      }}
      onMouseEnter={onEnter}
      onMouseLeave={onLeave}
    >
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
        <span className="shrink-0 text-[11px] font-semibold font-[family-name:var(--font-display)] text-on-surface-variant ml-auto">
          {item.count}×
        </span>
      </div>
      <div className="pl-0.5 font-[family-name:var(--font-body)]">
        {highlightSpan(item.exampleSentence, item.exampleSpan)}
      </div>
    </div>
  );
}

// ── Stats pills ────────────────────────────────────────────────────────────────

function StatsPills({ stats }: { stats: GrammarCompareSummary["stats"] }) {
  const richnessColor =
    stats.avgRichnessScore >= 70 ? "#15803d"
    : stats.avgRichnessScore >= 50 ? "#d97706"
    : "#dc2626";

  return (
    <div className="flex gap-2 flex-wrap mb-3">
      {[
        { label: "sentences", value: stats.sentenceCount },
        { label: "structures", value: stats.structureCount },
        { label: "error types", value: stats.errorTypeCount },
        { label: "richness", value: stats.avgRichnessScore, color: richnessColor },
      ].map((p) => (
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

// ── Main component ─────────────────────────────────────────────────────────────

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

export default function GrammarComparePane({
  studentId, leftId, rightId, leftName, rightName,
}: GrammarComparePaneProps) {
  const left = useCompareFetch(studentId, leftId);
  const right = useCompareFetch(studentId, rightId);

  const [hoveredSid, setHoveredSid] = useState<string | null>(null);
  const leftScrollRef = useRef<HTMLDivElement>(null);
  const rightScrollRef = useRef<HTMLDivElement>(null);
  const syncingRef = useRef(false);

  // Synced scroll for structures
  useEffect(() => {
    const l = leftScrollRef.current;
    const r = rightScrollRef.current;
    if (!l || !r) return;
    const onLeft = () => { if (syncingRef.current) return; syncingRef.current = true; r.scrollTop = l.scrollTop; syncingRef.current = false; };
    const onRight = () => { if (syncingRef.current) return; syncingRef.current = true; l.scrollTop = r.scrollTop; syncingRef.current = false; };
    l.addEventListener("scroll", onLeft);
    r.addEventListener("scroll", onRight);
    return () => { l.removeEventListener("scroll", onLeft); r.removeEventListener("scroll", onRight); };
  }, [left.data, right.data]);

  if (left.loading || right.loading) {
    return (
      <div className="flex flex-col gap-3">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="rounded-xl bg-surface-lowest p-4 animate-pulse">
            <div className="h-3 w-2/3 rounded bg-surface-variant mb-2" />
            <div className="h-3 w-full rounded bg-surface-variant" />
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

  // Shared structures (in both lessons)
  const leftStructMap = new Map((left.data?.structures ?? []).map((s) => [s.structureId, s]));
  const rightStructMap = new Map((right.data?.structures ?? []).map((s) => [s.structureId, s]));
  const sharedStructs = [...leftStructMap.keys()]
    .filter((sid) => rightStructMap.has(sid))
    .sort((a, b) => {
      const la = leftStructMap.get(a)!;
      const lb = leftStructMap.get(b)!;
      return lb.lowestLevelNumeric - la.lowestLevelNumeric || lb.count - la.count;
    })
    .slice(0, 12);

  // Common errors (in both lessons)
  const leftErrMap = new Map((left.data?.errors ?? []).map((e) => [e.grammarCategory, e]));
  const rightErrMap = new Map((right.data?.errors ?? []).map((e) => [e.grammarCategory, e]));
  const commonErrors = [...leftErrMap.entries()]
    .filter(([cat]) => rightErrMap.has(cat))
    .sort((a, b) => b[1].weight - a[1].weight || b[1].count - a[1].count);

  return (
    <motion.div
      key={`${leftId}-${rightId}`}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="flex flex-col gap-8"
    >
      {/* ── Shared grammar structures (2-col synced) ── */}
      <div>
        <div className="flex items-center gap-2 mb-3">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
            Shared grammar structures
          </span>
          <span className="text-[11px] text-on-surface-variant font-[family-name:var(--font-body)]">
            — {sharedStructs.length} in common
          </span>
        </div>
        <div className="grid grid-cols-2 gap-6">
          {[
            { name: leftName, data: left.data, map: leftStructMap, ref: leftScrollRef },
            { name: rightName, data: right.data, map: rightStructMap, ref: rightScrollRef },
          ].map(({ name, data: d, map, ref }) => (
            <div key={name} className="flex flex-col gap-1">
              <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-widest font-[family-name:var(--font-body)] mb-1">
                {name}
              </span>
              {d && <StatsPills stats={d.stats} />}
              <div
                ref={ref}
                className="overflow-y-auto rounded-xl"
                style={{ maxHeight: "380px", border: "1px solid rgba(0,0,0,0.07)", padding: "8px", background: "var(--surface-lowest)" }}
              >
                {sharedStructs.length === 0 ? (
                  <p className="text-xs text-on-surface-variant italic p-2 font-[family-name:var(--font-body)]">No shared structures.</p>
                ) : (
                  sharedStructs.map((sid) => (
                    <StructRow
                      key={sid}
                      item={map.get(sid)!}
                      isHovered={hoveredSid === sid}
                      onEnter={() => setHoveredSid(sid)}
                      onLeave={() => setHoveredSid(null)}
                    />
                  ))
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Common errors (single column) ── */}
      <div>
        <div className="flex items-center gap-2 mb-4">
          <span className="text-[11px] font-semibold uppercase tracking-widest text-on-surface-variant font-[family-name:var(--font-body)]">
            Common errors
          </span>
          <span className="text-[11px] text-on-surface-variant font-[family-name:var(--font-body)]">
            — {commonErrors.length} shared
          </span>
        </div>

        {commonErrors.length === 0 ? (
          <div className="rounded-2xl bg-surface-lowest p-8 text-center">
            <p className="text-sm text-on-surface-variant italic font-[family-name:var(--font-body)]">No errors in common.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {commonErrors.map(([cat, leftErr]) => {
              const rightErr = rightErrMap.get(cat)!;
              return (
                <div
                  key={cat}
                  className="rounded-2xl bg-surface-lowest p-5"
                  style={{ border: "1px solid rgba(0,0,0,0.07)" }}
                >
                  {/* Title + severity */}
                  <div className="flex items-baseline gap-3 mb-4">
                    <span className="text-sm font-semibold text-on-surface font-[family-name:var(--font-display)]">
                      {cat}
                    </span>
                    <span
                      className="text-[10px] font-medium uppercase tracking-widest font-[family-name:var(--font-body)]"
                      style={{ color: "var(--on-surface-variant)" }}
                    >
                      Severity: {SEV_LABEL[leftErr.weight] ?? "—"}
                    </span>
                  </div>

                  {/* Lesson 1 */}
                  <div className="mb-3">
                    <span
                      className="block text-[9px] font-semibold uppercase tracking-widest mb-1.5 font-[family-name:var(--font-body)]"
                      style={{ color: "var(--on-surface-variant)" }}
                    >
                      {leftName}
                    </span>
                    <div className="font-[family-name:var(--font-body)]">
                      {highlightError(leftErr.exampleSentence, leftErr.exampleOffset, leftErr.exampleLength)}
                    </div>
                    <p
                      className="mt-1.5 font-[family-name:var(--font-body)]"
                      style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}
                    >
                      {leftErr.exampleMessage}
                    </p>
                  </div>

                  {/* Divider */}
                  <div style={{ height: "1px", background: "var(--surface-variant)", margin: "4px 0 12px" }} />

                  {/* Lesson 2 */}
                  <div>
                    <span
                      className="block text-[9px] font-semibold uppercase tracking-widest mb-1.5 font-[family-name:var(--font-body)]"
                      style={{ color: "var(--on-surface-variant)" }}
                    >
                      {rightName}
                    </span>
                    <div className="font-[family-name:var(--font-body)]">
                      {highlightError(rightErr.exampleSentence, rightErr.exampleOffset, rightErr.exampleLength)}
                    </div>
                    <p
                      className="mt-1.5 font-[family-name:var(--font-body)]"
                      style={{ fontSize: "11px", color: "var(--on-surface-variant)" }}
                    >
                      {rightErr.exampleMessage}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </motion.div>
  );
}
