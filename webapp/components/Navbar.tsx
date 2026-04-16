"use client";

import { motion } from "framer-motion";
import { useStudent } from "@/lib/student-context";

const students = ["Student-1", "Student-2"] as const;

export default function Navbar() {
  const { student, setStudent } = useStudent();

  return (
    <nav className="w-full sticky top-0 z-50 backdrop-blur-[24px]"
      style={{ background: "rgba(253, 251, 249, 0.8)" }}
    >
      <div className="max-w-6xl mx-auto grid grid-cols-3 items-center px-8 py-4">
        <span className="font-[family-name:var(--font-display)] text-xl font-extrabold tracking-tight text-on-surface">
          Charlies
        </span>

        {/* Student toggle */}
        <div className="flex gap-1 rounded-2xl p-1 justify-self-center">
          {students.map((s) => (
            <button
              key={s}
              onClick={() => setStudent(s)}
              className="relative px-5 py-2 rounded-xl text-sm font-medium transition-colors duration-200 cursor-pointer outline-none focus-visible:ring-2 focus-visible:ring-primary/40"
              style={{
                fontFamily: "var(--font-body)",
                color: student === s ? "var(--on-primary)" : "var(--on-surface-variant)",
              }}
            >
              {student === s && (
                <motion.div
                  layoutId="studentToggle"
                  className="absolute inset-0 rounded-xl"
                  style={{ background: "var(--primary)" }}
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <span className="relative z-10">{s.replace("-", " ")}</span>
            </button>
          ))}
        </div>

        <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)] justify-self-end">
          CEFR Progress Tracker
        </span>
      </div>
    </nav>
  );
}
