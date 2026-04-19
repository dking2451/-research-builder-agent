"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPost } from "@/lib/api";

export function SaveToKnowledge(props: {
  projectId: string;
  defaultTitle: string;
  defaultContent: string;
  label?: string;
}) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState(props.defaultTitle);
  const [content, setContent] = useState(props.defaultContent);
  const [type, setType] = useState("note");
  const [isPinned, setIsPinned] = useState(false);
  const [importance, setImportance] = useState<string>("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function openModal() {
    setTitle(props.defaultTitle.slice(0, 500));
    setContent(props.defaultContent);
    setError(null);
    setOpen(true);
  }

  async function onSave() {
    setBusy(true);
    setError(null);
    try {
      const imp = importance.trim() === "" ? null : Number(importance);
      await apiPost(`/projects/${props.projectId}/knowledge`, {
        type,
        title: title.trim() || "Saved from workspace",
        content: content.trim() || title.trim(),
        created_by: "user",
        is_pinned: isPinned,
        importance_score: imp !== null && !Number.isNaN(imp) ? Math.min(1, Math.max(0, imp)) : null,
        tags: ["manual_save", "workspace"],
        metadata_json: { origin: "workspace_save" },
        related_to: [],
      });
      setOpen(false);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={openModal}
        className="mt-2 rounded-md bg-white px-2 py-1 text-xs font-medium text-ink-950 ring-1 ring-paper-100 hover:bg-paper-50"
      >
        {props.label ?? "Save to Knowledge"}
      </button>
      {open ? (
        <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/30 p-4 sm:items-center">
          <div className="w-full max-w-lg rounded-lg border border-paper-100 bg-white p-4 shadow-lg">
            <div className="text-sm font-semibold text-ink-950">Save to Knowledge</div>
            <p className="mt-1 text-xs text-ink-700">Creates a durable knowledge item in this project (manual capture).</p>
            <div className="mt-3 space-y-3">
              <label className="block text-xs font-medium text-ink-700">
                Type
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value)}
                  className="mt-1 w-full rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
                >
                  <option value="note">note</option>
                  <option value="finding">finding</option>
                  <option value="fact">fact</option>
                  <option value="claim">claim</option>
                  <option value="summary">summary</option>
                </select>
              </label>
              <label className="block text-xs font-medium text-ink-700">
                Title
                <input
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="mt-1 w-full rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
                />
              </label>
              <label className="block text-xs font-medium text-ink-700">
                Content
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  rows={8}
                  className="mt-1 w-full rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
                />
              </label>
              <label className="flex items-center gap-2 text-xs text-ink-800">
                <input type="checkbox" checked={isPinned} onChange={(e) => setIsPinned(e.target.checked)} />
                Pin on overview
              </label>
              <label className="block text-xs font-medium text-ink-700">
                Importance (0–1, optional)
                <input
                  value={importance}
                  onChange={(e) => setImportance(e.target.value)}
                  placeholder="e.g. 0.75"
                  className="mt-1 w-full rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
                />
              </label>
            </div>
            {error ? <div className="mt-2 text-xs text-red-700 whitespace-pre-wrap">{error}</div> : null}
            <div className="mt-4 flex justify-end gap-2">
              <button
                type="button"
                className="rounded-md px-3 py-2 text-sm text-ink-800 ring-1 ring-paper-100"
                onClick={() => setOpen(false)}
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={busy}
                className="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                onClick={onSave}
              >
                {busy ? "Saving…" : "Save"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
