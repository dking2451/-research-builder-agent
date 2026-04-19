"use client";

import { useState } from "react";
import { apiPatch, apiPost } from "@/lib/api";
import type { AgentRunResponse, KnowledgeItem } from "@/lib/types";

export function PostRunActions(props: {
  projectId: string;
  result: AgentRunResponse;
  onRefresh: () => void;
}) {
  const { result } = props;
  const [sel, setSel] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const knowledge = result.saved_knowledge;

  function toggle(id: string) {
    setSel((s) => ({ ...s, [id]: !s[id] }));
  }

  function selectedIds() {
    return knowledge.filter((k) => sel[k.id]).map((k) => k.id);
  }

  async function pinSelected() {
    const ids = selectedIds();
    if (ids.length === 0) {
      setMsg("Select at least one knowledge item.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      for (const id of ids) {
        await apiPatch<KnowledgeItem>(`/knowledge/${id}`, { is_pinned: true });
      }
      setMsg(`Pinned ${ids.length} item(s).`);
      props.onRefresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function pinAll() {
    setBusy(true);
    setMsg(null);
    try {
      for (const k of knowledge) {
        await apiPatch<KnowledgeItem>(`/knowledge/${k.id}`, { is_pinned: true });
      }
      setMsg("Pinned all saved knowledge from this run.");
      props.onRefresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function concludeSelected() {
    const ids = selectedIds();
    if (ids.length === 0) {
      setMsg("Select items to promote to conclusions.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      for (const id of ids) {
        await apiPatch<KnowledgeItem>(`/knowledge/${id}`, { type: "conclusion" });
      }
      setMsg(`Updated ${ids.length} item(s) to type conclusion.`);
      props.onRefresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  async function tasksFromSelected() {
    const ids = selectedIds();
    if (ids.length === 0) {
      setMsg("Select knowledge rows to turn into tasks.");
      return;
    }
    setBusy(true);
    setMsg(null);
    try {
      for (const k of knowledge.filter((x) => ids.includes(x.id))) {
        await apiPost(`/projects/${props.projectId}/tasks`, {
          title: `Follow up: ${k.title}`.slice(0, 500),
          description: k.content.slice(0, 4000),
          status: "todo",
          priority: 2,
          metadata_json: { source: "post_run_convert", "from_knowledge_id": k.id },
        });
      }
      setMsg(`Created ${ids.length} task(s).`);
      props.onRefresh();
    } catch (e) {
      setMsg(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  if (knowledge.length === 0 && result.saved_tasks.length === 0 && result.saved_artifacts.length === 0) {
    return (
      <p className="text-xs text-ink-700">
        This run did not persist structured rows. Try a richer prompt or check stub output.
      </p>
    );
  }

  return (
    <div className="mt-4 space-y-3 rounded-md border border-paper-100 bg-white p-3">
      <div className="text-xs font-semibold text-ink-950">Follow up on saved knowledge</div>
      <p className="text-xs text-ink-600">
        Items are already stored. Use this to pin, promote to conclusions, or spawn tasks from selected rows.
      </p>
      {knowledge.length > 0 ? (
        <ul className="max-h-48 space-y-1 overflow-auto text-xs">
          {knowledge.map((k) => (
            <li key={k.id} className="flex items-start gap-2">
              <input type="checkbox" checked={Boolean(sel[k.id])} onChange={() => toggle(k.id)} className="mt-0.5" />
              <span className="text-ink-800">{k.title}</span>
            </li>
          ))}
        </ul>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={busy || knowledge.length === 0}
          onClick={pinAll}
          className="rounded-md bg-white px-2 py-1 text-xs ring-1 ring-paper-200 disabled:opacity-50"
        >
          Pin all saved
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={pinSelected}
          className="rounded-md bg-white px-2 py-1 text-xs ring-1 ring-paper-200 disabled:opacity-50"
        >
          Pin selected
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={concludeSelected}
          className="rounded-md bg-white px-2 py-1 text-xs ring-1 ring-paper-200 disabled:opacity-50"
        >
          → Conclusion (selected)
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={tasksFromSelected}
          className="rounded-md bg-white px-2 py-1 text-xs ring-1 ring-paper-200 disabled:opacity-50"
        >
          New tasks (selected)
        </button>
      </div>
      {msg ? <div className="text-xs text-ink-700">{msg}</div> : null}
    </div>
  );
}
