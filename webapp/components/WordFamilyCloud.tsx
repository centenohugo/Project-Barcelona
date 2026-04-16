"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import type { DominantFamilyData } from "@/app/api/lesson/[studentId]/[lessonId]/dominant-family/route";

const CEFR_COLOR: Record<string, string> = {
  A1: "#6B7280", A2: "#1D4ED8", B1: "#065F46",
  B2: "#92400E", C1: "#991B1B", C2: "#5B21B6",
};
const CEFR_BG: Record<string, string> = {
  A1: "#F3F4F6", A2: "#DBEAFE", B1: "#D1FAE5",
  B2: "#FEF3C7", C1: "#FEE2E2", C2: "#EDE9FE",
};

interface WordFamilyCloudProps {
  studentId: string;
  lessonId: number;
  lessonName: string;
}

export default function WordFamilyCloud({ studentId, lessonId, lessonName }: WordFamilyCloudProps) {
  const [data, setData] = useState<DominantFamilyData | null>(null);
  const [imgError, setImgError] = useState(false);

  useEffect(() => {
    setData(null);
    setImgError(false);
    fetch(`/api/lesson/${studentId}/${lessonId}/dominant-family`)
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then((d: DominantFamilyData) => setData(d))
      .catch(() => setData(null));
  }, [studentId, lessonId]);

  const imgSrc = `/wordclouds/${studentId}_lesson-${lessonId}.png`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col gap-3"
    >
      {/* Cloud image */}
      <div
        className="w-full rounded-2xl overflow-hidden"
        style={{ border: "1px solid rgba(0,0,0,0.07)", background: "#fff" }}
      >
        {!imgError ? (
          <img
            src={imgSrc}
            alt={`Word family cloud for ${lessonName}`}
            className="w-full object-contain"
            style={{ display: "block", maxHeight: "240px" }}
            onError={() => setImgError(true)}
          />
        ) : (
          <div className="flex items-center justify-center h-40">
            <p className="text-xs text-on-surface-variant font-[family-name:var(--font-body)] italic">
              Cloud not generated yet
            </p>
          </div>
        )}
      </div>

      {/* Metadata — centred below the cloud */}
      {data && (
        <div className="flex flex-col items-center gap-1 pt-1">
          {/* Root word + CEFR badge */}
          <div className="flex items-center gap-2">
            <span
              className="px-2.5 py-0.5 rounded-lg text-[11px] font-semibold font-[family-name:var(--font-display)]"
              style={{ background: "var(--primary)", color: "var(--on-primary)" }}
            >
              {data.root}
            </span>
            <span
              className="px-2 py-0.5 rounded text-[10px] font-bold"
              style={{
                background: CEFR_BG[data.cefr_range[0]] ?? "#F3F4F6",
                color: CEFR_COLOR[data.cefr_range[0]] ?? "#374151",
              }}
            >
              {data.cefr_range[0] !== data.cefr_range[1]
                ? `${data.cefr_range[0]}–${data.cefr_range[1]}`
                : data.cefr_range[0]}
            </span>
          </div>

          {/* Large word count — primary comparison signal */}
          <div className="flex items-baseline gap-2 mt-1">
            <span
              className="font-[family-name:var(--font-display)] font-extrabold tracking-tight"
              style={{ fontSize: "3.5rem", color: "var(--primary)", lineHeight: 1 }}
            >
              {data.member_count}
            </span>
            <span className="text-sm font-semibold text-on-surface-variant font-[family-name:var(--font-body)]">
              word forms
            </span>
          </div>

          <span className="text-[11px] text-on-surface-variant font-[family-name:var(--font-body)]">
            {data.total_occurrences} total occurrences
          </span>
        </div>
      )}
    </motion.div>
  );
}
