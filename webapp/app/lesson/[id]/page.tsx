import Navbar from "@/components/Navbar";
import LessonDetail from "@/components/LessonDetail";
import { lessonsData } from "@/lib/mock-data";
import { notFound } from "next/navigation";

interface PageProps {
  params: Promise<{ id: string }>;
}

export default async function LessonPage({ params }: PageProps) {
  const { id } = await params;
  const lessonId = parseInt(id, 10);
  const lesson = lessonsData.find((l) => l.id === lessonId);

  if (!lesson) {
    notFound();
  }

  return (
    <div className="flex flex-col flex-1 bg-surface">
      <Navbar />
      <LessonDetail lesson={lesson} />
    </div>
  );
}
