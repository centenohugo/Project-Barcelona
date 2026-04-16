"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import ProgressChart from "./ProgressChart";
import MiniChart from "./MiniChart";
import { useStudent } from "@/lib/student-context";
import { studentsData, type ProgressPoint } from "@/lib/mock-data";
import type { VocabProgress } from "@/lib/progress-data";

function getProgressMessage(data: ProgressPoint[]) {
  if (data.length < 2) return { text: "Start your journey", trend: "neutral" as const };
  const last = data[data.length - 1].totalProgress;
  const prev = data[data.length - 2].totalProgress;
  const diff = last - prev;
  if (diff > 0.15) return { text: "You're making great progress!", trend: "positive" as const };
  if (diff < -0.15) return { text: "Let's get back on track", trend: "negative" as const };
  return { text: "Holding steady \u2014 consistency is key", trend: "neutral" as const };
}

const trendColors = {
  positive: "var(--secondary)",
  negative: "var(--primary)",
  neutral: "var(--on-surface-variant)",
};

const springTransition = {
  type: "spring" as const,
  stiffness: 300,
  damping: 24,
};

interface DashboardProps {
  vocabProgress: VocabProgress;
}

export default function Dashboard({ vocabProgress }: DashboardProps) {
  const { student } = useStudent();
  const progressData = studentsData[student].progress;
  const router = useRouter();

  const vocabForStudent = vocabProgress[student] ?? [];
  const vocabularyData = vocabForStudent.map((d) => ({ lesson: d.lesson, value: d.vocabScore }));
  const grammarData = progressData.map((d) => ({ lesson: d.lesson, value: d.grammar }));
  const fluencyData = progressData.map((d) => ({ lesson: d.lesson, value: d.fluency }));

  const progress = getProgressMessage(progressData);

  return (
    <section className="w-full min-h-[calc(100vh-80px)] flex flex-col gap-6 justify-center">
      {/* Primary chart — center, bigger */}
      <div>
        <ProgressChart prominent data={progressData} />
      </div>
      {/* Progress status text */}
      <div className="flex flex-col items-center gap-1 pt-2">
        <motion.p
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.5 }}
          className="font-[family-name:var(--font-display)] text-2xl font-bold tracking-tight"
          style={{ color: trendColors[progress.trend] }}
        >
          {progress.text}
        </motion.p>
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.6, duration: 0.4 }}
          className="font-[family-name:var(--font-body)] text-sm text-on-surface-variant"
        >
          Tap a chart below to compare lessons
        </motion.p>
      </div>
      {/* Secondary charts — bottom row */}
      <div className="grid grid-cols-3 gap-6">
        {([
          { key: "vocabulary", title: "Vocabulary", data: vocabularyData, color: "var(--secondary)", domain: [0, 100] as [number, number] },
          { key: "grammar", title: "Grammar", data: grammarData, color: "var(--primary)", domain: undefined },
          { key: "fluency", title: "Fluency", data: fluencyData, color: "#8B5CF6", domain: undefined },
        ]).map(({ key, title, data, color, domain }) => (
          <motion.div
            key={key}
            whileHover={{ scale: 1.015 }}
            whileTap={{ scale: 0.995 }}
            transition={springTransition}
            onClick={() => router.push(`/compare/${key}`)}
            className="cursor-pointer"
          >
            <MiniChart title={title} data={data} color={color} domain={domain} />
          </motion.div>
        ))}
      </div>
    </section>
  );
}
