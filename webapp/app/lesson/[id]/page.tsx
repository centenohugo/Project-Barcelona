"use client";

import { use, useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import LessonDetail from "@/components/LessonDetail";
import { useStudent } from "@/lib/student-context";
import { studentsData } from "@/lib/mock-data";
import type { RealLessonData } from "@/lib/types";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function LessonPage({ params }: PageProps) {
  const { id } = use(params);
  const lessonId = parseInt(id, 10);
  const { student } = useStudent();

  const [lessonData, setLessonData] = useState<RealLessonData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get lesson name from mock data for display
  const mockLesson = studentsData[student]?.lessons.find(
    (l) => l.id === lessonId
  );
  const lessonName = mockLesson?.name ?? `Lesson ${lessonId}`;

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetch(`/api/lesson/${student}/${lessonId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Not found (${res.status})`);
        return res.json();
      })
      .then((data: RealLessonData) => {
        setLessonData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [student, lessonId]);

  return (
    <div className="flex flex-col flex-1 bg-surface">
      <Navbar />
      {loading ? (
        <div className="w-full max-w-6xl mx-auto px-8 py-12 flex flex-col gap-6">
          {/* Skeleton loading */}
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="w-full rounded-2xl bg-surface-lowest p-8 flex gap-8 animate-pulse"
            >
              <div className="flex-1 space-y-3">
                <div className="h-3 w-32 rounded bg-surface-variant" />
                <div className="h-4 w-full rounded bg-surface-variant" />
                <div className="h-4 w-3/4 rounded bg-surface-variant" />
                <div className="h-4 w-5/6 rounded bg-surface-variant" />
              </div>
              <div className="w-[35%] space-y-4">
                {[1, 2, 3, 4, 5, 6].map((j) => (
                  <div key={j} className="space-y-2">
                    <div className="h-2 w-8 rounded bg-surface-variant" />
                    <div className="h-3 rounded-full bg-surface-variant" />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="w-full max-w-6xl mx-auto px-8 py-12">
          <div className="rounded-2xl bg-surface-lowest p-12 text-center">
            <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
              No vocabulary data available for this lesson yet.
            </p>
          </div>
        </div>
      ) : lessonData ? (
        <LessonDetail lesson={lessonData} lessonName={lessonName} studentId={student} lessonId={lessonId} />
      ) : null}
    </div>
  );
}
