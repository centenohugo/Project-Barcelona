"use client";

import { useEffect, useState } from "react";

export interface MetricBarProps {
  label: string;
  value: number;
  delay?: number;
  color?: string;
}

export default function MetricBar({ label, value, delay = 200, color }: MetricBarProps) {
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
            background: color ?? "linear-gradient(90deg, var(--secondary), var(--secondary-container))",
            transition: `width 800ms cubic-bezier(0.34, 1.56, 0.64, 1)`,
          }}
        />
      </div>
    </div>
  );
}
