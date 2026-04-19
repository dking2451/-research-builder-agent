"""Post-process LLM envelopes: dedupe, cap, light fallbacks, scoring hints."""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.schemas.llm_output import AgentLLMEnvelope, ArtifactDraft, KnowledgeDraft, TaskDraft


@dataclass(frozen=True)
class ProcessedAgentPayload:
    envelope: AgentLLMEnvelope
    """Drafts aligned with `envelope.knowledge_items` after processing (same length/order)."""


def _norm_title(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def _default_importance(item_type: str) -> float | None:
    t = (item_type or "").lower()
    if t in {"finding", "conclusion"}:
        return 0.75
    if t in {"fact", "summary"}:
        return 0.65
    if t in {"claim", "source"}:
        return 0.55
    if t in {"task", "output"}:
        return 0.45
    return 0.5


def _fallback_knowledge_from_markdown(md: str, *, mode: str) -> list[KnowledgeDraft]:
    out: list[KnowledgeDraft] = []
    for raw in (md or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith(("- ", "* ", "• ")):
            text = line[2:].strip()
            if len(text) < 10:
                continue
            title = text[:120] + ("…" if len(text) > 120 else "")
            out.append(
                KnowledgeDraft(
                    type="finding",
                    title=title,
                    content=text,
                    tags=["auto_extract", mode],
                    metadata={"extractor": "markdown_bullets"},
                )
            )
        if len(out) >= 8:
            break
    return out


def _fallback_tasks_from_markdown(md: str, *, mode: str) -> list[TaskDraft]:
    out: list[TaskDraft] = []
    for raw in (md or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        lower = line.lower()
        if lower.startswith("next step") or lower.startswith("next steps") or lower.startswith("- [ ]"):
            title = re.sub(r"^[-*]\s*(\[[ x]\]\s*)?", "", line, flags=re.IGNORECASE).strip()
            if len(title) < 6:
                continue
            out.append(
                TaskDraft(
                    title=title[:500],
                    description="Auto-extracted from assistant markdown",
                    status="todo",
                    priority=2,
                )
            )
        if len(out) >= 10:
            break
    if not out and mode in {"research", "decide", "build", "learn"}:
        out.append(
            TaskDraft(
                title="Review the run output and pin the best knowledge items",
                description="Lightweight default next action when no explicit tasks were extracted.",
                status="todo",
                priority=3,
            )
        )
    return out


def _fallback_artifact_from_markdown(md: str, *, mode: str) -> ArtifactDraft | None:
    text = (md or "").strip()
    if len(text) < 400:
        return None
    excerpt = text[:3500]
    return ArtifactDraft(
        artifact_type="memo",
        title=f"Session memo ({mode})",
        content=f"## Auto-saved session memo\n\n{excerpt}\n",
        format="markdown",
    )


def process_agent_envelope(envelope: AgentLLMEnvelope, *, mode: str) -> ProcessedAgentPayload:
    k_items = list(envelope.knowledge_items)
    if not k_items:
        k_items = _fallback_knowledge_from_markdown(envelope.display_markdown, mode=mode)

    # Dedupe by normalized title (keep first).
    seen: set[str] = set()
    deduped: list[KnowledgeDraft] = []
    for k in k_items:
        key = _norm_title(k.title)
        if not key:
            key = _norm_title(k.content)[:80]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(k)
    k_items = deduped[:15]

    artifacts = list(envelope.artifacts)[:8]
    if not artifacts:
        memo = _fallback_artifact_from_markdown(envelope.display_markdown, mode=mode)
        if memo:
            artifacts = [memo]

    tasks = list(envelope.tasks)[:15]
    if not tasks:
        tasks = _fallback_tasks_from_markdown(envelope.display_markdown, mode=mode)

    # Enrich knowledge with defaults where missing.
    enriched: list[KnowledgeDraft] = []
    for k in k_items:
        imp = k.importance_score if k.importance_score is not None else _default_importance(k.type)
        pinned = bool(k.is_pinned)
        if (k.type or "").lower() in {"conclusion", "summary"} and imp is not None and imp >= 0.7:
            pinned = pinned or False
        enriched.append(
            k.model_copy(
                update={
                    "importance_score": imp,
                    "is_pinned": pinned,
                }
            )
        )

    out = AgentLLMEnvelope(
        display_markdown=envelope.display_markdown,
        knowledge_items=enriched,
        source_records=list(envelope.source_records)[:20],
        artifacts=artifacts,
        tasks=tasks,
    )
    return ProcessedAgentPayload(envelope=out)
