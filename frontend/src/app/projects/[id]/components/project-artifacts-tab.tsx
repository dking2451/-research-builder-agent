"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { apiPatch } from "@/lib/api";
import type { Artifact } from "@/lib/types";

const ORDER = ["report", "plan", "memo", "table", "code", "prompt_pack"];

export function ProjectArtifactsTab(props: { artifacts: Artifact[]; onChange: (next: Artifact[]) => void }) {
  const [busy, setBusy] = useState<string | null>(null);

  const grouped = useMemo(() => {
    const m = new Map<string, Artifact[]>();
    for (const a of props.artifacts) {
      const k = a.artifact_type || "other";
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(a);
    }
    const keys = Array.from(m.keys()).sort((a, b) => {
      const ia = ORDER.indexOf(a);
      const ib = ORDER.indexOf(b);
      if (ia === -1 && ib === -1) return a.localeCompare(b);
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });
    return keys.map((t) => ({ type: t, items: m.get(t)! }));
  }, [props.artifacts]);

  async function togglePin(a: Artifact) {
    setBusy(a.id);
    try {
      const next = await apiPatch<Artifact>(`/artifacts/${a.id}`, { is_pinned: !(a.is_pinned ?? false) });
      props.onChange(props.artifacts.map((x) => (x.id === a.id ? next : x)));
    } finally {
      setBusy(null);
    }
  }

  const pinned = props.artifacts.filter((a) => a.is_pinned ?? false);
  const hasPinned = pinned.length > 0;

  return (
    <div className="space-y-4">
      {hasPinned ? (
        <div className="rounded-lg border border-accent-200 bg-accent-50/40 p-4">
          <div className="text-xs font-semibold text-accent-900">Pinned outputs</div>
          <ul className="mt-2 space-y-2 text-sm">
            {pinned.map((a) => (
              <li key={a.id}>
                <Link href={`/artifacts/${a.id}`} className="font-medium text-ink-950 hover:underline">
                  {a.title}
                </Link>
                <div className="text-xs text-ink-700">{a.artifact_type}</div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="rounded-lg border border-paper-100 bg-white shadow-sm">
        <div className="border-b border-paper-100 px-4 py-3 text-sm font-semibold text-ink-950">All artifacts</div>
        <div className="divide-y divide-paper-100">
          {grouped.length === 0 ? (
            <div className="px-4 py-8 text-sm text-ink-700">No artifacts yet.</div>
          ) : (
            grouped.map((g) => (
              <div key={g.type} className="px-4 py-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-ink-500">{g.type}</div>
                <ul className="mt-2 space-y-3">
                  {g.items.map((a) => (
                    <li key={a.id} className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <Link href={`/artifacts/${a.id}`} className="text-sm font-semibold text-ink-950 hover:underline">
                          {a.title}
                        </Link>
                        <div className="text-xs text-ink-600">
                          updated {new Date(a.updated_at).toLocaleDateString()}
                        </div>
                      </div>
                      <button
                        type="button"
                        disabled={busy === a.id}
                        onClick={() => togglePin(a)}
                        className="self-start rounded px-2 py-1 text-xs text-ink-700 ring-1 ring-paper-200 hover:bg-paper-50 disabled:opacity-50"
                      >
                        {a.is_pinned ?? false ? "Unpin" : "Pin"}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
