"use client";

import Link from "next/link";
import type { ActivityEvent, OpenLoopItem, Project, ProjectCommandCenter } from "@/lib/types";

function Section(props: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-paper-100 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-ink-950">{props.title}</div>
      {props.hint ? <p className="mt-1 text-xs text-ink-600">{props.hint}</p> : null}
      <div className="mt-3">{props.children}</div>
    </div>
  );
}

function loopHref(loop: OpenLoopItem): string {
  return loop.entity === "task" ? `#tasks` : `/knowledge/${loop.id}`;
}

export function CommandCenterOverview(props: {
  project: Project;
  cc: ProjectCommandCenter;
}) {
  const { project, cc } = props;

  return (
    <div className="space-y-6">
      <Section title="Project focus" hint="Goal and description keep everyone aligned.">
        {project.goal ? <p className="text-sm font-medium text-ink-900">{project.goal}</p> : null}
        <p className={`text-sm text-ink-800 ${project.goal ? "mt-2" : ""}`}>
          {project.description?.trim() || "Add a goal and description from the project settings when you can."}
        </p>
      </Section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Pinned knowledge" hint="North-star items for this project.">
          {cc.pinned_knowledge.length === 0 ? (
            <p className="text-sm text-ink-700">Nothing pinned yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {cc.pinned_knowledge.map((k) => (
                <li key={k.id}>
                  <Link href={`/knowledge/${k.id}`} className="font-medium text-ink-900 hover:underline">
                    {k.title}
                  </Link>
                  <div className="text-xs text-ink-600">{k.type}</div>
                </li>
              ))}
            </ul>
          )}
        </Section>
        <Section title="Key findings" hint="Latest research-style saves.">
          {cc.key_findings.length === 0 ? (
            <p className="text-sm text-ink-700">No findings yet — run Research mode or capture manually.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {cc.key_findings.map((k) => (
                <li key={k.id}>
                  <Link href={`/knowledge/${k.id}`} className="font-medium text-ink-900 hover:underline">
                    {k.title}
                  </Link>
                  <div className="line-clamp-2 text-xs text-ink-700">{k.content}</div>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Latest conclusions" hint="Decisions and synthesized takeaways.">
          {cc.latest_conclusions.length === 0 ? (
            <p className="text-sm text-ink-700">No conclusions yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {cc.latest_conclusions.map((k) => (
                <li key={k.id}>
                  <Link href={`/knowledge/${k.id}`} className="font-medium text-ink-900 hover:underline">
                    {k.title}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Section>
        <Section title="Open questions" hint="Explicit questions worth answering next.">
          {cc.open_questions.length === 0 ? (
            <p className="text-sm text-ink-700">No question-type knowledge yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {cc.open_questions.map((k) => (
                <li key={k.id}>
                  <Link href={`/knowledge/${k.id}`} className="font-medium text-ink-900 hover:underline">
                    {k.title}
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>

      <Section
        title="Open loops"
        hint="Lightweight follow-ups: open work, questions, weak evidence, unverified claims."
      >
        {cc.open_loops.length === 0 ? (
          <p className="text-sm text-ink-700">Nothing flagged — you are caught up.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {cc.open_loops.map((loop) => (
              <li key={`${loop.entity}:${loop.id}`} className="flex flex-col gap-0.5 rounded-md bg-paper-50 px-2 py-2">
                <Link href={loopHref(loop)} className="font-medium text-ink-900 hover:underline">
                  {loop.title}
                </Link>
                <div className="text-xs text-ink-600">
                  <span className="font-mono text-[10px] uppercase text-ink-500">{loop.kind.replace(/_/g, " ")}</span>
                  {" · "}
                  {loop.reason}
                </div>
              </li>
            ))}
          </ul>
        )}
      </Section>

      <div className="grid gap-4 lg:grid-cols-2">
        <Section title="Next tasks" hint="Open work, highest priority first.">
          {cc.next_tasks.length === 0 ? (
            <p className="text-sm text-ink-700">No open tasks.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {cc.next_tasks.map((t) => (
                <li key={t.id}>
                  <div className="font-medium text-ink-950">{t.title}</div>
                  <div className="text-xs text-ink-600">
                    {t.status} · p{t.priority}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>
        <Section title="Recent artifacts" hint="Reports, plans, code, and packs.">
          {cc.recent_artifacts.length === 0 ? (
            <p className="text-sm text-ink-700">No artifacts yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {cc.recent_artifacts.map((a) => (
                <li key={a.id}>
                  <Link href={`/artifacts/${a.id}`} className="font-medium text-ink-900 hover:underline">
                    {a.title}
                  </Link>
                  <div className="text-xs text-ink-600">
                    {a.artifact_type}
                    {a.is_pinned ?? false ? " · pinned" : ""}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </Section>
      </div>

      <Section title="Activity timeline" hint="Recent messages, saves, artifacts, and tasks (merged).">
        {cc.timeline.length === 0 ? (
          <p className="text-sm text-ink-700">No activity yet.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {cc.timeline.map((ev) => (
              <TimelineRow key={`${ev.kind}:${ev.entity_id}`} ev={ev} />
            ))}
          </ul>
        )}
      </Section>
    </div>
  );
}

function TimelineRow({ ev }: { ev: ActivityEvent }) {
  const href =
    ev.kind === "knowledge"
      ? `/knowledge/${ev.entity_id}`
      : ev.kind === "artifact"
        ? `/artifacts/${ev.entity_id}`
        : ev.kind === "task"
          ? `#tasks`
          : undefined;
  const inner = (
    <>
      <div className="text-[10px] font-medium uppercase tracking-wide text-ink-500">
        {ev.kind} · {new Date(ev.occurred_at).toLocaleString()}
      </div>
      <div className="text-ink-900">{ev.title}</div>
      {ev.subtitle ? <div className="text-xs text-ink-600">{ev.subtitle}</div> : null}
    </>
  );
  return (
    <li className="rounded-md border border-paper-100 bg-paper-50/60 px-3 py-2">
      {href ? (
        <Link href={href} className="block hover:bg-paper-50">
          {inner}
        </Link>
      ) : (
        <div>{inner}</div>
      )}
    </li>
  );
}
