"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import VocabularyComparison from "@/components/VocabularyComparison";
import { useStudent } from "@/lib/student-context";
import type { VocabularyApiResponse } from "@/lib/vocabulary-types";

export default function VocabularyPage() {
  const { student } = useStudent();
  const [data, setData] = useState<VocabularyApiResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);

    fetch(`/api/vocabulary/${student}`)
      .then((res) => {
        if (!res.ok) throw new Error(`Not found (${res.status})`);
        return res.json();
      })
      .then((json: VocabularyApiResponse) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [student]);

  return (
    <div className="flex flex-col flex-1 bg-surface">
      <Navbar />
      {loading ? (
        <div className="w-full max-w-6xl mx-auto px-8 py-12 flex flex-col gap-6">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="w-full rounded-2xl bg-surface-lowest p-8 animate-pulse"
            >
              <div className="space-y-3">
                <div className="h-3 w-32 rounded bg-surface-variant" />
                <div className="h-4 w-full rounded bg-surface-variant" />
                <div className="h-4 w-3/4 rounded bg-surface-variant" />
              </div>
            </div>
          ))}
        </div>
      ) : error ? (
        <div className="w-full max-w-6xl mx-auto px-8 py-12">
          <div className="rounded-2xl bg-surface-lowest p-12 text-center">
            <p className="text-on-surface-variant font-[family-name:var(--font-body)]">
              No vocabulary data available yet.
            </p>
          </div>
        </div>
      ) : data ? (
        <VocabularyComparison data={data} />
      ) : null}
    </div>
  );
}
