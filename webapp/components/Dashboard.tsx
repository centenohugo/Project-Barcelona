"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import ProgressChart, { mockData } from "./ProgressChart";
import MiniChart from "./MiniChart";

const vocabularyData = mockData.map((d) => ({ lesson: d.lesson, value: d.vocabulary }));
const grammarData = mockData.map((d) => ({ lesson: d.lesson, value: d.grammar }));
const fluencyData = mockData.map((d) => ({ lesson: d.lesson, value: d.fluency }));

function getProgressMessage(data: typeof mockData) {
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

const dropdownVariants = {
  hidden: { height: 0, opacity: 0, marginTop: 0 },
  visible: { height: "auto", opacity: 1, marginTop: 12 },
};

function ChartExplanation({ type }: { type: "total" | "vocabulary" | "grammar" | "fluency" }) {
  const explanations: Record<string, { title: string; body: string }> = {
    total: {
      title: "How is Total Progress calculated?",
      body: "Your total progress score is the weighted average of Vocabulary, Grammar, and Fluency scores across each lesson. It reflects your overall improvement trajectory.",
    },
    vocabulary: {
      title: "How is Vocabulary measured?",
      body: "Vocabulary is scored by analyzing the CEFR level of words you use. Higher-level words (B2+) contribute more to the score. Function words are excluded.",
    },
    grammar: {
      title: "How is Grammar measured?",
      body: "Grammar tracks sentence complexity and accuracy patterns across your lessons, measuring structural growth over time.",
    },
    fluency: {
      title: "How is Fluency measured?",
      body: "Fluency captures speech flow, lexical diversity, and consistency. It combines type-token ratio with contextual richness indicators.",
    },
  };

  const { title, body } = explanations[type];

  return (
    <motion.div
      variants={dropdownVariants}
      initial="hidden"
      animate="visible"
      exit="hidden"
      transition={{ duration: 0.25, ease: [0.34, 1.56, 0.64, 1] }}
      className="overflow-hidden"
    >
      <div className="rounded-xl bg-surface-low px-5 py-4">
        <p className="font-[family-name:var(--font-display)] text-sm font-semibold text-on-surface mb-1">
          {title}
        </p>
        <p className="font-[family-name:var(--font-body)] text-sm text-on-surface-variant leading-relaxed">
          {body}
        </p>
      </div>
    </motion.div>
  );
}

export default function Dashboard() {
  const progress = getProgressMessage(mockData);
  const [expanded, setExpanded] = useState<string | null>(null);

  const toggle = (key: string) => setExpanded((prev) => (prev === key ? null : key));

  return (
    <section className="w-full min-h-[calc(100vh-80px)] flex flex-col gap-6 justify-center">
      {/* Primary chart — center, bigger */}
      <motion.div
        whileHover={{ scale: 1.008 }}
        whileTap={{ scale: 0.998 }}
        transition={springTransition}
        onClick={() => toggle("total")}
        className="cursor-pointer"
      >
        <ProgressChart prominent />
        <AnimatePresence>
          {expanded === "total" && <ChartExplanation type="total" />}
        </AnimatePresence>
      </motion.div>
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
          Tap on any chart to see how it&apos;s calculated
        </motion.p>
      </div>
      {/* Secondary charts — top row */}
      <div className="grid grid-cols-3 gap-6">
        {([
          { key: "vocabulary", title: "Vocabulary", data: vocabularyData, color: "var(--secondary)" },
          { key: "grammar", title: "Grammar", data: grammarData, color: "var(--primary)" },
          { key: "fluency", title: "Fluency", data: fluencyData, color: "#8B5CF6" },
        ] as const).map(({ key, title, data, color }) => (
          <motion.div
            key={key}
            whileHover={{ scale: 1.015 }}
            whileTap={{ scale: 0.995 }}
            transition={springTransition}
            onClick={() => toggle(key)}
            className="cursor-pointer"
          >
            <MiniChart title={title} data={data} color={color} />
            <AnimatePresence>
              {expanded === key && <ChartExplanation type={key} />}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
