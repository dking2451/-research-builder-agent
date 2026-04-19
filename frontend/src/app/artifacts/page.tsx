import Link from "next/link";
import { Suspense } from "react";
import { apiGet } from "@/lib/api";
import type { Artifact, Project } from "@/lib/types";
import { ArtifactFilters } from "./ui";

function qs(params: Record<string, string | undefined>) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) u.set(k, v);
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}

export default async function ArtifactsPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const type = typeof searchParams.type === "string" ? searchParams.type : undefined;
  const q = typeof searchParams.q === "string" ? searchParams.q : undefined;
  const projectId = typeof searchParams.project_id === "string" ? searchParams.project_id : undefined;

  const items = await apiGet<Artifact[]>(`/artifacts/library${qs({ type, q, project_id: projectId })}`);
  const projects = await apiGet<Project[]>("/projects");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink-950">Artifact library</h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-700">Reports, memos, tables, prompt packs, code, and plans.</p>
      </div>

      <Suspense fallback={<div className="text-sm text-ink-700">Loading filters…</div>}>
        <ArtifactFilters projects={projects} initial={{ type, q, projectId }} />
      </Suspense>

      <div className="rounded-lg border border-paper-100 bg-white shadow-sm">
        <div className="border-b border-paper-100 px-4 py-3 text-sm font-semibold text-ink-950">Results</div>
        <ul className="divide-y divide-paper-100">
          {items.length === 0 ? (
            <li className="px-4 py-6 text-sm text-ink-700">No artifacts match these filters.</li>
          ) : (
            items.map((a) => (
              <li key={a.id} className="px-4 py-4">
                <Link href={`/artifacts/${a.id}`} className="text-sm font-semibold">
                  {a.title}
                </Link>
                <div className="text-xs text-ink-700">
                  {a.artifact_type} · {a.format}
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
