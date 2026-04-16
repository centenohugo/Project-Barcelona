"use client";

import Link from "next/link";
import { motion } from "framer-motion";

const sleeveColors = [
  "var(--primary)",           // #FF6B9D — pink
  "var(--secondary)",         // #40E0D0 — teal
  "var(--surface-variant)",   // #E0DBD6 — warm grey
];

interface LessonCardProps {
  index: number;
  total: number;
  lessonName: string;
  lessonId: number;
}

export default function LessonCard({ index, total, lessonName, lessonId }: LessonCardProps) {
  const bg = sleeveColors[index % sleeveColors.length];

  return (
    <Link href={`/lesson/${lessonId}`} className="outline-none shrink-0" tabIndex={-1}>
      <motion.div
        className="relative flex flex-col justify-end rounded-2xl cursor-pointer outline-none
          focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
        style={{
          width: 200,
          height: 260,
          background: bg,
          marginLeft: index === 0 ? 0 : -32,
          zIndex: index,
        }}
        tabIndex={0}
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          delay: index * 0.07,
          duration: 0.6,
          ease: [0.34, 1.56, 0.64, 1],
        }}
        whileHover={{
          y: -8,
          scale: 1.04,
          zIndex: total + 10,
          transition: { duration: 0.3, ease: [0.34, 1.56, 0.64, 1] },
        }}
        whileFocus={{
          y: -8,
          scale: 1.04,
          zIndex: total + 10,
          transition: { duration: 0.3, ease: [0.34, 1.56, 0.64, 1] },
        }}
        whileTap={{ scale: 0.97 }}
      >
        {/* Number — editorial display */}
        <div className="absolute top-6 left-7">
          <span
            className="font-[family-name:var(--font-display)] text-[3.5rem] font-extrabold leading-none"
            style={{ color: "rgba(28,27,26,0.10)" }}
          >
            {String(index + 1).padStart(2, "0")}
          </span>
        </div>

        {/* Label */}
        <div className="px-7 pb-6">
          <span
            className="font-[family-name:var(--font-display)] text-base font-bold"
            style={{ color: "rgba(28,27,26,0.7)" }}
          >
            {lessonName}
          </span>
        </div>

      </motion.div>
    </Link>
  );
}
