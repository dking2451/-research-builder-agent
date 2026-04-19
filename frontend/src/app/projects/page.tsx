import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { Project } from "@/lib/types";
import { CreateProjectForm } from "./ui";

export default async function ProjectsPage() {
  const projects = await apiGet<Project[]>("/projects");

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-ink-950">Projects</h1>
          <p className="mt-2 max-w-2xl text-sm text-ink-700">Workspaces for research, decisions, builds, and learning.</p>
        </div>
      </div>

      <CreateProjectForm />

      <div className="rounded-lg border border-paper-100 bg-white shadow-sm">
        <div className="border-b border-paper-100 px-4 py-3 text-sm font-semibold text-ink-950">All projects</div>
        <ul className="divide-y divide-paper-100">
          {projects.length === 0 ? (
            <li className="px-4 py-6 text-sm text-ink-700">No projects yet — create one above.</li>
          ) : (
            projects.map((p) => (
              <li key={p.id} className="px-4 py-4">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <Link href={`/projects/${p.id}`} className="text-sm font-semibold">
                      {p.title}
                    </Link>
                    <div className="text-xs text-ink-700">
                      {p.status}
                      {p.goal ? ` · ${p.goal.slice(0, 120)}${p.goal.length > 120 ? "…" : ""}` : ""}
                    </div>
                  </div>
                  <div className="text-xs text-ink-700">{new Date(p.updated_at).toLocaleString()}</div>
                </div>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
