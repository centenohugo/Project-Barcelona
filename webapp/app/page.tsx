import Navbar from "@/components/Navbar";
import Dashboard from "@/components/Dashboard";
import { loadVocabProgress } from "@/lib/progress-data";

export default function Home() {
  const vocabProgress = loadVocabProgress();

  return (
    <div className="flex flex-col flex-1 bg-surface">
      <Navbar />
      <main className="w-full max-w-6xl mx-auto flex flex-col gap-12 px-8 py-12">
        <Dashboard vocabProgress={vocabProgress} />
      </main>
      <footer className="py-8 text-center">
        <p className="font-[family-name:var(--font-body)] text-xs text-on-surface-variant/40 tracking-wide">
          hacked from the tree
        </p>
      </footer>
    </div>
  );
}
