"use client";

import { useMemo } from "react";
import type { TaskItem } from "@/lib/types";

const STATUS_ORDER = ["todo", "in_progress", "done", "cancelled"];

export function ProjectTasksTab(props: { tasks: TaskItem[] }) {
  const grouped = useMemo(() => {
    const m = new Map<string, TaskItem[]>();
    for (const t of props.tasks) {
      const s = t.status || "todo";
      if (!m.has(s)) m.set(s, []);
      m.get(s)!.push(t);
    }
    const keys = Array.from(m.keys()).sort((a, b) => {
      const ia = STATUS_ORDER.indexOf(a);
      const ib = STATUS_ORDER.indexOf(b);
      if (ia === -1 && ib === -1) return a.localeCompare(b);
      if (ia === -1) return 1;
      if (ib === -1) return -1;
      return ia - ib;
    });
    return keys.map((status) => ({
      status,
      items: (m.get(status) || []).sort((a, b) => a.priority - b.priority || (b.updated_at || "").localeCompare(a.updated_at || "")),
    }));
  }, [props.tasks]);

  const nextBest = useMemo(() => {
    return props.tasks
      .filter((t) => t.status === "todo" || t.status === "in_progress")
      .sort((a, b) => a.priority - b.priority)
      .slice(0, 4);
  }, [props.tasks]);

  return (
    <div id="tasks" className="space-y-4">
      {nextBest.length > 0 ? (
        <div className="rounded-lg border border-paper-100 bg-paper-50/80 p-4">
          <div className="text-xs font-semibold text-ink-950">Suggested next actions</div>
          <p className="mt-1 text-xs text-ink-600">Open tasks sorted by priority (lower number = sooner).</p>
          <ul className="mt-2 space-y-2 text-sm">
            {nextBest.map((t) => (
              <li key={t.id}>
                <div className="font-medium text-ink-950">{t.title}</div>
                <div className="text-xs text-ink-600">
                  {t.status} · p{t.priority}
                  {taskOrigin(t) ? ` · ${taskOrigin(t)}` : ""}
                </div>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="rounded-lg border border-paper-100 bg-white shadow-sm">
        <div className="border-b border-paper-100 px-4 py-3 text-sm font-semibold text-ink-950">By status</div>
        <div className="divide-y divide-paper-100">
          {grouped.length === 0 ? (
            <div className="px-4 py-8 text-sm text-ink-700">No tasks yet.</div>
          ) : (
            grouped.map((g) => (
              <div key={g.status} className="px-4 py-4">
                <div className="text-xs font-semibold uppercase tracking-wide text-ink-500">{g.status}</div>
                <ul className="mt-2 space-y-3">
                  {g.items.map((t) => (
                    <li key={t.id}>
                      <div className="text-sm font-semibold text-ink-950">{t.title}</div>
                      <div className="text-xs text-ink-600">
                        priority {t.priority}
                        {taskOrigin(t) ? ` · ${taskOrigin(t)}` : ""}
                      </div>
                      {t.description ? <div className="mt-1 text-sm text-ink-800">{t.description}</div> : null}
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

function taskOrigin(t: TaskItem): string | null {
  const src = t.metadata_json && typeof t.metadata_json.source === "string" ? t.metadata_json.source : null;
  if (src === "agent_run") return "from agent run";
  if (src === "post_run_convert") return "from saved knowledge";
  if (src === "quick_action") return "quick capture";
  return null;
}
