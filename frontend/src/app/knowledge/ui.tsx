"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { KNOWLEDGE_SORT, KNOWLEDGE_TYPES, VERIFICATION_FILTER } from "@/lib/knowledge-ui";
import type { Project } from "@/lib/types";

export type KnowledgeFilterInitial = {
  type?: string;
  tag?: string;
  q?: string;
  projectId?: string;
  pinnedOnly?: boolean;
  verification?: string;
  sort?: string;
  includeArchived?: boolean;
};

function buildQuery(params: {
  type: string;
  tag: string;
  q: string;
  projectId: string;
  pinnedOnly: boolean;
  verification: string;
  sort: string;
  includeArchived: boolean;
}): string {
  const u = new URLSearchParams();
  const set = (k: string, v: string) => {
    const t = v.trim();
    if (!t) u.delete(k);
    else u.set(k, t);
  };
  set("type", params.type);
  set("tag", params.tag);
  set("q", params.q);
  set("project_id", params.projectId);
  if (params.pinnedOnly) u.set("is_pinned", "true");
  set("verification_status", params.verification);
  set("sort", params.sort);
  if (params.includeArchived) u.set("include_archived", "true");
  const s = u.toString();
  return s ? `?${s}` : "";
}

export function KnowledgeFilters(props: {
  mode: "library" | "project";
  projects?: Project[];
  initial: KnowledgeFilterInitial;
  onProjectApply?: (queryString: string) => void;
}) {
  const router = useRouter();
  const [type, setType] = useState(props.initial.type ?? "");
  const [tag, setTag] = useState(props.initial.tag ?? "");
  const [q, setQ] = useState(props.initial.q ?? "");
  const [projectId, setProjectId] = useState(props.initial.projectId ?? "");
  const [pinnedOnly, setPinnedOnly] = useState(Boolean(props.initial.pinnedOnly));
  const [verification, setVerification] = useState(props.initial.verification ?? "");
  const [sort, setSort] = useState(props.initial.sort ?? "newest");
  const [includeArchived, setIncludeArchived] = useState(Boolean(props.initial.includeArchived));

  const query = useMemo(() => {
    return buildQuery({
      type,
      tag,
      q,
      projectId,
      pinnedOnly,
      verification,
      sort,
      includeArchived,
    });
  }, [type, tag, q, projectId, pinnedOnly, verification, sort, includeArchived]);

  function apply() {
    if (props.mode === "library") {
      router.push(`/knowledge${query}`);
    } else {
      props.onProjectApply?.(query);
    }
  }

  function reset() {
    setType("");
    setTag("");
    setQ("");
    setProjectId("");
    setPinnedOnly(false);
    setVerification("");
    setSort("newest");
    setIncludeArchived(false);
    if (props.mode === "library") {
      router.push("/knowledge");
    } else {
      props.onProjectApply?.("");
    }
  }

  return (
    <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {props.mode === "library" && props.projects ? (
          <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
            Project
            <select
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
            >
              <option value="">All</option>
              {props.projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
          </label>
        ) : null}
        <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
          Type
          <select
            value={type}
            onChange={(e) => setType(e.target.value)}
            className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
          >
            <option value="">Any</option>
            {KNOWLEDGE_TYPES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
          Verification
          <select
            value={verification}
            onChange={(e) => setVerification(e.target.value)}
            className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
          >
            {VERIFICATION_FILTER.map((v) => (
              <option key={v === "" ? "__any__" : v} value={v}>
                {v ? v.replace(/_/g, " ") : "Any"}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
          Tag
          <input
            value={tag}
            onChange={(e) => setTag(e.target.value)}
            placeholder="exact tag"
            className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
          Search
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="title or body…"
            className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
          Sort
          <select
            value={sort}
            onChange={(e) => setSort(e.target.value)}
            className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
          >
            {KNOWLEDGE_SORT.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-4 border-t border-paper-100 pt-3 text-xs text-ink-700">
        <label className="flex cursor-pointer items-center gap-2">
          <input type="checkbox" checked={pinnedOnly} onChange={(e) => setPinnedOnly(e.target.checked)} />
          Pinned only
        </label>
        <label className="flex cursor-pointer items-center gap-2">
          <input type="checkbox" checked={includeArchived} onChange={(e) => setIncludeArchived(e.target.checked)} />
          Show archived
        </label>
      </div>
      <div className="mt-3 flex gap-2">
        <button
          type="button"
          onClick={apply}
          className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white"
        >
          Apply
        </button>
        <button
          type="button"
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-ink-950 ring-1 ring-paper-100 hover:bg-paper-50"
          onClick={reset}
        >
          Reset
        </button>
      </div>
    </div>
  );
}
