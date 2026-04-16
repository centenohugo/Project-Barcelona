"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import ChunkCard from "./ChunkCard";
import type { LessonData } from "@/lib/mock-data";

const tabs = ["Vocabulary", "Grammar", "Fluency"] as const;
type Tab = (typeof tabs)[number];

interface LessonDetailProps {
  lesson: LessonData;
}

export default function LessonDetail({ lesson }: LessonDetailProps) {
  const [activeTab, setActiveTab] = useState<Tab>("Vocabulary");

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col gap-8 px-8 py-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/#lessons"
            className="w-10 h-10 rounded-xl flex items-center justify-center text-on-surface-variant transition-colors"
            style={{ background: "var(--surface-container)" }}
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M12.5 15L7.5 10L12.5 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </Link>
          <motion.h1
            className="font-[family-name:var(--font-display)] text-[2rem] font-extrabold text-on-surface tracking-tight"
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.4, ease: [0.34, 1.56, 0.64, 1] }}
          >
            {lesson.name}
          </motion.h1>
        </div>

        {/* Toggle buttons */}
        <div className="flex gap-1 rounded-2xl p-1" style={{ background: "var(--surface-container)" }}>
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className="relative px-5 py-2 rounded-xl text-sm font-medium transition-colors duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
              style={{
                fontFamily: "var(--font-body)",
                color: activeTab === tab ? "var(--on-primary)" : "var(--on-surface-variant)",
              }}
            >
              {activeTab === tab && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 rounded-xl"
                  style={{ background: "var(--primary)" }}
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span className="relative z-10">{tab}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Chunks */}
      {lesson.chunks.length > 0 ? (
        <motion.div
          key={activeTab}
          className="flex flex-col gap-6"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          {lesson.chunks.map((chunk, i) => (
            <ChunkCard key={chunk.topic} chunk={chunk} index={i} />
          ))}
        </motion.div>
      ) : (
        <div className="rounded-2xl bg-surface-lowest p-12 text-center">
          <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
            No conversation data available for this lesson yet.
          </p>
        </div>
      )}
    </div>
  );
}
