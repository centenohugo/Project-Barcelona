"use client";

import { createContext, useContext, useState, type ReactNode } from "react";

type StudentId = "Student-1" | "Student-2";

interface StudentContextValue {
  student: StudentId;
  setStudent: (s: StudentId) => void;
}

const StudentContext = createContext<StudentContextValue | null>(null);

export function StudentProvider({ children }: { children: ReactNode }) {
  const [student, setStudent] = useState<StudentId>("Student-1");
  return (
    <StudentContext.Provider value={{ student, setStudent }}>
      {children}
    </StudentContext.Provider>
  );
}

export function useStudent() {
  const ctx = useContext(StudentContext);
  if (!ctx) throw new Error("useStudent must be used within StudentProvider");
  return ctx;
}
