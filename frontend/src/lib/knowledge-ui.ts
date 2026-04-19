/** Prompt-aligned knowledge kinds (V1). */
export const KNOWLEDGE_TYPES = [
  "fact",
  "claim",
  "note",
  "finding",
  "source",
  "summary",
  "conclusion",
  "output",
  "task",
  "question",
] as const;

export const KNOWLEDGE_SORT = [
  { value: "newest", label: "Newest" },
  { value: "importance", label: "Most important" },
  { value: "pinned_first", label: "Pinned first" },
] as const;

export const VERIFICATION_FILTER = [
  "",
  "unverified",
  "partially_verified",
  "verified",
  "disputed",
] as const;

export function canPromoteToFinding(type: string): boolean {
  const t = type.toLowerCase();
  return t !== "finding" && t !== "conclusion";
}

export function canPromoteToConclusion(type: string): boolean {
  const t = type.toLowerCase();
  if (t === "conclusion") return false;
  return ["finding", "claim", "fact", "summary", "note", "source"].includes(t);
}
