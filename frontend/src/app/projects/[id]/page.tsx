import { notFound } from "next/navigation";
import { apiGet } from "@/lib/api";
import type { Artifact, Conversation, KnowledgeItem, Project, ProjectCommandCenter, TaskItem } from "@/lib/types";
import { ProjectClient } from "./project-client";

export default async function ProjectPage({ params }: { params: { id: string } }) {
  const id = params.id;
  let project: Project;
  try {
    project = await apiGet<Project>(`/projects/${id}`);
  } catch {
    notFound();
  }

  const [conversations, knowledge, artifacts, tasks, commandCenter] = await Promise.all([
    apiGet<Conversation[]>(`/projects/${id}/conversations`),
    apiGet<KnowledgeItem[]>(`/projects/${id}/knowledge`),
    apiGet<Artifact[]>(`/projects/${id}/artifacts`),
    apiGet<TaskItem[]>(`/projects/${id}/tasks`),
    apiGet<ProjectCommandCenter>(`/projects/${id}/command-center`),
  ]);

  return (
    <ProjectClient
      project={project}
      initialConversations={conversations}
      initialKnowledge={knowledge}
      initialArtifacts={artifacts}
      initialTasks={tasks}
      initialCommandCenter={commandCenter}
    />
  );
}
