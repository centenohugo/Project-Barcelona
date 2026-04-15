"use client";

import Link from "next/link";
import { motion, useMotionValue, useTransform, useSpring } from "framer-motion";

interface LessonCardProps {
  index: number;
  total: number;
  lessonName: string;
}

export default function LessonCard({
  index,
  total,
  lessonName,
}: LessonCardProps) {
  const hovered = useMotionValue(0);
  const textOpacity = useSpring(hovered, { stiffness: 300, damping: 25 });
  const textX = useTransform(textOpacity, [0, 1], [-8, 0]);
  const badgeScale = useTransform(textOpacity, [0, 1], [0.9, 1]);
  const badgeOpacity = useTransform(textOpacity, [0, 1], [0.35, 1]);

  return (
    <Link href={`/lesson/${index + 1}`} className="outline-none" tabIndex={-1}>
      <motion.div
        className="group relative w-full text-left rounded-2xl bg-surface-lowest px-8 py-6 cursor-pointer outline-none
          focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2"
        style={{
          zIndex: index,
          marginTop: index === 0 ? 0 : -48,
        }}
        tabIndex={0}
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{
          delay: index * 0.08,
          duration: 0.5,
          ease: [0.34, 1.56, 0.64, 1],
        }}
        whileHover={{
          y: -20,
          scale: 1.02,
          zIndex: total + 10,
          boxShadow: "0 20px 40px rgba(28,27,26,0.08)",
          transition: { duration: 0.35, ease: [0.34, 1.56, 0.64, 1] },
        }}
        whileFocus={{
          y: -20,
          scale: 1.02,
          zIndex: total + 10,
          boxShadow: "0 20px 40px rgba(28,27,26,0.08)",
          transition: { duration: 0.35, ease: [0.34, 1.56, 0.64, 1] },
        }}
        whileTap={{ scale: 0.98 }}
        onHoverStart={() => hovered.set(1)}
        onHoverEnd={() => hovered.set(0)}
        onFocus={() => hovered.set(1)}
        onBlur={() => hovered.set(0)}
      >
        <div className="flex items-center justify-between">
          <motion.h3
            className="font-[family-name:var(--font-display)] text-lg font-bold text-on-surface"
            style={{ opacity: textOpacity, x: textX }}
          >
            {lessonName}
          </motion.h3>

          <motion.div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold text-on-primary"
            style={{
              background: "linear-gradient(135deg, var(--primary), var(--primary-container))",
              opacity: badgeOpacity,
              scale: badgeScale,
            }}
          >
            {index + 1}
          </motion.div>
        </div>
      </motion.div>
    </Link>
  );
}
