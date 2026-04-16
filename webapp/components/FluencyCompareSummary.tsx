"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import MetricBar from "./MetricBar";
import type {
  FluencyLessonData,
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
  thr: { p25Ms: number; p75Ms: number; p90Ms: number }
) {
  if (speed === null) return { bg: "#F9FAFB", border: "#E5E7EB", color: "#9CA3AF" };
  const ms = speed * 1000;
  if (ms < thr.p25Ms) return { bg: "#D1FAE5", border: "#34D399", color: "#064E3B" };
  if (ms <= thr.p75Ms) return { bg: "#F3F4F6", border: "#D1D5DB", color: "#374151" };
  if (ms <= thr.p90Ms) return { bg: "#FEF3C7", border: "#FCD34D", color: "#78350F" };
  return { bg: "#FEE2E2", border: "#FCA5A5", color: "#991B1B" };
}

function gapColor(g: number) {
  if (g < 0.08) return "#34D399";
  if (g < 0.25) return "#FCD34D";
  return "#F87171";
}

function buildDupMap(dups: FluencyDuplicate[]) {
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

// ── Horizontal bar ─────────────────────────────────────────────────────────────

function HBar({
  label,
  pct,
  count,
  color,
}: {
  label: string;
  pct: number;
  count: number | string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-2 mb-1.5">
      <span style={{ width: "130px", fontSize: "11px", color: "#374151", flexShrink: 0 }}>
        {label}
      </span>
      <div
        style={{ flex: 1, background: "#E5E7EB", borderRadius: "3px", height: "14px" }}
      >
        <div
          style={{
            width: `${pct}%`,
            background: color,
            height: "14px",
            borderRadius: "3px",
            transition: "width 700ms cubic-bezier(0.34,1.56,0.64,1)",
          }}
        />
      </div>
      <span style={{ width: "30px", textAlign: "right", fontSize: "11px", fontWeight: 600 }}>
        {count}
      </span>
    </div>
  );
}

// ── Stat card ──────────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  color = "#374151",
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div
      className="flex flex-col items-center justify-center rounded-xl px-3 py-2 flex-1 min-w-0"
      style={{ background: "#F9FAFB", border: "1px solid #E5E7EB" }}
    >
      <span style={{ fontSize: "18px", fontWeight: 800, color, lineHeight: 1 }}>{value}</span>
      <span style={{ fontSize: "9px", color: "#6B7280", marginTop: "3px" }}>{label}</span>
    </div>
  );
}

// ── Section header ─────────────────────────────────────────────────────────────

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <div
      className="text-[10px] font-semibold uppercase tracking-[0.07em] text-on-surface-variant font-[family-name:var(--font-body)] mb-2 mt-3"
    >
      {children}
    </div>
  );
}

// ── Inline filler/repeat text ──────────────────────────────────────────────────

