"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LabelList,
  Customized,
} from "recharts";

interface MiniChartProps {
  title: string;
  data: { lesson: string; value: number }[];
  color: string;
  domain?: [number, number]; // kept for API compat, not used for axis
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type BarDatum = { x: number; y: number; width: number; height: number; value: number };

export default function MiniChart({ title, data, color }: MiniChartProps) {
  // Enrich data with % change vs previous lesson
  const enriched = data.map((d, i) => ({
    ...d,
    pct:
      i === 0
        ? null
        : Math.round(((d.value - data[i - 1].value) / data[i - 1].value) * 100),
  }));

  // Custom SVG trend line drawn over bars (no tooltip/legend pollution)
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function TrendLine({ formattedGraphicalItems }: { formattedGraphicalItems?: any[] }) {
    const barItem = formattedGraphicalItems?.[0];
    const pts: { x: number; y: number }[] = (barItem?.props?.data ?? [])
      .map((d: BarDatum) => ({ x: d.x + d.width / 2, y: d.y }))
      .filter((p: { x: number; y: number }) => isFinite(p.x) && isFinite(p.y));

    if (pts.length < 2) return null;

    const polyPts = pts.map((p) => `${p.x},${p.y}`).join(" ");

    return (
      <>
        <polyline
          points={polyPts}
          fill="none"
          stroke={color}
          strokeWidth={2.5}
          strokeLinecap="round"
          strokeLinejoin="round"
          opacity={0.9}
        />
        {pts.map((p, i) => (
          <circle key={i} cx={p.x} cy={p.y} r={4} fill={color} />
        ))}
      </>
    );
  }

  // % change label rendered above each bar (skipped for the first bar)
  function PctLabel(props: {
    x?: number;
    y?: number;
    width?: number;
    value?: number | null;
  }) {
    const { x = 0, y = 0, width = 0, value } = props;
    if (value === null || value === undefined) return <g />;
    const isPos = value > 0;
    const isNeg = value < 0;
    const fill = isPos ? "#059669" : isNeg ? "#DC2626" : "#6B7280";
    return (
      <text
        x={x + width / 2}
        y={y - 7}
        textAnchor="middle"
        fontSize={10}
        fontWeight="700"
        fill={fill}
      >
        {isPos ? "+" : ""}
        {value}%
      </text>
    );
  }

  return (
    <div className="rounded-2xl bg-surface-lowest p-6">
      <h3 className="font-[family-name:var(--font-display)] text-base font-bold text-on-surface tracking-tight mb-4">
        {title}
      </h3>
      <div className="h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={enriched} margin={{ top: 28, right: 4, left: 4, bottom: 4 }}>
            <XAxis
              dataKey="lesson"
              tick={{ fontSize: 11, fill: "var(--on-surface-variant)" }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis hide domain={[0, "dataMax"]} />
            <Tooltip
              contentStyle={{
                background: "var(--surface-container-lowest)",
                border: "none",
                borderRadius: 10,
                boxShadow: "0 6px 24px rgba(28,27,26,0.06)",
                fontSize: 12,
              }}
              formatter={(value: number) => [value.toFixed(1), title]}
              cursor={false}
            />
            <Bar
              dataKey="value"
              name={title}
              fill={color}
              fillOpacity={0.4}
              radius={[8, 8, 0, 0]}
              animationDuration={1000}
              animationEasing="ease-out"
            >
              <LabelList dataKey="pct" content={PctLabel} />
            </Bar>
            {/* Trend line overlay — drawn as pure SVG, invisible to tooltip */}
            <Customized component={TrendLine} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
