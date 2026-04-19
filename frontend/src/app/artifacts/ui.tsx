"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useMemo, useState } from "react";
import type { Project } from "@/lib/types";

export function ArtifactFilters(props: {
  projects: Project[];
  initial: { type?: string; q?: string; projectId?: string };
}) {
  const router = useRouter();
  const sp = useSearchParams();
  const [type, setType] = useState(props.initial.type ?? "");
  const [q, setQ] = useState(props.initial.q ?? "");
  const [projectId, setProjectId] = useState(props.initial.projectId ?? "");

  const query = useMemo(() => {
    const u = new URLSearchParams(sp?.toString());
    const setOrDelete = (k: string, v: string) => {
      const t = v.trim();
      if (!t) u.delete(k);
      else u.set(k, t);
    };
    setOrDelete("type", type);
    setOrDelete("q", q);
    setOrDelete("project_id", projectId);
    const s = u.toString();
    return s ? `?${s}` : "";
  }, [sp, type, q, projectId]);

  return (
    <form
      className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm"
      onSubmit={(e) => {
        e.preventDefault();
        router.push(`/artifacts${query}`);
      }}
    >
      <div className="grid gap-3 md:grid-cols-3">
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
        <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
          Artifact type
          <input
            value={type}
            onChange={(e) => setType(e.target.value)}
            placeholder="report, plan, …"
            className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
          />
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
          Search
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="keywords…"
            className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
          />
        </label>
      </div>
      <div className="mt-3 flex gap-2">
        <button type="submit" className="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white">
          Apply
        </button>
        <button
          type="button"
          className="rounded-md bg-white px-4 py-2 text-sm font-medium text-ink-950 ring-1 ring-paper-100"
          onClick={() => {
            setType("");
            setQ("");
            setProjectId("");
            router.push("/artifacts");
          }}
        >
          Reset
        </button>
      </div>
    </form>
  );
}
