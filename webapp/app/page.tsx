import Dashboard from "@/components/Dashboard";
import LessonCards from "@/components/LessonCards";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center bg-surface">
      <main className="w-full max-w-6xl flex flex-col gap-12 px-8 py-12">
        {/* Section 1: Charts + Metric Bars */}
        <Dashboard />

        {/* Section 2: Stacked Lesson Cards */}
        <LessonCards />
      </main>
    </div>
  );
}
