import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

interface FamilyMember {
  word: string;
  occurrences: number;
  cefr_level: string;
}

export interface DominantFamilyData {
  root: string;
  method: string;
  members: FamilyMember[];
  member_count: number;
  total_occurrences: number;
  avg_cefr_numeric: number;
  cefr_range: [string, string];
}

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ studentId: string; lessonId: string }> }
) {
  const { studentId, lessonId } = await params;
  const lessonKey = `lesson-${lessonId}`;
  const projectRoot = path.join(process.cwd(), "..");

  const filePath = path.join(
    projectRoot,
    "data",
    "processed",
    studentId,
    lessonKey,
    "vocabulary",
    "dominant_family.json"
  );

  try {
    const raw = fs.readFileSync(filePath, "utf-8");
    const parsed = JSON.parse(raw);
    const family: DominantFamilyData = parsed.dominant_family;
    if (!family) {
      return NextResponse.json({ error: "No dominant family found" }, { status: 404 });
    }
    return NextResponse.json(family);
  } catch {
    return NextResponse.json({ error: "Dominant family data not found" }, { status: 404 });
  }
}
