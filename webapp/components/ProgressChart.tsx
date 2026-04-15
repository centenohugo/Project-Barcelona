"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

const mockData = [
  { lesson: "Lesson 1", vocabLevel: 1.8, lsi: 0.12, rootTtr: 6.2, uniqueWords: 95 },
  { lesson: "Lesson 2", vocabLevel: 2.1, lsi: 0.19, rootTtr: 7.9, uniqueWords: 133 },
  { lesson: "Lesson 3", vocabLevel: 2.0, lsi: 0.15, rootTtr: 5.3, uniqueWords: 99 },
  { lesson: "Lesson 4", vocabLevel: 2.4, lsi: 0.22, rootTtr: 8.1, uniqueWords: 148 },
  { lesson: "Lesson 5", vocabLevel: 2.6, lsi: 0.25, rootTtr: 8.8, uniqueWords: 162 },
];

const normalizeField = (data: typeof mockData, field: keyof (typeof mockData)[0]) => {
  const values = data.map((d) => d[field] as number);
  const max = Math.max(...values);
  const min = Math.min(...values);
  const range = max - min || 1;
  return data.map((d) => ((d[field] as number) - min) / range);
};

const compositeData = mockData.map((d, i) => {
  const normLsi = normalizeField(mockData, "lsi")[i];
  const normTtr = normalizeField(mockData, "rootTtr")[i];
  const normUnique = normalizeField(mockData, "uniqueWords")[i];
  const composite = (normLsi + normTtr + normUnique) / 3;
  return { ...d, composite: +(composite * 3 + 1).toFixed(2) };
});

export default function ProgressChart() {
  return (
    <div className="flex-1 min-w-0 rounded-2xl bg-surface-lowest p-8 pl-8 pr-6">
      <h2 className="font-[family-name:var(--font-display)] text-[1.75rem] font-bold text-on-surface tracking-tight mb-6">
        Vocabulary Progress
      </h2>
      <div className="h-[320px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={compositeData} margin={{ top: 8, right: 16, left: -8, bottom: 8 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="var(--surface-variant)"
              strokeOpacity={0.5}
            />
            <XAxis
              dataKey="lesson"
              tick={{ fontSize: 12, fill: "var(--on-surface-variant)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: "var(--on-surface-variant)" }}
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
            />
            <Legend
              wrapperStyle={{ fontSize: 12, fontFamily: "var(--font-body)" }}
            />

            {/* Sub-lines: individual metrics — thinner, muted */}
            <Line
              type="linear"
              dataKey="lsi"
              name="LSI"
              stroke="var(--secondary)"
              strokeWidth={1}
              strokeOpacity={0.35}
              dot={false}
              activeDot={{ r: 3 }}
            />
            <Line
              type="linear"
              dataKey="rootTtr"
              name="Root TTR"
              stroke="var(--secondary)"
              strokeWidth={1}
              strokeOpacity={0.25}
              strokeDasharray="6 4"
              dot={false}
              activeDot={{ r: 3 }}
            />
            <Line
              type="linear"
              dataKey="uniqueWords"
              name="Unique Words"
              stroke="var(--secondary)"
              strokeWidth={1}
              strokeOpacity={0.2}
              strokeDasharray="2 4"
              dot={false}
              activeDot={{ r: 3 }}
              yAxisId="right"
            />

            {/* Main line: vocab level — prominent */}
            <Line
              type="linear"
              dataKey="vocabLevel"
              name="Vocab Level"
              stroke="var(--primary)"
              strokeWidth={3}
              dot={{ r: 5, fill: "var(--primary)", strokeWidth: 2, stroke: "var(--surface-container-lowest)" }}
              activeDot={{ r: 7, fill: "var(--primary)" }}
              animationDuration={1200}
              animationEasing="ease-out"
            />

            <YAxis
              yAxisId="right"
              orientation="right"
              tick={{ fontSize: 11, fill: "var(--on-surface-variant)" }}
              tickLine={false}
              axisLine={false}
              hide
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
