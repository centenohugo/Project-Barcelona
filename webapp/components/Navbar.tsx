"use client";

export default function Navbar() {
  return (
    <nav className="w-full sticky top-0 z-50 backdrop-blur-[24px]"
      style={{ background: "rgba(253, 251, 249, 0.8)" }}
    >
      <div className="max-w-6xl mx-auto flex items-center justify-between px-8 py-4">
        <span className="font-[family-name:var(--font-display)] text-xl font-extrabold tracking-tight text-on-surface">
          Charlies
        </span>
        <span className="text-sm text-on-surface-variant font-[family-name:var(--font-body)]">
          CEFR Progress Tracker
        </span>
      </div>
    </nav>
  );
}
