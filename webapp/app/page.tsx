import Navbar from "@/components/Navbar";
import Dashboard from "@/components/Dashboard";
import LessonCards from "@/components/LessonCards";

export default function Home() {
  return (
    <div className="flex flex-col flex-1 bg-surface">
      <Navbar />
      <main className="w-full max-w-6xl mx-auto flex flex-col gap-12 px-8 py-12">
        <Dashboard />
        <LessonCards />
      </main>
    </div>
  );
}
