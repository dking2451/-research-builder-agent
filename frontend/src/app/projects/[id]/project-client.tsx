"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { KnowledgeFilters } from "@/app/knowledge/ui";
import { KnowledgeInlineList } from "@/components/knowledge/knowledge-inline-list";
import { apiGet, apiPost } from "@/lib/api";
import type {
  AgentMode,
  AgentRunResponse,
  Artifact,
  Conversation,
  ConversationDetail,
  KnowledgeItem,
  Project,
  ProjectCommandCenter,
  TaskItem,
} from "@/lib/types";
import { CommandCenterOverview } from "./components/command-center-overview";
import { PostRunActions } from "./components/post-run-actions";
import { ProjectArtifactsTab } from "./components/project-artifacts-tab";
import { ProjectQuickActions } from "./components/project-quick-actions";
import { ProjectTasksTab } from "./components/project-tasks-tab";
import { SaveToKnowledge } from "./save-to-knowledge";

type Tab = "overview" | "workspace" | "knowledge" | "artifacts" | "tasks";

export function ProjectClient(props: {
  project: Project;
  initialConversations: Conversation[];
  initialKnowledge: KnowledgeItem[];
  initialArtifacts: Artifact[];
  initialTasks: TaskItem[];
  initialCommandCenter: ProjectCommandCenter;
}) {
  const router = useRouter();
  const { project } = props;
  const [tab, setTab] = useState<Tab>("overview");
  const promptRef = useRef<HTMLTextAreaElement | null>(null);

  const [conversations, setConversations] = useState(props.initialConversations);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    props.initialConversations[0]?.id ?? null,
  );
  const [conversation, setConversation] = useState<ConversationDetail | null>(null);

  const [knowledge, setKnowledge] = useState(props.initialKnowledge);
  const knowledgeListQsRef = useRef("");
  const [artifacts, setArtifacts] = useState(props.initialArtifacts);
  const [tasks, setTasks] = useState(props.initialTasks);
  const [commandCenter, setCommandCenter] = useState(props.initialCommandCenter);

  const [mode, setMode] = useState<AgentMode>((project.mode_default as AgentMode | null) ?? "research");
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<AgentRunResponse | null>(null);

  useEffect(() => {
    setCommandCenter(props.initialCommandCenter);
  }, [props.initialCommandCenter]);

  useEffect(() => {
    if (!activeConversationId) return;
    void (async () => {
      try {
        await refreshConversation(activeConversationId);
      } catch {
        // ignore
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeConversationId]);

  async function refreshConversation(id: string) {
    const detail = await apiGet<ConversationDetail>(`/conversations/${id}`);
    setConversation(detail);
  }

  async function refreshProjectData() {
    const [k, a, t, cc] = await Promise.all([
      apiGet<KnowledgeItem[]>(`/projects/${project.id}/knowledge${knowledgeListQsRef.current}`),
      apiGet<Artifact[]>(`/projects/${project.id}/artifacts`),
      apiGet<TaskItem[]>(`/projects/${project.id}/tasks`),
      apiGet<ProjectCommandCenter>(`/projects/${project.id}/command-center`),
    ]);
    setKnowledge(k);
    setArtifacts(a);
    setTasks(t);
    setCommandCenter(cc);
    router.refresh();
  }

  async function ensureConversation(): Promise<string> {
    if (activeConversationId) {
      await refreshConversation(activeConversationId);
      return activeConversationId;
    }
    const c = await apiPost<Conversation>(`/projects/${project.id}/conversations`, { title: "Main workspace" });
    setConversations((prev) => [c, ...prev]);
    setActiveConversationId(c.id);
    await refreshConversation(c.id);
    return c.id;
  }

  async function onRun(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    setLastResult(null);
    try {
      const convId = await ensureConversation();
      const res = await apiPost<AgentRunResponse>("/agent/run", {
        project_id: project.id,
        conversation_id: convId,
        mode,
        prompt,
      });
      setLastResult(res);
      setPrompt("");
      await refreshConversation(convId);
      await refreshProjectData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Run failed");
    } finally {
      setBusy(false);
    }
  }

  function goAskAgent() {
    setTab("workspace");
    setTimeout(() => promptRef.current?.focus(), 0);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <div className="text-xs text-ink-700">
            <Link href="/projects" className="no-underline">
              Projects
            </Link>{" "}
            / <span className="text-ink-950">{project.title}</span>
          </div>
          <h1 className="mt-2 text-2xl font-semibold tracking-tight text-ink-950">{project.title}</h1>
          {project.goal ? <p className="mt-2 max-w-3xl text-sm text-ink-700">{project.goal}</p> : null}
        </div>
        <div className="text-xs text-ink-700">
          status: <span className="font-medium text-ink-950">{project.status}</span>
        </div>
      </div>

      <ProjectQuickActions projectId={project.id} onAskAgent={goAskAgent} onCreated={refreshProjectData} />

      <div className="flex flex-wrap gap-2 border-b border-paper-100 pb-2">
        {(
          [
            ["overview", "Overview"],
            ["workspace", "Chat / Workspace"],
            ["knowledge", "Knowledge"],
            ["artifacts", "Artifacts"],
            ["tasks", "Tasks"],
          ] as const
        ).map(([k, label]) => (
          <button
            key={k}
            type="button"
            onClick={() => setTab(k)}
            className={[
              "rounded-md px-3 py-1.5 text-sm",
              tab === k ? "bg-ink-950 text-white" : "bg-white text-ink-800 ring-1 ring-paper-100 hover:bg-paper-50",
            ].join(" ")}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "overview" ? <CommandCenterOverview project={project} cc={commandCenter} /> : null}

      {tab === "workspace" ? (
        <div className="grid gap-4 lg:grid-cols-2">
          <div className="space-y-3">
            <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
              <div className="text-sm font-semibold text-ink-950">Run agent</div>
              <form className="mt-3 space-y-3" onSubmit={onRun}>
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-medium text-ink-700">Mode</label>
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value as AgentMode)}
                    className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm"
                  >
                    <option value="research">Research</option>
                    <option value="decide">Decide</option>
                    <option value="build">Build</option>
                    <option value="learn">Learn</option>
                  </select>
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-medium text-ink-700">Prompt</label>
                  <textarea
                    ref={promptRef}
                    id="workspace-prompt"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    rows={6}
                    className="rounded-md border border-paper-100 bg-paper-50 px-3 py-2 text-sm outline-none focus:border-accent-600"
                    placeholder="Ask a question, define a decision, describe a build, or pick a learning goal…"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={busy}
                  className="w-full rounded-md bg-accent-600 px-4 py-2 text-sm font-medium text-white disabled:opacity-50 sm:w-auto"
                >
                  {busy ? "Running…" : "Run"}
                </button>
                {error ? <div className="text-xs text-red-700 whitespace-pre-wrap">{error}</div> : null}
              </form>
            </div>

            <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
              <div className="text-sm font-semibold text-ink-950">Conversation</div>
              <div className="mt-2 text-xs text-ink-700">
                {activeConversationId ? (
                  <span>
                    Active: <span className="font-mono">{activeConversationId}</span>
                  </span>
                ) : (
                  <span>No conversation yet — running the agent will create one.</span>
                )}
              </div>
              <button
                type="button"
                className="mt-3 rounded-md bg-white px-3 py-2 text-xs font-medium text-ink-950 ring-1 ring-paper-100 hover:bg-paper-50"
                onClick={async () => {
                  const c = await apiPost<Conversation>(`/projects/${project.id}/conversations`, {
                    title: "New thread",
                  });
                  setConversations((prev) => [c, ...prev]);
                  setActiveConversationId(c.id);
                  await refreshConversation(c.id);
                }}
              >
                New conversation
              </button>
            </div>
          </div>

          <div className="space-y-3">
            <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
              <div className="text-sm font-semibold text-ink-950">Thread</div>
              <div className="mt-3 max-h-[520px] space-y-3 overflow-auto pr-1">
                {(conversation?.messages ?? []).map((m) => (
                  <div key={m.id} className="rounded-md border border-paper-100 bg-paper-50 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-xs font-semibold text-ink-700">{m.role}</div>
                      {m.role === "assistant" ? (
                        <SaveToKnowledge
                          projectId={project.id}
                          defaultTitle="Saved from assistant message"
                          defaultContent={m.content}
                          label="Save to Knowledge"
                        />
                      ) : null}
                    </div>
                    <div className="prose prose-sm mt-2 max-w-none text-ink-900">
                      <ReactMarkdown>{m.content}</ReactMarkdown>
                    </div>
                  </div>
                ))}
                {(conversation?.messages ?? []).length === 0 ? (
                  <div className="text-sm text-ink-700">No messages yet.</div>
                ) : null}
              </div>
            </div>

            <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
              <div className="text-sm font-semibold text-ink-950">Structured result (last run)</div>
              {!lastResult ? (
                <div className="mt-2 text-sm text-ink-700">Run the agent to see extracted saves here.</div>
              ) : (
                <div className="mt-3 space-y-3 text-sm">
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-xs font-semibold text-ink-700">Assistant markdown</div>
                      <SaveToKnowledge
                        projectId={project.id}
                        defaultTitle="Saved from last agent run"
                        defaultContent={lastResult.display_markdown}
                        label="Save to Knowledge"
                      />
                    </div>
                    <div className="prose prose-sm mt-2 max-w-none rounded-md border border-paper-100 bg-paper-50 p-3">
                      <ReactMarkdown>{lastResult.display_markdown}</ReactMarkdown>
                    </div>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-3 text-xs text-ink-800">
                    <div className="rounded-md bg-paper-50 p-2 ring-1 ring-paper-100">
                      knowledge saved: {lastResult.saved_knowledge.length}
                    </div>
                    <div className="rounded-md bg-paper-50 p-2 ring-1 ring-paper-100">
                      artifacts saved: {lastResult.saved_artifacts.length}
                    </div>
                    <div className="rounded-md bg-paper-50 p-2 ring-1 ring-paper-100">
                      tasks saved: {lastResult.saved_tasks.length}
                    </div>
                  </div>
                  <PostRunActions projectId={project.id} result={lastResult} onRefresh={refreshProjectData} />
                  <details className="mt-3 rounded-md border border-paper-100 bg-paper-50 p-3 text-xs">
                    <summary className="cursor-pointer font-semibold text-ink-950">
                      Retrieval context used (prior run)
                    </summary>
                    <div className="mt-2 space-y-3 text-ink-800">
                      <div>
                        <div className="font-semibold text-ink-700">
                          Knowledge ({lastResult.selected_context.knowledge_items.length})
                        </div>
                        <ul className="mt-1 list-inside list-disc space-y-1">
                          {lastResult.selected_context.knowledge_items.map((k) => (
                            <li key={k.id}>
                              <span className="text-ink-600">[{k.role}]</span> {k.title}{" "}
                              <span className="font-mono text-ink-500">({k.id.slice(0, 8)}…)</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div className="font-semibold text-ink-700">Tasks ({lastResult.selected_context.tasks.length})</div>
                        <ul className="mt-1 list-inside list-disc space-y-1">
                          {lastResult.selected_context.tasks.map((t) => (
                            <li key={t.id}>
                              {t.title} <span className="text-ink-600">({t.status})</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <div className="font-semibold text-ink-700">
                          Artifacts ({lastResult.selected_context.artifacts.length})
                        </div>
                        <ul className="mt-1 list-inside list-disc space-y-1">
                          {lastResult.selected_context.artifacts.map((a) => (
                            <li key={a.id}>
                              [{a.artifact_type}] {a.title}
                            </li>
                          ))}
                        </ul>
                      </div>
                      <pre className="overflow-x-auto rounded bg-white p-2 text-[11px] leading-relaxed text-ink-700">
                        {JSON.stringify(lastResult.selected_context.caps, null, 2)}
                      </pre>
                      <div className="mt-2 text-xs font-semibold text-ink-700">Context notes</div>
                      <ul className="mt-1 list-inside list-disc space-y-1 text-[11px] text-ink-700">
                        {lastResult.selected_context.context_notes.map((n, i) => (
                          <li key={i}>{n}</li>
                        ))}
                      </ul>
                    </div>
                  </details>
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {tab === "knowledge" ? (
        <div className="space-y-4">
          <p className="text-xs text-ink-600">
            Pinned items sort first. Related links between items are on each knowledge detail page.
          </p>
          <KnowledgeFilters
            mode="project"
            initial={{}}
            onProjectApply={(query) => {
              knowledgeListQsRef.current = query;
              void (async () => {
                try {
                  const rows = await apiGet<KnowledgeItem[]>(`/projects/${project.id}/knowledge${query}`);
                  setKnowledge(rows);
                } catch {
                  // ignore
                }
              })();
            }}
          />
          <div className="rounded-lg border border-paper-100 bg-white shadow-sm">
            <div className="border-b border-paper-100 px-4 py-3 text-sm font-semibold text-ink-950">Knowledge</div>
            <KnowledgeInlineList
              variant="project"
              items={knowledge}
              onItemsChange={setKnowledge}
              sortMode="pinned_first_then_type"
              showVerificationQuickEdit
            />
          </div>
        </div>
      ) : null}

      {tab === "artifacts" ? <ProjectArtifactsTab artifacts={artifacts} onChange={setArtifacts} /> : null}

      {tab === "tasks" ? <ProjectTasksTab tasks={tasks} /> : null}
    </div>
  );
}
