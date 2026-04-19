import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { DashboardSummary } from "@/lib/types";

export default async function DashboardPage() {
  let data: DashboardSummary | null = null;
  let error: string | null = null;
  try {
    data = await apiGet<DashboardSummary>("/dashboard");
  } catch (e) {
    error = e instanceof Error ? e.message : "Failed to load dashboard";
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-900">
        <div className="font-semibold">Could not reach the API</div>
        <div className="mt-2 whitespace-pre-wrap">{error}</div>
        <div className="mt-3 text-xs text-red-800">
          Start the backend (`uvicorn app.main:app --reload` from `backend/`) and ensure `NEXT_PUBLIC_API_URL` matches.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink-950">Dashboard</h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-700">
          Capture questions, run workflows, and accumulate structured knowledge over time.
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <Link
          href="/projects"
          className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm no-underline hover:border-accent-600"
        >
          <div className="text-sm font-semibold text-ink-950">Projects</div>
          <div className="mt-1 text-xs text-ink-700">Create a workspace for a topic, decision, build, or learning goal.</div>
        </Link>
        <Link
          href="/knowledge"
          className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm no-underline hover:border-accent-600"
        >
          <div className="text-sm font-semibold text-ink-950">Knowledge library</div>
          <div className="mt-1 text-xs text-ink-700">Browse saved facts, findings, sources, and conclusions.</div>
        </Link>
        <Link
          href="/artifacts"
          className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm no-underline hover:border-accent-600"
        >
          <div className="text-sm font-semibold text-ink-950">Artifact library</div>
          <div className="mt-1 text-xs text-ink-700">Open reports, memos, plans, prompt packs, and code snippets.</div>
        </Link>
      </div>

      <section className="grid gap-6 lg:grid-cols-3">
        <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
          <div className="text-sm font-semibold text-ink-950">Recent projects</div>
          <ul className="mt-3 space-y-2 text-sm">
            {data!.recent_projects.length === 0 ? (
              <li className="text-ink-700">No projects yet.</li>
            ) : (
              data!.recent_projects.map((p) => (
                <li key={p.id}>
                  <Link href={`/projects/${p.id}`} className="font-medium">
                    {p.title}
                  </Link>
                  <div className="text-xs text-ink-700">{p.status}</div>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
          <div className="text-sm font-semibold text-ink-950">Recent knowledge</div>
          <ul className="mt-3 space-y-2 text-sm">
            {data!.recent_knowledge.length === 0 ? (
              <li className="text-ink-700">No knowledge items yet.</li>
            ) : (
              data!.recent_knowledge.map((k) => (
                <li key={k.id}>
                  <Link href={`/knowledge/${k.id}`} className="font-medium">
                    {k.title}
                  </Link>
                  <div className="text-xs text-ink-700">
                    {k.type} · project {k.project_id.slice(0, 8)}…
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>

        <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
          <div className="text-sm font-semibold text-ink-950">Recent artifacts</div>
          <ul className="mt-3 space-y-2 text-sm">
            {data!.recent_artifacts.length === 0 ? (
              <li className="text-ink-700">No artifacts yet.</li>
            ) : (
              data!.recent_artifacts.map((a) => (
                <li key={a.id}>
                  <Link href={`/artifacts/${a.id}`} className="font-medium">
                    {a.title}
                  </Link>
                  <div className="text-xs text-ink-700">{a.artifact_type}</div>
                </li>
              ))
            )}
          </ul>
        </div>
      </section>
    </div>
  );
}
