import Link from "next/link";
import { apiGet } from "@/lib/api";
import type { SearchHit } from "@/lib/types";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const q = typeof searchParams.q === "string" ? searchParams.q : "";
  const hits = q ? await apiGet<SearchHit[]>(`/search?q=${encodeURIComponent(q)}`) : [];

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink-950">Search</h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-700">Basic full-text-ish search across projects, knowledge, artifacts, and messages.</p>
      </div>

      <form className="flex gap-2" action="/search" method="get">
        <input
          name="q"
          defaultValue={q}
          placeholder="Search…"
          className="w-full rounded-md border border-paper-100 bg-white px-3 py-2 text-sm outline-none focus:border-accent-600"
        />
        <button className="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white" type="submit">
          Search
        </button>
      </form>

      {!q ? (
        <div className="text-sm text-ink-700">Enter a query to search.</div>
      ) : (
        <div className="rounded-lg border border-paper-100 bg-white shadow-sm">
          <div className="border-b border-paper-100 px-4 py-3 text-sm font-semibold text-ink-950">Results</div>
          <ul className="divide-y divide-paper-100">
            {hits.length === 0 ? (
              <li className="px-4 py-6 text-sm text-ink-700">No hits.</li>
            ) : (
              hits.map((h) => (
                <li key={`${h.entity}:${h.id}`} className="px-4 py-4">
                  <div className="text-xs text-ink-700">
                    {h.entity}
                    {h.project_id ? (
                      <>
                        {" "}
                        ·{" "}
                        <Link className="font-mono" href={`/projects/${h.project_id}`}>
                          project
                        </Link>
                      </>
                    ) : null}
                  </div>
                  <div className="mt-1 text-sm font-semibold text-ink-950">{h.title}</div>
                  <div className="mt-2 text-sm text-ink-800">{h.snippet}</div>
                  <div className="mt-2 text-xs">
                    {h.entity === "knowledge" ? (
                      <Link href={`/knowledge/${h.id}`}>Open</Link>
                    ) : h.entity === "artifact" ? (
                      <Link href={`/artifacts/${h.id}`}>Open</Link>
                    ) : h.entity === "project" ? (
                      <Link href={`/projects/${h.id}`}>Open</Link>
                    ) : (
                      <span className="text-ink-700">message hit (open the project conversation)</span>
                    )}
                  </div>
                </li>
              ))
            )}
          </ul>
        </div>
      )}
    </div>
  );
}
