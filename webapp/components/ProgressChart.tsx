"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import type { ProgressPoint } from "@/lib/mock-data";

interface ProgressChartProps {
  prominent?: boolean;
  data: ProgressPoint[];
}

export default function ProgressChart({ prominent = false, data }: ProgressChartProps) {
  const chartHeight = prominent ? 240 : 180;

  return (
    <div className={`rounded-2xl bg-surface-lowest ${prominent ? "p-10" : "p-8"} max-w-5xl mx-auto w-full`}>
      <h2
        className={`font-[family-name:var(--font-display)] font-bold text-on-surface tracking-tight ${
          prominent ? "text-[2rem] mb-8" : "text-[1.75rem] mb-6"
        }`}
      >
        Total Progress
      </h2>
      <div style={{ height: chartHeight }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 16, left: -8, bottom: 8 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--surface-variant)"
              strokeOpacity={0.5}
              vertical={false}
            />
            <XAxis
              dataKey="lesson"
              tick={{ fontSize: prominent ? 13 : 12, fill: "var(--on-surface-variant)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: prominent ? 13 : 12, fill: "var(--on-surface-variant)" }}
              tickLine={false}
              axisLine={false}
              domain={[0, "auto"]}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface-container-lowest)",
                border: "none",
                borderRadius: 12,
                boxShadow: "0 8px 32px rgba(28,27,26,0.06)",
                fontSize: 13,
              }}
              cursor={false}
            />
            <Bar
              dataKey="totalProgress"
              name="Total Progress"
              fill="var(--primary)"
              radius={[8, 8, 0, 0]}
              animationDuration={1200}
              animationEasing="ease-out"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
