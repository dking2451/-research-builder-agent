import { notFound } from "next/navigation";
import { apiGet } from "@/lib/api";
import type { KnowledgeDetail, KnowledgeItem, SourceRecordSummary } from "@/lib/types";
import { KnowledgeDetailClient } from "./knowledge-detail-client";

export default async function KnowledgeDetailPage({ params }: { params: { id: string } }) {
  let item: KnowledgeDetail;
  try {
    item = await apiGet<KnowledgeDetail>(`/knowledge/${params.id}`);
  } catch {
    notFound();
  }

  let sources: SourceRecordSummary[] = [];
  try {
    sources = await apiGet<SourceRecordSummary[]>(`/projects/${item.project_id}/source-records`);
  } catch {
    sources = [];
  }

  let peerKnowledge: KnowledgeItem[] = [];
  try {
    const all = await apiGet<KnowledgeItem[]>(`/projects/${item.project_id}/knowledge`);
    peerKnowledge = all.filter((k) => k.id !== item.id);
  } catch {
    peerKnowledge = [];
  }

  return <KnowledgeDetailClient initial={item} sources={sources} peerKnowledge={peerKnowledge} />;
}
