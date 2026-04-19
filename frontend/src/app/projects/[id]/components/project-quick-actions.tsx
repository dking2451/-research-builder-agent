"use client";

import { useState } from "react";
import { apiPost } from "@/lib/api";
export function ProjectQuickActions(props: {
  projectId: string;
  onAskAgent: () => void;
  onCreated: () => void;
}) {
  const [open, setOpen] = useState<null | "note" | "task" | "artifact" | "knowledge">(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [atype, setAtype] = useState("memo");
  const [ktype, setKtype] = useState("note");

  function close() {
    setOpen(null);
    setError(null);
    setTitle("");
    setBody("");
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      if (open === "note" || open === "knowledge") {
        await apiPost(`/projects/${props.projectId}/knowledge`, {
          type: open === "note" ? "note" : ktype,
          title: title.trim() || "Untitled",
          content: body.trim() || "—",
          created_by: "user",
          tags: ["quick_capture"],
          related_to: [],
        });
      } else if (open === "task") {
        await apiPost(`/projects/${props.projectId}/tasks`, {
          title: title.trim() || "Untitled task",
          description: body.trim() || null,
          status: "todo",
          priority: 2,
          metadata_json: { source: "quick_action" },
        });
      } else if (open === "artifact") {
        await apiPost(`/projects/${props.projectId}/artifacts`, {
          artifact_type: atype,
          title: title.trim() || "Untitled artifact",
          content: body.trim() || "_Empty — edit in artifact view._",
          format: "markdown",
        });
      }
      close();
      props.onCreated();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-lg border border-paper-100 bg-paper-50/80 p-3 shadow-sm">
      <div className="text-xs font-medium text-ink-700">Quick actions</div>
      <div className="mt-2 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={props.onAskAgent}
          className="rounded-md bg-ink-950 px-3 py-1.5 text-xs font-medium text-white"
        >
          Ask the agent
        </button>
        <button
          type="button"
          onClick={() => setOpen("note")}
          className="rounded-md bg-white px-3 py-1.5 text-xs text-ink-800 ring-1 ring-paper-200 hover:bg-paper-50"
        >
          Save note
        </button>
        <button
          type="button"
          onClick={() => setOpen("task")}
          className="rounded-md bg-white px-3 py-1.5 text-xs text-ink-800 ring-1 ring-paper-200 hover:bg-paper-50"
        >
          Create task
        </button>
        <button
          type="button"
          onClick={() => setOpen("artifact")}
          className="rounded-md bg-white px-3 py-1.5 text-xs text-ink-800 ring-1 ring-paper-200 hover:bg-paper-50"
        >
          Create artifact
        </button>
        <button
          type="button"
          onClick={() => setOpen("knowledge")}
          className="rounded-md bg-white px-3 py-1.5 text-xs text-ink-800 ring-1 ring-paper-200 hover:bg-paper-50"
        >
          Add knowledge
        </button>
      </div>

      {open ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/30 p-4 sm:items-center">
          <div className="w-full max-w-md rounded-lg border border-paper-100 bg-white p-4 shadow-lg">
            <div className="text-sm font-semibold text-ink-950">
              {open === "note" && "Save note"}
              {open === "knowledge" && "Add knowledge"}
              {open === "task" && "Create task"}
              {open === "artifact" && "Create artifact"}
            </div>
            {open === "knowledge" ? (
              <label className="mt-3 block text-xs font-medium text-ink-700">
                Type
                <select
                  value={ktype}
                  onChange={(e) => setKtype(e.target.value)}
                  className="mt-1 w-full rounded-md border border-paper-100 px-2 py-2 text-sm"
                >
                  <option value="note">note</option>
                  <option value="finding">finding</option>
                  <option value="fact">fact</option>
                  <option value="question">question</option>
                  <option value="conclusion">conclusion</option>
                </select>
              </label>
            ) : null}
            {open === "artifact" ? (
              <label className="mt-3 block text-xs font-medium text-ink-700">
                Artifact type
                <select
                  value={atype}
                  onChange={(e) => setAtype(e.target.value)}
                  className="mt-1 w-full rounded-md border border-paper-100 px-2 py-2 text-sm"
                >
                  <option value="memo">memo</option>
                  <option value="report">report</option>
                  <option value="plan">plan</option>
                  <option value="code">code</option>
                  <option value="prompt_pack">prompt_pack</option>
                </select>
              </label>
            ) : null}
            <label className="mt-3 block text-xs font-medium text-ink-700">
              Title
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-1 w-full rounded-md border border-paper-100 px-2 py-2 text-sm"
              />
            </label>
            <label className="mt-3 block text-xs font-medium text-ink-700">
              {open === "task" ? "Description" : "Content"}
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                rows={5}
                className="mt-1 w-full rounded-md border border-paper-100 px-2 py-2 text-sm"
              />
            </label>
            {error ? <div className="mt-2 text-xs text-red-700">{error}</div> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button type="button" className="rounded-md px-3 py-2 text-sm ring-1 ring-paper-200" onClick={close}>
                Cancel
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={submit}
                className="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {busy ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
