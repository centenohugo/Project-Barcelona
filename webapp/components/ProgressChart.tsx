"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import type { ProgressPoint } from "@/lib/mock-data";

interface ProgressChartProps {
  prominent?: boolean;
  data: ProgressPoint[];
}

const barColors = [
  "var(--primary)",         // pink
  "var(--secondary)",       // teal
  "var(--surface-variant)", // warm grey
];

export default function ProgressChart({ prominent = false, data }: ProgressChartProps) {
  const router = useRouter();
  const maxValue = Math.max(...data.map((d) => d.totalProgress), 0.1);

  return (
    <div className={`${prominent ? "p-10" : "p-8"} max-w-5xl mx-auto w-full`}>
      <h2
        className={`font-[family-name:var(--font-display)] font-bold text-on-surface tracking-tight ${
          prominent ? "text-[2rem] mb-8" : "text-[1.75rem] mb-6"
        }`}
      >
        Progress per Class
      </h2>
      <div
        className="flex items-end gap-3"
        style={{ height: prominent ? 240 : 180 }}
      >
        {data.map((point, index) => {
          const heightPct = (point.totalProgress / maxValue) * 100;
          return (
            <motion.div
              key={point.lesson}
              className="relative flex-1 rounded-t-xl cursor-pointer overflow-hidden"
              style={{ background: barColors[index % barColors.length] }}
              initial={{ height: 0 }}
              animate={{ height: `${heightPct}%` }}
              transition={{ duration: 0.8, delay: index * 0.08, ease: [0.34, 1.56, 0.64, 1] }}
              whileHover={{ scale: 1.06, y: -4 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => router.push(`/lesson/${index + 1}`)}
            >
              <span
                className="absolute inset-0 flex items-center justify-center font-[family-name:var(--font-display)] text-2xl font-extrabold select-none pointer-events-none"
                style={{ color: "rgba(28,27,26,0.15)" }}
              >
                {String(index + 1).padStart(2, "0")}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