function FillerRepeatText({ sentence }: { sentence: FluencySentenceRecord }) {
  const dupMap = buildDupMap(sentence.duplicates);
  if (sentence.fillers.count === 0 && sentence.duplicates.length === 0) {
    return (
      <span style={{ fontSize: "12px", lineHeight: 2, fontFamily: "Georgia, serif" }}>
        {sentence.text}
      </span>
    );
  }
  return (
    <span style={{ fontSize: "12px", lineHeight: 2.2, fontFamily: "Georgia, serif" }}>
      {sentence.words.map((word: FluencyWordData, i: number) => {
        const dup = dupMap.get(i);
        if (word.isFiller) {
          return (
            <span
              key={i}
              className="rounded mx-0.5 italic"
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
              className="rounded mx-0.5"
              style={{ padding: "1px 5px", background: "#FEF2F2", color: "#DC2626", borderBottom: "2px dotted #DC2626" }}
              title={`first: "${dup.label}"`}
            >
              {word.punctuatedWord}
            </span>
          ) : (
            <span
              key={i}
              className="rounded mx-0.5 line-through"
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

// ── Speed/gaps row (expandable) ────────────────────────────────────────────────

function SpeedGapsView({
  sentence,
  thr,
}: {
  sentence: FluencySentenceRecord;
  thr: { p25Ms: number; p75Ms: number; p90Ms: number };
}) {
  return (
    <div style={{ display: "flex", flexWrap: "wrap", alignItems: "flex-end", lineHeight: "3.8", padding: "2px 0" }}>
      {sentence.words.flatMap((word: FluencyWordData, i: number) => {
        const sStyle = word.isFiller
          ? { bg: "#FFF7ED", border: "#F97316", color: "#9A3412" }
          : getSpeedStyle(word.speed, thr);
        const chip = (
          <div
            key={"w-" + i}
            className="inline-flex flex-col items-center"
            style={{ margin: "0 2px" }}
          >
            <span
              className="rounded-md px-1.5 py-0.5 whitespace-nowrap"
              style={{
                background: sStyle.bg,
                border: "1px solid " + sStyle.border,
                color: sStyle.color,
                fontStyle: word.isFiller ? "italic" : "normal",
                fontFamily: "Georgia, serif",
                fontSize: "11px",
              }}
            >
              {word.punctuatedWord}
            </span>
            <span style={{ fontSize: "7px", color: word.isFiller ? "#F97316" : "#9CA3AF", marginTop: "1px" }}>
              {word.isFiller ? (word.fillerType ?? "filler") : word.speed != null ? Math.round(word.speed * 1000) + "ms" : "—"}
            </span>
          </div>
        );
        if (i < sentence.words.length - 1) {
          const next = sentence.words[i + 1];
          const gap = next.start - word.end;
          const gCol = gap >= 0 ? gapColor(gap) : "#D1D5DB";
          return [
            chip,
            <div key={"g-" + i} style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", width: "20px", margin: "0 1px" }}>
              <div style={{ width: "2px", height: "16px", background: gCol, margin: "0 auto" }} />
              <span style={{ fontSize: "6px", color: gCol, marginTop: "1px" }}>{gap >= 0 ? Math.round(gap * 1000) + "ms" : "—"}</span>
            </div>,
          ];
        }
        return [chip];
      })}
    </div>
  );
}

// ── Sentence row ───────────────────────────────────────────────────────────────

function SentenceRow({
  sentence,
  thr,
}: {
  sentence: FluencySentenceRecord;
  thr: { p25Ms: number; p75Ms: number; p90Ms: number };
}) {
  const [open, setOpen] = useState(false);
  const score = sentence.fluency.score;
  const { fg, bg } = scoreColor(score);
  const nFillers = sentence.fillers.count;
  const nRepeats = sentence.duplicates.reduce((s, d) => s + d.occurrences - 1, 0);

  return (
    <div className="mb-2.5">
      <div className="flex items-start gap-2">
        <span style={{ width: "18px", fontSize: "9px", color: "#9CA3AF", flexShrink: 0, marginTop: "2px" }}>
          s{sentence.sentenceId}
        </span>
        <div className="flex-1 min-w-0">
          <FillerRepeatText sentence={sentence} />
          <div className="flex gap-1 mt-1 flex-wrap">
            {score !== null && (
              <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded-full" style={{ background: bg, color: fg }}>
                {score}
              </span>
            )}
            {nFillers > 0 && (
              <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: "#FFF7ED", color: "#9A3412", border: "1px solid #F97316" }}>
                {nFillers} filler{nFillers > 1 ? "s" : ""}
              </span>
            )}
            {nRepeats > 0 && (
              <span className="text-[9px] px-1.5 py-0.5 rounded-full" style={{ background: "#FEE2E2", color: "#991B1B" }}>
                {nRepeats} repeat{nRepeats > 1 ? "s" : ""}
              </span>
            )}
            <button
              onClick={() => setOpen((v) => !v)}
              className="text-[9px] px-1.5 py-0.5 rounded-full cursor-pointer"
              style={{ background: open ? "var(--primary)" : "rgba(0,0,0,0.06)", color: open ? "var(--on-primary)" : "var(--on-surface-variant)" }}
            >
              {open ? "▲ timing" : "▼ timing"}
            </button>
          </div>
        </div>
      </div>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            style={{ overflow: "hidden" }}
          >
            <div className="mt-1.5 rounded-xl p-2.5" style={{ background: "var(--surface)", border: "1px solid var(--surface-variant)" }}>
              <SpeedGapsView sentence={sentence} thr={thr} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

const FILLER_COLORS: Record<string, string> = {
  hesitation: "#8B5CF6",
  backchannel: "#3B82F6",
  discourse_marker: "#F97316",
  placeholder: "#EF4444",
};

export default function FluencyCompareSummary({ data }: { data: FluencyLessonData }) {
  const thr = data.speedThresholds;
  const sb = data.speedBuckets;
  const { fg: avgFg } = scoreColor(data.avgFluency);

  function pct(n: number, total: number) {
    return total > 0 ? Math.round((n / total) * 100) : 0;
  }

  const sortedSentences = [...data.sentences].sort(
    (a, b) => (a.fluency.score ?? 101) - (b.fluency.score ?? 101)
  );

  const scoreLabels = ["0–20", "20–40", "40–60", "60–80", "80–100"];
  const scoreMids = [10, 30, 50, 70, 90];
  const scoreTotal = data.scoreDist.reduce((a, b) => a + b, 0);

  const fillerTotal = Object.values(data.fillerTypes).reduce((a, b) => a + b, 0);
  const fillerOrder = ["hesitation", "backchannel", "discourse_marker", "placeholder"];

  return (
    <div className="flex flex-col gap-0">
      {/* Stat cards row */}
      <div className="flex gap-2 mb-2">
        <StatCard label="Avg fluency" value={String(data.avgFluency)} color={avgFg} />
        <StatCard label="Filler rate" value={data.fillerRate + "%"} color="#F97316" />
        <StatCard label="Avg gap" value={data.avgGapMs + "ms"} color="#6B7280" />
        <StatCard label="Confidence" value={data.avgAccuracy + "%"} color="#059669" />
      </div>

      {/* Speed distribution */}
      <SectionTitle>Word speed distribution</SectionTitle>
      <div className="rounded-xl p-3" style={{ background: "#F9FAFB", border: "1px solid #E5E7EB" }}>
        <HBar label={`Fast  ${pct(sb.fast, sb.total)}%`} pct={pct(sb.fast, sb.total)} count={sb.fast} color="#34D399" />
        <HBar label={`Normal  ${pct(sb.normal, sb.total)}%`} pct={pct(sb.normal, sb.total)} count={sb.normal} color="#9CA3AF" />
        <HBar label={`Slow  ${pct(sb.slow, sb.total)}%`} pct={pct(sb.slow, sb.total)} count={sb.slow} color="#FCD34D" />
        <HBar label={`Very slow  ${pct(sb.verySlow, sb.total)}%`} pct={pct(sb.verySlow, sb.total)} count={sb.verySlow} color="#FCA5A5" />
        <div style={{ fontSize: "9px", color: "#9CA3AF", marginTop: "4px" }}>
          fast &lt; {thr.p25Ms}ms · slow &gt; {thr.p75Ms}ms · very slow &gt; {thr.p90Ms}ms/letter
        </div>
      </div>

      {/* Filler type breakdown */}
      {fillerTotal > 0 && (
        <>
          <SectionTitle>Filler types</SectionTitle>
          <div className="rounded-xl p-3" style={{ background: "#F9FAFB", border: "1px solid #E5E7EB" }}>
            {fillerOrder
              .filter((ft) => (data.fillerTypes[ft] ?? 0) > 0)
              .map((ft) => {
                const cnt = data.fillerTypes[ft];
                return (
                  <HBar
                    key={ft}
                    label={`${ft}  ${pct(cnt, fillerTotal)}%`}
                    pct={pct(cnt, fillerTotal)}
                    count={cnt}
                    color={FILLER_COLORS[ft] ?? "#6B7280"}
                  />
                );
              })}
          </div>
        </>
      )}

      {/* Score distribution */}
      <SectionTitle>Fluency score distribution</SectionTitle>
      <div className="rounded-xl p-3" style={{ background: "#F9FAFB", border: "1px solid #E5E7EB" }}>
        {scoreLabels.map((lbl, i) => (
          <HBar
            key={lbl}
            label={`${lbl}  ${pct(data.scoreDist[i], scoreTotal)}%`}
            pct={pct(data.scoreDist[i], scoreTotal)}
            count={data.scoreDist[i]}
            color={scoreColor(scoreMids[i]).fg}
          />
        ))}
      </div>

      {/* Component averages */}
      <SectionTitle>Component averages</SectionTitle>
      <div className="flex flex-col gap-2 rounded-xl p-3" style={{ background: "#F9FAFB", border: "1px solid #E5E7EB" }}>
        <MetricBar label="Speed ×35%" value={Math.round(data.compAvgs.speed)} color="#34D399" />
        <MetricBar label="Thinking ×35%" value={Math.round(data.compAvgs.gaps)} color="#60A5FA" />
        <MetricBar label="Fillers ×15%" value={Math.round(data.compAvgs.fillers)} color="#F97316" />
        <MetricBar label="Duplicates ×15%" value={Math.round(data.compAvgs.dups)} color="#A78BFA" />
      </div>

      {/* Sentences sorted worst → best */}
      <SectionTitle>Sentences — worst → best</SectionTitle>
      <div
        className="rounded-xl p-3 overflow-y-auto"
        style={{ maxHeight: "480px", background: "#fff", border: "1px solid #E5E7EB" }}
      >
        {sortedSentences.map((sentence) => (
          <SentenceRow key={sentence.sentenceId} sentence={sentence} thr={thr} />
        ))}
      </div>
    </div>
  );
}
