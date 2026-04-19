import Link from "next/link";
import { notFound } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { apiGet } from "@/lib/api";
import type { Artifact } from "@/lib/types";

export default async function ArtifactDetailPage({ params }: { params: { id: string } }) {
  let a: Artifact;
  try {
    a = await apiGet<Artifact>(`/artifacts/${params.id}`);
  } catch {
    notFound();
  }

  return (
    <div className="space-y-4">
      <div className="text-xs text-ink-700">
        <Link href="/artifacts" className="no-underline">
          Artifacts
        </Link>{" "}
        / <span className="text-ink-950">{a.title}</span>
      </div>
      <div className="rounded-lg border border-paper-100 bg-white p-5 shadow-sm">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <h1 className="text-xl font-semibold tracking-tight text-ink-950">{a.title}</h1>
            <div className="mt-2 text-xs text-ink-700">
              type: <span className="font-medium text-ink-950">{a.artifact_type}</span> · format:{" "}
              <span className="font-medium text-ink-950">{a.format}</span>
            </div>
          </div>
          <Link href={`/projects/${a.project_id}`} className="text-sm">
            Open project
          </Link>
        </div>

        <div className="prose prose-sm mt-6 max-w-none">
          <ReactMarkdown>{a.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
