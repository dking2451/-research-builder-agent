"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { apiDelete, apiPatch } from "@/lib/api";
import { canPromoteToConclusion, canPromoteToFinding, KNOWLEDGE_TYPES } from "@/lib/knowledge-ui";
import type { KnowledgeItem, UUID } from "@/lib/types";

const VERIFY_OPTS = ["unverified", "partially_verified", "verified", "disputed"] as const;

type ListProps =
  | { variant: "library"; items: KnowledgeItem[] }
  | { variant: "project"; items: KnowledgeItem[]; onItemsChange: (next: KnowledgeItem[]) => void };

type KnowledgeListOptions = {
  sortMode?: "default" | "pinned_first_then_type";
  showVerificationQuickEdit?: boolean;
};

function shortVerification(v: string): string {
  if (v === "partially_verified") return "partial";
  return v.replace(/_/g, " ");
}

export function KnowledgeInlineList(props: ListProps & KnowledgeListOptions) {
  const router = useRouter();
  const [busyId, setBusyId] = useState<string | null>(null);
  const [openEditId, setOpenEditId] = useState<string | null>(null);
  const [draftTitle, setDraftTitle] = useState("");
  const [draftContent, setDraftContent] = useState("");
  const [error, setError] = useState<string | null>(null);

  const items = useMemo(() => {
    const raw = props.items;
    if (props.sortMode !== "pinned_first_then_type") return raw;
    return [...raw].sort((a, b) => {
      if (a.is_pinned !== b.is_pinned) return a.is_pinned ? -1 : 1;
      const ta = a.type.localeCompare(b.type);
      if (ta !== 0) return ta;
      const ia = a.importance_score ?? 0;
      const ib = b.importance_score ?? 0;
      if (ia !== ib) return ib - ia;
      return (b.updated_at || "").localeCompare(a.updated_at || "");
    });
  }, [props.items, props.sortMode]);

  function replaceItem(id: UUID, next: KnowledgeItem) {
    if (props.variant === "project") {
      props.onItemsChange(props.items.map((k) => (k.id === id ? next : k)));
    }
  }

  function removeItem(id: UUID) {
    if (props.variant === "project") {
      props.onItemsChange(props.items.filter((k) => k.id !== id));
    }
  }

  async function patchRow(id: UUID, body: Record<string, unknown>) {
    setBusyId(id);
    setError(null);
    try {
      const updated = await apiPatch<KnowledgeItem>(`/knowledge/${id}`, body);
      if (props.variant === "library") {
        router.refresh();
      } else {
        replaceItem(id, updated);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusyId(null);
    }
  }

  async function togglePin(k: KnowledgeItem) {
    await patchRow(k.id, { is_pinned: !k.is_pinned });
  }

  async function saveImportance(k: KnowledgeItem, raw: string) {
    const t = raw.trim();
    const importance_score = t === "" ? null : Number(t);
    if (t !== "" && Number.isNaN(importance_score)) {
      setError("Importance must be a number or empty.");
      return;
    }
    await patchRow(k.id, { importance_score });
  }

  async function saveType(k: KnowledgeItem, type: string) {
    await patchRow(k.id, { type });
  }

  async function saveVerification(k: KnowledgeItem, verification_status: string) {
    await patchRow(k.id, { verification_status });
  }

  async function saveCore(k: KnowledgeItem) {
    await patchRow(k.id, { title: draftTitle.trim(), content: draftContent });
    setOpenEditId(null);
  }

  function beginEdit(k: KnowledgeItem) {
    setOpenEditId(k.id);
    setDraftTitle(k.title);
    setDraftContent(k.content);
    setError(null);
  }

  async function promoteFinding(k: KnowledgeItem) {
    await patchRow(k.id, { type: "finding" });
  }

  async function promoteConclusion(k: KnowledgeItem) {
    await patchRow(k.id, { type: "conclusion" });
  }

  async function archiveRow(k: KnowledgeItem) {
    await patchRow(k.id, { is_archived: true });
  }

  async function unarchiveRow(k: KnowledgeItem) {
    await patchRow(k.id, { is_archived: false });
  }

  async function deleteRow(k: KnowledgeItem) {
    if (!window.confirm(`Delete “${k.title}”? This cannot be undone.`)) return;
    setBusyId(k.id);
    setError(null);
    try {
      await apiDelete(`/knowledge/${k.id}`);
      if (props.variant === "library") {
        router.refresh();
      } else {
        removeItem(k.id);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Delete failed");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div>
      {error ? <div className="mb-3 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-800">{error}</div> : null}
      <ul className="divide-y divide-paper-100">
        {items.length === 0 ? (
          <li className="px-4 py-8 text-sm text-ink-700">No items match these filters.</li>
        ) : (
          items.map((k) => {
            const busy = busyId === k.id;
            const archived = k.is_archived;
            return (
              <li
                key={k.id}
                className={[
                  "px-4 py-4 transition-colors",
                  archived ? "bg-paper-50/80 opacity-90" : "hover:bg-paper-50/60",
                ].join(" ")}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0 flex-1 space-y-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => togglePin(k)}
                        className={[
                          "rounded px-2 py-0.5 text-xs font-medium ring-1 ring-paper-200",
                          k.is_pinned ? "bg-accent-50 text-accent-800" : "bg-white text-ink-700",
                          "hover:bg-paper-50 disabled:opacity-50",
                        ].join(" ")}
                        title={k.is_pinned ? "Unpin" : "Pin"}
                      >
                        {k.is_pinned ? "Pinned" : "Pin"}
                      </button>
                      <Link href={`/knowledge/${k.id}`} className="truncate text-sm font-semibold text-ink-950 hover:underline">
                        {k.title}
                      </Link>
                      {archived ? (
                        <span className="rounded bg-paper-200 px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-ink-600">
                          archived
                        </span>
                      ) : null}
                    </div>
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-ink-600">
                      <span className="font-mono text-[11px] text-ink-500">{k.type}</span>
                      <span className="text-ink-500">·</span>
                      <span title="verification">{shortVerification(k.verification_status)}</span>
                      {props.variant === "library" ? (
                        <>
                          <span className="text-ink-500">·</span>
                          <Link href={`/projects/${k.project_id}`} className="text-ink-600 hover:text-ink-950">
                            project
                          </Link>
                        </>
                      ) : null}
                    </div>
                    <div className="line-clamp-3 text-sm text-ink-800">{k.content}</div>
                  </div>
                  <div className="flex shrink-0 flex-col gap-2 sm:items-end">
                    <div className="flex flex-wrap gap-1.5 sm:justify-end">
                      {canPromoteToFinding(k.type) ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => promoteFinding(k)}
                          className="rounded px-2 py-1 text-xs text-ink-700 ring-1 ring-paper-200 hover:bg-white disabled:opacity-50"
                        >
                          → Finding
                        </button>
                      ) : null}
                      {canPromoteToConclusion(k.type) ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => promoteConclusion(k)}
                          className="rounded px-2 py-1 text-xs text-ink-700 ring-1 ring-paper-200 hover:bg-white disabled:opacity-50"
                        >
                          → Conclusion
                        </button>
                      ) : null}
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => beginEdit(k)}
                        className="rounded px-2 py-1 text-xs text-ink-700 ring-1 ring-paper-200 hover:bg-white disabled:opacity-50"
                      >
                        Edit
                      </button>
                      {archived ? (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => unarchiveRow(k)}
                          className="rounded px-2 py-1 text-xs text-ink-700 ring-1 ring-paper-200 hover:bg-white disabled:opacity-50"
                        >
                          Restore
                        </button>
                      ) : (
                        <button
                          type="button"
                          disabled={busy}
                          onClick={() => archiveRow(k)}
                          className="rounded px-2 py-1 text-xs text-ink-700 ring-1 ring-paper-200 hover:bg-white disabled:opacity-50"
                        >
                          Archive
                        </button>
                      )}
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => deleteRow(k)}
                        className="rounded px-2 py-1 text-xs text-red-700 ring-1 ring-red-200 hover:bg-red-50 disabled:opacity-50"
                      >
                        Delete
                      </button>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-xs">
                      <label className="flex items-center gap-1 text-ink-600">
                        Type
                        <select
                          disabled={busy}
                          value={k.type}
                          onChange={(e) => saveType(k, e.target.value)}
                          className="rounded border border-paper-200 bg-white px-2 py-1 text-xs text-ink-900"
                        >
                          {!(KNOWLEDGE_TYPES as readonly string[]).includes(k.type) ? (
                            <option value={k.type}>
                              {k.type}
                            </option>
                          ) : null}
                          {KNOWLEDGE_TYPES.map((t) => (
                            <option key={t} value={t}>
                              {t}
                            </option>
                          ))}
                        </select>
                      </label>
                      <label className="flex items-center gap-1 text-ink-600">
                        Importance
                        <input
                          key={`imp-${k.id}-${k.importance_score ?? "x"}`}
                          type="text"
                          defaultValue={k.importance_score ?? ""}
                          disabled={busy}
                          onBlur={(e) => {
                            const cur = k.importance_score;
                            const raw = e.target.value.trim();
                            const next = raw === "" ? null : Number(raw);
                            if (raw !== "" && Number.isNaN(next)) return;
                            if ((cur ?? null) === (next ?? null)) return;
                            void saveImportance(k, e.target.value);
                          }}
                          className="w-14 rounded border border-paper-200 bg-white px-2 py-1 text-xs text-ink-900"
                          placeholder="—"
                        />
                      </label>
                      {props.showVerificationQuickEdit ? (
                        <label className="flex items-center gap-1 text-ink-600">
                          Verify
                          <select
                            disabled={busy}
                            value={k.verification_status}
                            onChange={(e) => saveVerification(k, e.target.value)}
                            className="rounded border border-paper-200 bg-white px-2 py-1 text-xs text-ink-900"
                          >
                            {VERIFY_OPTS.map((v) => (
                              <option key={v} value={v}>
                                {shortVerification(v)}
                              </option>
                            ))}
                          </select>
                        </label>
                      ) : null}
                    </div>
                  </div>
                </div>

                {openEditId === k.id ? (
                  <div className="mt-3 space-y-2 rounded-md border border-paper-200 bg-paper-50/50 p-3">
                    <label className="block text-xs font-medium text-ink-600">
                      Title
                      <input
                        value={draftTitle}
                        onChange={(e) => setDraftTitle(e.target.value)}
                        className="mt-1 w-full rounded border border-paper-200 bg-white px-2 py-1.5 text-sm"
                      />
                    </label>
                    <label className="block text-xs font-medium text-ink-600">
                      Content
                      <textarea
                        value={draftContent}
                        onChange={(e) => setDraftContent(e.target.value)}
                        rows={5}
                        className="mt-1 w-full rounded border border-paper-200 bg-white px-2 py-1.5 text-sm"
                      />
                    </label>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        disabled={busy || !draftTitle.trim()}
                        onClick={() => saveCore(k)}
                        className="rounded-md bg-ink-900 px-3 py-1.5 text-xs font-medium text-white disabled:opacity-50"
                      >
                        Save
                      </button>
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => setOpenEditId(null)}
                        className="rounded-md px-3 py-1.5 text-xs text-ink-700 ring-1 ring-paper-200"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                ) : null}
              </li>
            );
          })
        )}
      </ul>
    </div>
  );
}
