"use client";

import MetricBar from "./MetricBar";

const mockMetrics = [
  { label: "Metric A", value: 72 },
  { label: "Metric B", value: 58 },
  { label: "Metric C", value: 85 },
  { label: "Metric D", value: 41 },
  { label: "Metric E", value: 63 },
];

export default function MetricBars() {
  return (
    <div className="w-[38%] shrink-0 rounded-2xl bg-surface-lowest p-8 pl-8 pr-6 flex flex-col justify-between">
      <h2 className="font-[family-name:var(--font-display)] text-[1.75rem] font-bold text-on-surface tracking-tight mb-6">
        Key Metrics
      </h2>
      <div className="flex flex-col gap-5 flex-1 justify-center">
        {mockMetrics.map((m, i) => (
          <MetricBar key={m.label} label={m.label} value={m.value} delay={200 + i * 120} />
        ))}
      </div>
    </div>
  );
}
