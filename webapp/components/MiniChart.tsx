"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface MiniChartProps {
  title: string;
  data: { lesson: string; value: number }[];
  color: string;
}

export default function MiniChart({ title, data, color }: MiniChartProps) {
  return (
    <div className="rounded-2xl bg-surface-lowest p-6">
      <h3 className="font-[family-name:var(--font-display)] text-base font-bold text-on-surface tracking-tight mb-4">
        {title}
      </h3>
      <div className="h-[160px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 8, left: -24, bottom: 4 }}>
            <XAxis
              dataKey="lesson"
              tick={{ fontSize: 10, fill: "var(--on-surface-variant)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 10, fill: "var(--on-surface-variant)" }}
              tickLine={false}
              axisLine={false}
              domain={[0, "auto"]}
            />
            <Tooltip
              contentStyle={{
                background: "var(--surface-container-lowest)",
                border: "none",
                borderRadius: 10,
                boxShadow: "0 6px 24px rgba(28,27,26,0.06)",
                fontSize: 12,
              }}
              cursor={false}
            />
            <Bar
              dataKey="value"
              name={title}
              fill={color}
              radius={[6, 6, 0, 0]}
              animationDuration={1000}
              animationEasing="ease-out"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
