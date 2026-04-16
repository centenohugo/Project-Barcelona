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

export const mockData = [
  { lesson: "L1", totalProgress: 1.8, vocabulary: 1.6, grammar: 2.0, fluency: 1.9 },
  { lesson: "L2", totalProgress: 2.1, vocabulary: 2.0, grammar: 2.1, fluency: 2.2 },
  { lesson: "L3", totalProgress: 2.0, vocabulary: 1.9, grammar: 2.2, fluency: 1.8 },
  { lesson: "L4", totalProgress: 2.4, vocabulary: 2.3, grammar: 2.4, fluency: 2.5 },
  { lesson: "L5", totalProgress: 2.6, vocabulary: 2.5, grammar: 2.7, fluency: 2.7 },
];

interface ProgressChartProps {
  prominent?: boolean;
}

export default function ProgressChart({ prominent = false }: ProgressChartProps) {
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
          <BarChart data={mockData} margin={{ top: 8, right: 16, left: -8, bottom: 8 }}>
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
