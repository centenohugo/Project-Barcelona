# Webapp — Charlies CEFR Progress Tracker

## Stack
- Next.js 16 (App Router) + TypeScript
- Tailwind CSS with custom design tokens (see `globals.css`)
- Recharts for data visualization
- Framer Motion for animations

## Design System
See `DESIGN.md` for the full design system ("The Kinetic Editorial").
- **Primary:** #FF6B9D (Vibrant Pink) — energy, active learning, hero data
- **Secondary:** #40E0D0 (Vibrant Teal) — growth, success, milestones
- **Fonts:** Plus Jakarta Sans (headings), Inter (body) — loaded via `next/font/google` in `app/layout.tsx`
- **No-Line Rule:** No 1px borders. Use background color shifts for boundaries.
- **Springy easing:** `cubic-bezier(0.34, 1.56, 0.64, 1)` for animations

## Project Structure
```
app/
  layout.tsx          — Root layout (fonts, metadata)
  page.tsx            — Landing page (Dashboard + LessonCards)
  globals.css         — Tailwind + CSS custom properties (design tokens)
  lesson/[id]/page.tsx — Lesson detail page

components/
  Navbar.tsx          — Sticky glassmorphism navbar
  Dashboard.tsx       — Section 1: ProgressChart + MetricBars
  ProgressChart.tsx   — Recharts LineChart (vocab_level + sub-metrics)
  MetricBars.tsx      — Dashboard horizontal bars (uses MetricBar)
  MetricBar.tsx       — Reusable animated horizontal bar component
  LessonCards.tsx     — Section 2: stacked lesson card list
  LessonCard.tsx      — Individual lesson card with Framer Motion (links to /lesson/[id])
  LessonDetail.tsx    — Lesson detail view with conversation chunks
  ChunkCard.tsx       — Conversation chunk: highlighted text + metric bars

lib/
  mock-data.ts        — Hardcoded lesson/chunk data (to be replaced with real data later)
```

## Data Flow
Currently all data is hardcoded in `lib/mock-data.ts`. The real data will come from:
- `progress/Student-X_lesson-Y_progress.json` — per-lesson metrics
- `progress/Student-X_history.json` — cross-lesson scores and vocabulary
- `output/Student-X_lesson-Y_NN_contextual.json` — word-level CEFR classifications

## Running
```bash
npm run dev    # http://localhost:3000
```
