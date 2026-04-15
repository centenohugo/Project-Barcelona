"use client";

import { useEffect, useState } from "react";

interface MetricBarProps {
  label: string;
  value: number;
  delay: number;
}

function MetricBar({ label, value, delay }: MetricBarProps) {
  const [width, setWidth] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setWidth(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-baseline justify-between">
        <span className="text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant font-[family-name:var(--font-body)]">
          {label}
        </span>
        <span className="text-sm font-semibold text-on-surface font-[family-name:var(--font-display)]">
          {value}%
        </span>
      </div>
      <div className="h-3 rounded-full bg-surface-variant overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{
            width: `${width}%`,
            background: "linear-gradient(90deg, var(--secondary), var(--secondary-container))",
            transition: `width 800ms cubic-bezier(0.34, 1.56, 0.64, 1)`,
          }}
        />
      </div>
    </div>
  );
}

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
