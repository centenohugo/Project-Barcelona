"use client";

import MetricBar from "./MetricBar";
import type {
  FluencyLessonData,
} from "@/lib/types";

// ── Colour helpers ─────────────────────────────────────────────────────────────

function scoreColor(score: number | null): { fg: string; bg: string } {
  if (score === null) return { fg: "#9CA3AF", bg: "#F3F4F6" };
  if (score >= 80) return { fg: "#059669", bg: "#D1FAE5" };
  if (score >= 60) return { fg: "#D97706", bg: "#FEF3C7" };
  return { fg: "#DC2626", bg: "#FEE2E2" };
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

// ── Filler examples helper ─────────────────────────────────────────────────────

function getFillerExamples(
  sentences: FluencyLessonData["sentences"],
  ft: string
): { examples: string[]; hasMore: boolean } {
  const seen = new Set<string>();
  for (const s of sentences) {
    for (const w of s.words) {
      if (w.isFiller && w.fillerType === ft) {
        seen.add(w.fillerPattern ?? w.word);
      }
    }
  }
  const arr = [...seen];
  return { examples: arr.slice(0, 3), hasMore: arr.length > 3 };
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
                const { examples, hasMore } = getFillerExamples(data.sentences, ft);
                return (
                  <div key={ft}>
                    <HBar
                      label={`${ft}  ${pct(cnt, fillerTotal)}%`}
                      pct={pct(cnt, fillerTotal)}
                      count={cnt}
                      color={FILLER_COLORS[ft] ?? "#6B7280"}
                    />
                    {examples.length > 0 && (
                      <div
                        style={{
                          fontSize: "10px",
                          color: "#9CA3AF",
                          paddingLeft: "138px",
                          marginTop: "-6px",
                          marginBottom: "6px",
                          fontStyle: "italic",
                        }}
                      >
                        {examples.map((e, i) => (
                          <span key={i} style={{ marginRight: "8px" }}>{e}</span>
                        ))}
                        {hasMore && <span>…</span>}
                      </div>
                    )}
                  </div>
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
    </div>
  );
}
