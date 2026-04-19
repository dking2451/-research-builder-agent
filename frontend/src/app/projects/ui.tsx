"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { apiPost } from "@/lib/api";

export function CreateProjectForm() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const p = await apiPost<{ id: string }>("/projects", { title, status: "active", tags: [] });
      setTitle("");
      router.push(`/projects/${p.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-ink-950">Create project</div>
      <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Title (e.g., “Compare vector DB options”)"
          className="w-full rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm outline-none focus:border-accent-600"
          required
        />
        <button
          type="submit"
          disabled={busy || !title.trim()}
          className="rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {busy ? "Creating…" : "Create"}
        </button>
      </div>
      {error ? <div className="mt-2 text-xs text-red-700 whitespace-pre-wrap">{error}</div> : null}
    </form>
  );
}
