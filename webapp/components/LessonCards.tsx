"use client";

import LessonCard from "./LessonCard";

const mockLessons = [
  "Lesson 1",
  "Lesson 2",
  "Lesson 3",
];

export default function LessonCards() {
  return (
    <section id="lessons" className="w-full">
      <h2 className="font-[family-name:var(--font-display)] text-[1.75rem] font-bold text-on-surface tracking-tight mb-8">
        Lesson History
      </h2>
      <div
        className="flex items-end justify-center py-16 px-8 overflow-visible"
        style={{ perspective: "1200px" }}
      >
        {mockLessons.map((name, i) => (
          <LessonCard
            key={name}
            index={i}
            total={mockLessons.length}
            lessonName={name}
          />
        ))}
      </div>
    </section>
  );
}
