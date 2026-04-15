"use client";

import LessonCard from "./LessonCard";

const mockLessons = [
  { lessonName: "Lesson 1", date: "March 12, 2026", score: 2.1, cefrLabel: "A2" },
  { lessonName: "Lesson 2", date: "March 19, 2026", score: 2.0, cefrLabel: "A2" },
  { lessonName: "Lesson 3", date: "March 26, 2026", score: 2.4, cefrLabel: "A2" },
  { lessonName: "Lesson 4", date: "April 2, 2026", score: 2.6, cefrLabel: "B1" },
  { lessonName: "Lesson 5", date: "April 9, 2026", score: 2.8, cefrLabel: "B1" },
  { lessonName: "Lesson 6", date: "April 16, 2026", score: 3.1, cefrLabel: "B1" },
];

export default function LessonCards() {
  return (
    <section className="w-full">
      <h2 className="font-[family-name:var(--font-display)] text-[1.75rem] font-bold text-on-surface tracking-tight mb-8">
        Lesson History
      </h2>
      <div className="flex flex-col pb-16">
        {mockLessons.map((lesson, i) => (
          <LessonCard
            key={lesson.lessonName}
            index={i}
            total={mockLessons.length}
            lessonName={lesson.lessonName}
            date={lesson.date}
            score={lesson.score}
            cefrLabel={lesson.cefrLabel}
          />
        ))}
      </div>
    </section>
  );
}
