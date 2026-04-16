import type { CefrLevel } from "./types";

const CEFR_ORDER: Record<CefrLevel, number> = {
  A1: 1,
  A2: 2,
  B1: 3,
  B2: 4,
  C1: 5,
  C2: 6,
};

export function cefrToNumber(level: CefrLevel): number {
  return CEFR_ORDER[level];
}

export function numberToCefr(n: number): CefrLevel {
  const rounded = Math.round(n);
  const clamped = Math.max(1, Math.min(6, rounded));
  const entries = Object.entries(CEFR_ORDER) as [CefrLevel, number][];
  return entries.find(([, v]) => v === clamped)![0];
}

export function isAboveLevel(wordLevel: CefrLevel, studentLevel: CefrLevel): boolean {
  return CEFR_ORDER[wordLevel] > CEFR_ORDER[studentLevel];
}

export const CEFR_LEVELS: CefrLevel[] = ["A1", "A2", "B1", "B2", "C1", "C2"];

// Background colors for highlighted words (used in ChunkCard)
export const cefrBgColors: Record<CefrLevel, string> = {
  A1: "rgba(64, 224, 208, 0.15)",
  A2: "rgba(64, 224, 208, 0.25)",
  B1: "rgba(255, 107, 157, 0.15)",
  B2: "rgba(255, 107, 157, 0.25)",
  C1: "rgba(18, 17, 17, 0.10)",
  C2: "rgba(18, 17, 17, 0.18)",
};

// Text colors for highlighted words
export const cefrTextColors: Record<CefrLevel, string> = {
  A1: "var(--secondary-fixed)",
  A2: "var(--secondary-fixed)",
  B1: "var(--primary)",
  B2: "var(--primary)",
  C1: "var(--tertiary)",
  C2: "var(--tertiary)",
};

// Bar gradient for MetricBar per CEFR level
export const cefrBarGradients: Record<CefrLevel, string> = {
  A1: "linear-gradient(90deg, #40E0D0, #B2F5EA)",
  A2: "linear-gradient(90deg, #1A9E8F, #40E0D0)",
  B1: "linear-gradient(90deg, #FF6B9D, #FFD6E4)",
  B2: "linear-gradient(90deg, #E0457B, #FF6B9D)",
  C1: "linear-gradient(90deg, #4A4744, #8A8582)",
  C2: "linear-gradient(90deg, #121111, #4A4744)",
};
