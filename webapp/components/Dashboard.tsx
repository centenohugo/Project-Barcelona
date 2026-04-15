"use client";

import ProgressChart from "./ProgressChart";
import MetricBars from "./MetricBars";

export default function Dashboard() {
  return (
    <section className="w-full flex gap-6">
      <ProgressChart />
      <MetricBars />
    </section>
  );
}
