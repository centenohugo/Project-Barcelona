"use client";

import LessonCard from "./LessonCard";
import { useStudent } from "@/lib/student-context";
import { studentsData } from "@/lib/mock-data";

export default function LessonCards() {
  const { student } = useStudent();
  const lessons = studentsData[student].lessons;

  return (
    <section id="lessons" className="w-full">
      <h2 className="font-[family-name:var(--font-display)] text-[1.75rem] font-bold text-on-surface tracking-tight mb-8">
        Lesson History
      </h2>
      <div
        className="flex items-end justify-center py-16 px-8 overflow-visible"
      >
        {lessons.map((lesson, i) => (
          <LessonCard
            key={lesson.id}
            index={i}
            total={lessons.length}
            lessonName={lesson.name}
            lessonId={lesson.id}
          />
        ))}
      </div>
    </section>
  );
}
