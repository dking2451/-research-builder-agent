import Link from "next/link";
import { apiGet } from "@/lib/api";
import { KnowledgeInlineList } from "@/components/knowledge/knowledge-inline-list";
import type { KnowledgeItem, Project } from "@/lib/types";
import { KnowledgeFilters } from "./ui";

function qs(params: Record<string, string | undefined>) {
  const u = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v) u.set(k, v);
  }
  const s = u.toString();
  return s ? `?${s}` : "";
}

export default async function KnowledgeLibraryPage({
  searchParams,
}: {
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const str = (k: string) => (typeof searchParams[k] === "string" ? (searchParams[k] as string) : undefined);
  const type = str("type");
  const tag = str("tag");
  const q = str("q");
  const projectId = str("project_id");
  const verification_status = str("verification_status");
  const sort = str("sort");
  const isPinned = str("is_pinned");
  const includeArchived = str("include_archived");

  const items = await apiGet<KnowledgeItem[]>(
    `/knowledge/library${qs({
      type,
      tag,
      q,
      project_id: projectId,
      verification_status,
      sort,
      is_pinned: isPinned === "true" ? "true" : undefined,
      include_archived: includeArchived === "true" ? "true" : undefined,
    })}`,
  );
  const projects = await apiGet<Project[]>("/projects");

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-ink-950">Knowledge library</h1>
        <p className="mt-2 max-w-2xl text-sm text-ink-700">
          Browse saved facts, findings, sources, and conclusions across projects. Use filters to narrow the list; inline
          actions update items in place.
        </p>
      </div>

      <KnowledgeFilters
        mode="library"
        projects={projects}
        initial={{
          type,
          tag,
          q,
          projectId,
          pinnedOnly: isPinned === "true",
          verification: verification_status,
          sort: sort ?? "newest",
          includeArchived: includeArchived === "true",
        }}
      />

      <div className="rounded-lg border border-paper-100 bg-white shadow-sm">
        <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-paper-100 px-4 py-3">
          <div className="text-sm font-semibold text-ink-950">Results</div>
          <div className="text-xs text-ink-600">{items.length} shown</div>
        </div>
        <KnowledgeInlineList variant="library" items={items} />
      </div>

      <div className="text-xs text-ink-600">
        <Link href="/projects" className="text-ink-800 underline-offset-2 hover:underline">
          Back to projects
        </Link>
      </div>
    </div>
  );
}
