"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { apiDelete, apiGet, apiPatch, apiPost } from "@/lib/api";
import { canPromoteToConclusion, canPromoteToFinding, KNOWLEDGE_TYPES } from "@/lib/knowledge-ui";
import type {
  EvidenceStrength,
  KnowledgeDetail,
  KnowledgeItem,
  SourceRecordSummary,
  VerificationStatus,
} from "@/lib/types";

const VERIFICATION = ["unverified", "partially_verified", "verified", "disputed"] as const;
const STRENGTH = ["weak", "medium", "strong"] as const;

export function KnowledgeDetailClient(props: {
  initial: KnowledgeDetail;
  sources: SourceRecordSummary[];
  peerKnowledge: KnowledgeItem[];
}) {
  const router = useRouter();
  const [item, setItem] = useState(props.initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [confidence, setConfidence] = useState(
    item.confidence !== null && item.confidence !== undefined ? String(item.confidence) : "",
  );
  const [verificationStatus, setVerificationStatus] = useState(item.verification_status);
  const [evidenceStrength, setEvidenceStrength] = useState(item.evidence_strength);

  const [coreTitle, setCoreTitle] = useState(item.title);
  const [coreType, setCoreType] = useState(item.type);
  const [coreContent, setCoreContent] = useState(item.content);
  const [linkTarget, setLinkTarget] = useState("");

  useEffect(() => {
    setItem(props.initial);
    setCoreTitle(props.initial.title);
    setCoreType(props.initial.type);
    setCoreContent(props.initial.content);
    setConfidence(
      props.initial.confidence !== null && props.initial.confidence !== undefined
        ? String(props.initial.confidence)
        : "",
    );
    setVerificationStatus(props.initial.verification_status);
    setEvidenceStrength(props.initial.evidence_strength);
  }, [props.initial]);

  const availableSources = useMemo(() => {
    const linked = new Set((item.linked_sources ?? []).map((s) => s.source_record_id));
    return props.sources.filter((s) => !linked.has(s.id));
  }, [props.sources, item.linked_sources]);

  const linkOptions = useMemo(() => {
    const linkedIds = new Set(item.related.map((r) => r.knowledge_id));
    return props.peerKnowledge.filter((k) => k.id !== item.id && !linkedIds.has(k.id));
  }, [props.peerKnowledge, item.related, item.id]);

  async function saveEvidence() {
    setBusy(true);
    setError(null);
    try {
      let conf: number | null = null;
      if (confidence.trim() !== "") {
        const n = Number(confidence);
        if (Number.isNaN(n)) {
          throw new Error("Confidence must be a number between 0 and 1.");
        }
        conf = Math.min(1, Math.max(0, n));
      }
      const updated = await apiPatch<KnowledgeItem>(`/knowledge/${item.id}`, {
        confidence: conf,
        verification_status: verificationStatus,
        evidence_strength: evidenceStrength,
      });
      setItem((prev) => ({ ...prev, ...updated }));
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function saveCore() {
    setBusy(true);
    setError(null);
    try {
      const updated = await apiPatch<KnowledgeItem>(`/knowledge/${item.id}`, {
        title: coreTitle.trim(),
        type: coreType,
        content: coreContent,
      });
      setItem((prev) => ({ ...prev, ...updated }));
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Save failed");
    } finally {
      setBusy(false);
    }
  }

  async function promoteFinding() {
    setBusy(true);
    setError(null);
    try {
      const updated = await apiPatch<KnowledgeItem>(`/knowledge/${item.id}`, { type: "finding" });
      setItem((prev) => ({ ...prev, ...updated }));
      setCoreType(updated.type);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  async function promoteConclusion() {
    setBusy(true);
    setError(null);
    try {
      const updated = await apiPatch<KnowledgeItem>(`/knowledge/${item.id}`, { type: "conclusion" });
      setItem((prev) => ({ ...prev, ...updated }));
      setCoreType(updated.type);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  async function addCitation(sourceId: string) {
    setBusy(true);
    setError(null);
    try {
      const detail = await apiPost<KnowledgeDetail>(`/knowledge/${item.id}/citations`, {
        source_record_id: sourceId,
        citation_note: null,
        locator: null,
      });
      setItem(detail);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Add citation failed");
    } finally {
      setBusy(false);
    }
  }

  async function removeCitation(sourceId: string) {
    setBusy(true);
    setError(null);
    try {
      await apiDelete(`/knowledge/${item.id}/citations/${sourceId}`);
      const detail = await apiGet<KnowledgeDetail>(`/knowledge/${item.id}`);
      setItem(detail);
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Remove failed");
    } finally {
      setBusy(false);
    }
  }

  async function addRelation() {
    if (!linkTarget) return;
    setBusy(true);
    setError(null);
    try {
      const detail = await apiPost<KnowledgeDetail>(`/knowledge/${item.id}/relations`, {
        to_knowledge_id: linkTarget,
        relation_type: "related",
      });
      setItem(detail);
      setLinkTarget("");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Link failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="text-xs text-ink-700">
        <Link href="/knowledge" className="no-underline">
          Knowledge
        </Link>{" "}
        / <span className="text-ink-950">{item.title}</span>
      </div>

      <div className="lg:grid lg:grid-cols-[minmax(0,1fr),280px] lg:items-start lg:gap-8">
        <div className="min-w-0 space-y-4">
          <div className="rounded-lg border border-paper-100 bg-white p-5 shadow-sm">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <h1 className="text-xl font-semibold tracking-tight text-ink-950">{item.title}</h1>
                  {item.is_archived ? (
                    <span className="rounded bg-paper-200 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-ink-600">
                      archived
                    </span>
                  ) : null}
                </div>
                <div className="mt-2 flex flex-wrap gap-x-2 gap-y-1 text-xs text-ink-600">
                  <span>{item.type}</span>
                  <span className="text-ink-400">·</span>
                  <span>{item.created_by}</span>
                  {item.is_pinned ? (
                    <>
                      <span className="text-ink-400">·</span>
                      <span className="font-medium text-accent-700">pinned</span>
                    </>
                  ) : null}
                  {typeof item.importance_score === "number" ? (
                    <>
                      <span className="text-ink-400">·</span>
                      <span>importance {item.importance_score}</span>
                    </>
                  ) : null}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {canPromoteToFinding(item.type) ? (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={promoteFinding}
                    className="rounded-md px-3 py-1.5 text-xs text-ink-800 ring-1 ring-paper-200 hover:bg-paper-50 disabled:opacity-50"
                  >
                    Promote to finding
                  </button>
                ) : null}
                {canPromoteToConclusion(item.type) ? (
                  <button
                    type="button"
                    disabled={busy}
                    onClick={promoteConclusion}
                    className="rounded-md px-3 py-1.5 text-xs text-ink-800 ring-1 ring-paper-200 hover:bg-paper-50 disabled:opacity-50"
                  >
                    Promote to conclusion
                  </button>
                ) : null}
                <Link href={`/projects/${item.project_id}`} className="rounded-md px-3 py-1.5 text-xs text-ink-800 ring-1 ring-paper-200 hover:bg-paper-50">
                  Open project
                </Link>
              </div>
            </div>

            {error ? <div className="mt-3 text-xs text-red-700 whitespace-pre-wrap">{error}</div> : null}

            <details className="mt-5 rounded-md border border-paper-100 bg-paper-50/60 p-4">
              <summary className="cursor-pointer text-sm font-medium text-ink-900">Edit title, type & body</summary>
              <div className="mt-4 space-y-3">
                <label className="block text-xs font-medium text-ink-600">
                  Title
                  <input
                    value={coreTitle}
                    onChange={(e) => setCoreTitle(e.target.value)}
                    className="mt-1 w-full rounded-md border border-paper-200 bg-white px-3 py-2 text-sm"
                  />
                </label>
                <label className="block text-xs font-medium text-ink-600">
                  Type
                  <select
                    value={coreType}
                    onChange={(e) => setCoreType(e.target.value)}
                    className="mt-1 w-full rounded-md border border-paper-200 bg-white px-3 py-2 text-sm"
                  >
                    {!(KNOWLEDGE_TYPES as readonly string[]).includes(coreType) ? (
                      <option value={coreType}>{coreType}</option>
                    ) : null}
                    {KNOWLEDGE_TYPES.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="block text-xs font-medium text-ink-600">
                  Body
                  <textarea
                    value={coreContent}
                    onChange={(e) => setCoreContent(e.target.value)}
                    rows={8}
                    className="mt-1 w-full rounded-md border border-paper-200 bg-white px-3 py-2 text-sm"
                  />
                </label>
                <button
                  type="button"
                  disabled={busy || !coreTitle.trim()}
                  onClick={saveCore}
                  className="rounded-md bg-ink-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                >
                  Save core fields
                </button>
              </div>
            </details>

            <div className="mt-5 rounded-md border border-paper-100 bg-paper-50 p-4">
              <div className="text-sm font-semibold text-ink-950">Evidence & verification</div>
              <div className="mt-3 grid gap-3 sm:grid-cols-3">
                <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
                  Confidence (0–1)
                  <input
                    value={confidence}
                    onChange={(e) => setConfidence(e.target.value)}
                    placeholder="e.g. 0.7"
                    className="rounded-md border border-paper-100 bg-white px-3 py-2 text-sm"
                  />
                </label>
                <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
                  Verification
                  <select
                    value={verificationStatus}
                    onChange={(e) =>
                      setVerificationStatus(e.target.value as VerificationStatus)
                    }
                    className="rounded-md border border-paper-100 bg-white px-3 py-2 text-sm"
                  >
                    {VERIFICATION.map((v) => (
                      <option key={v} value={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="flex flex-col gap-1 text-xs font-medium text-ink-700">
                  Evidence strength
                  <select
                    value={evidenceStrength}
                    onChange={(e) =>
                      setEvidenceStrength(e.target.value as EvidenceStrength)
                    }
                    className="rounded-md border border-paper-100 bg-white px-3 py-2 text-sm"
                  >
                    {STRENGTH.map((v) => (
                      <option key={v} value={v}>
                        {v}
                      </option>
                    ))}
                  </select>
                </label>
              </div>
              <button
                type="button"
                disabled={busy}
                onClick={saveEvidence}
                className="mt-3 rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
              >
                {busy ? "Saving…" : "Save evidence fields"}
              </button>
            </div>

            {(item.source_name || item.source_url) && (
              <div className="mt-4 rounded-md border border-paper-100 bg-paper-50 p-3 text-sm">
                <div className="text-xs font-semibold text-ink-700">Inline source (legacy fields)</div>
                <div className="mt-1 text-sm text-ink-900">{item.source_name || "—"}</div>
                {item.source_url ? (
                  <a className="mt-2 inline-block text-sm" href={item.source_url}>
                    {item.source_url}
                  </a>
                ) : null}
              </div>
            )}

            <div className="mt-5 rounded-md border border-paper-100 bg-paper-50 p-4">
              <div className="text-sm font-semibold text-ink-950">Linked sources (citations)</div>
              {(item.linked_sources ?? []).length === 0 ? (
                <p className="mt-2 text-sm text-ink-700">No source records linked yet.</p>
              ) : (
                <ul className="mt-3 space-y-3 text-sm">
                  {(item.linked_sources ?? []).map((s) => (
                    <li key={s.source_record_id} className="rounded-md border border-paper-100 bg-white p-3">
                      <div className="font-medium text-ink-950">{s.title}</div>
                      <div className="text-xs text-ink-700">{s.source_type || "source"}</div>
                      {s.url ? (
                        <a href={s.url} className="mt-1 inline-block text-sm">
                          {s.url}
                        </a>
                      ) : null}
                      {s.locator ? <div className="mt-1 text-xs text-ink-700">Locator: {s.locator}</div> : null}
                      {s.citation_note ? <div className="mt-1 text-xs text-ink-800">{s.citation_note}</div> : null}
                      <button
                        type="button"
                        disabled={busy}
                        className="mt-2 text-xs text-red-700 underline"
                        onClick={() => removeCitation(s.source_record_id)}
                      >
                        Remove link
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {availableSources.length > 0 ? (
                <div className="mt-4 flex flex-wrap items-end gap-2">
                  <label className="text-xs font-medium text-ink-700">
                    Add citation
                    <select
                      className="ml-2 rounded-md border border-paper-100 bg-white px-2 py-1 text-sm"
                      defaultValue=""
                      onChange={(e) => {
                        const v = e.target.value;
                        if (v) void addCitation(v);
                        e.target.value = "";
                      }}
                    >
                      <option value="">Choose source…</option>
                      {availableSources.map((s) => (
                        <option key={s.id} value={s.id}>
                          {s.title}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              ) : (
                <p className="mt-3 text-xs text-ink-700">
                  {props.sources.length === 0
                    ? "No source records in this project yet."
                    : "All project sources are already linked."}
                </p>
              )}
            </div>

            <div className="mt-5 whitespace-pre-wrap text-sm text-ink-900">{item.content}</div>

            {item.tags && item.tags.length > 0 ? (
              <div className="mt-5 text-sm text-ink-800">
                <span className="text-xs font-semibold text-ink-700">Tags: </span>
                {item.tags.join(", ")}
              </div>
            ) : null}
          </div>
        </div>

        <aside className="mt-6 space-y-4 lg:mt-0">
          <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
            <div className="text-sm font-semibold text-ink-950">Related knowledge</div>
            <p className="mt-1 text-xs text-ink-600">Items linked to this entry in the same project.</p>
            {item.related.length === 0 ? (
              <p className="mt-3 text-sm text-ink-700">None yet.</p>
            ) : (
              <ul className="mt-3 space-y-2 text-sm">
                {item.related.map((r) => (
                  <li key={`${r.direction}:${r.knowledge_id}`} className="rounded-md bg-paper-50 px-2 py-2">
                    <div className="text-[10px] uppercase tracking-wide text-ink-500">
                      {r.direction}
                      {r.relation_type ? ` · ${r.relation_type}` : ""}
                    </div>
                    <Link href={`/knowledge/${r.knowledge_id}`} className="font-medium text-ink-900 hover:underline">
                      {r.title}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
            {linkOptions.length > 0 ? (
              <div className="mt-4 border-t border-paper-100 pt-3">
                <div className="text-xs font-medium text-ink-700">Link another item</div>
                <div className="mt-2 flex flex-col gap-2">
                  <select
                    value={linkTarget}
                    onChange={(e) => setLinkTarget(e.target.value)}
                    className="rounded-md border border-paper-200 bg-paper-50 px-2 py-2 text-sm"
                  >
                    <option value="">Choose…</option>
                    {linkOptions.map((k) => (
                      <option key={k.id} value={k.id}>
                        {k.title}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    disabled={busy || !linkTarget}
                    onClick={addRelation}
                    className="rounded-md bg-ink-900 px-3 py-2 text-xs font-medium text-white disabled:opacity-50"
                  >
                    Add link
                  </button>
                </div>
              </div>
            ) : (
              <p className="mt-3 text-xs text-ink-600">No other items in this project to link.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
