"use client";

interface LessonCardProps {
  index: number;
  total: number;
  lessonName: string;
  date: string;
  score: number;
  cefrLabel: string;
}

export default function LessonCard({
  index,
  total,
  lessonName,
  date,
  score,
  cefrLabel,
}: LessonCardProps) {
  return (
    <button
      className="group relative w-full text-left rounded-2xl bg-surface-lowest px-8 py-6 cursor-pointer
        outline-none
        transition-all duration-300
        focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2
        hover:-translate-y-5 hover:scale-[1.02]
        focus-visible:-translate-y-5 focus-visible:scale-[1.02]"
      style={{
        zIndex: index,
        marginTop: index === 0 ? 0 : -48,
        transitionTimingFunction: "cubic-bezier(0.34, 1.56, 0.64, 1)",
        boxShadow: "0 2px 8px rgba(28,27,26,0.03)",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.zIndex = String(total + 10);
        e.currentTarget.style.boxShadow = "0 16px 32px rgba(28,27,26,0.06)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.zIndex = String(index);
        e.currentTarget.style.boxShadow = "0 2px 8px rgba(28,27,26,0.03)";
      }}
      onFocus={(e) => {
        e.currentTarget.style.zIndex = String(total + 10);
        e.currentTarget.style.boxShadow = "0 16px 32px rgba(28,27,26,0.06)";
      }}
      onBlur={(e) => {
        e.currentTarget.style.zIndex = String(index);
        e.currentTarget.style.boxShadow = "0 2px 8px rgba(28,27,26,0.03)";
      }}
    >
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <h3 className="font-[family-name:var(--font-display)] text-lg font-bold text-on-surface">
            {lessonName}
          </h3>
          <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
            {date}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex flex-col items-end gap-0.5">
            <span className="font-[family-name:var(--font-display)] text-2xl font-extrabold tracking-tight text-primary">
              {score.toFixed(1)}
            </span>
            <span className="text-xs font-medium uppercase tracking-[0.05em] text-on-surface-variant">
              {cefrLabel}
            </span>
          </div>
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold text-on-primary
              transition-transform duration-300 group-hover:scale-110"
            style={{
              background: "linear-gradient(135deg, var(--primary), var(--primary-container))",
              transitionTimingFunction: "cubic-bezier(0.34, 1.56, 0.64, 1)",
            }}
          >
            {cefrLabel}
          </div>
        </div>
      </div>
    </button>
  );
}
