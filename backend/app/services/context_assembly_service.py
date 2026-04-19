"""
Retrieval-aware, compact project context for agent runs (deterministic).

Ranking for merged knowledge (stable, explainable):
1. is_pinned (True before False)
2. importance_score (higher first; None treated as 0)
3. updated_at (newer first)
4. created_at (newer first), tie-break when updated_at matches

Sources (per project, non-archived knowledge only):
- pinned knowledge
- recent findings (type=finding)
- recent conclusions (type=conclusion)
- knowledge linked via KnowledgeItemRelation to pinned + findings + conclusions (anchors)
- mode-specific supplemental pool (types biased per agent mode)
- open tasks + recent artifacts

Semantic search / embeddings: plug in as a *candidate source* before merge+rank without
changing caps or debug shape — add rows with selection_reason `semantic_retrieval` later.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Iterable, Literal, Protocol, TypeVar, cast

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.artifact import GeneratedArtifact
from app.models.knowledge import KnowledgeItem, KnowledgeItemRelation
from app.models.project import Project
from app.models.task import TaskItem
from app.schemas.context_assembly import (
    ProjectSummaryRef,
    RetrievedArtifactRef,
    RetrievedKnowledgeRef,
    RetrievedTaskRef,
    SelectedContextDebug,
)


class _HasKnowledgeRankAttrs(Protocol):
    is_pinned: bool
    importance_score: float | None
    updated_at: datetime | None
    created_at: datetime | None


T = TypeVar("T", bound=_HasKnowledgeRankAttrs)


def knowledge_retrieval_sort_key(item: _HasKnowledgeRankAttrs) -> tuple[bool, float, float, float]:
    pinned = bool(item.is_pinned)
    imp = float(item.importance_score) if item.importance_score is not None else 0.0
    uts = item.updated_at.timestamp() if item.updated_at is not None else 0.0
    cts = item.created_at.timestamp() if item.created_at is not None else 0.0
    return (pinned, imp, uts, cts)


def rank_knowledge_for_context(items: Iterable[T]) -> list[T]:
    """Pinned first, then importance desc, then recency (updated, then created)."""
    return sorted(items, key=knowledge_retrieval_sort_key, reverse=True)


def truncate_text(text: str, max_chars: int) -> str:
    t = (text or "").strip()
    if len(t) <= max_chars:
        return t
    return t[: max_chars - 1].rstrip() + "…"


@dataclass(frozen=True)
class ContextAssemblyLimits:
    """V1 defaults (tuned per mode via `default_limits_for_mode`)."""

    max_pinned_knowledge: int = 12
    max_recent_findings: int = 10
    max_recent_conclusions: int = 8
    max_supplemental_knowledge: int = 10
    max_related_knowledge: int = 16
    max_knowledge_in_prompt: int = 24
    max_open_tasks: int = 12
    max_recent_artifacts: int = 5
    max_chars_per_knowledge: int = 700
    max_chars_per_artifact: int = 2200
    max_total_retrieval_chars: int = 14_000


def default_limits_for_mode(mode: str) -> ContextAssemblyLimits:
    """Mode-aware caps (deterministic overrides on a shared baseline)."""
    base = ContextAssemblyLimits()
    if mode == "research":
        return replace(
            base,
            max_recent_findings=14,
            max_recent_conclusions=6,
            max_supplemental_knowledge=12,
            max_related_knowledge=18,
            max_knowledge_in_prompt=26,
        )
    if mode == "decide":
        return replace(
            base,
            max_recent_conclusions=14,
            max_recent_findings=8,
            max_open_tasks=14,
            max_supplemental_knowledge=12,
            max_related_knowledge=14,
        )
    if mode == "build":
        return replace(
            base,
            max_recent_artifacts=10,
            max_open_tasks=14,
            max_supplemental_knowledge=12,
            max_knowledge_in_prompt=22,
        )
    if mode == "learn":
        return replace(
            base,
            max_recent_findings=8,
            max_supplemental_knowledge=14,
            max_recent_artifacts=6,
            max_knowledge_in_prompt=24,
        )
    return base


MODE_SUPPLEMENTAL_TYPES: dict[str, tuple[str, ...]] = {
    # findings + sources + explicit questions
    "research": ("source", "question"),
    # tradeoff-shaped memory
    "decide": ("claim", "fact"),
    # implementation-shaped memory
    "build": ("output", "note", "task"),
    # learning-shaped memory
    "learn": ("summary", "note", "output"),
}


def _dedupe_preserve_order(items: list[KnowledgeItem]) -> list[KnowledgeItem]:
    seen: set[uuid.UUID] = set()
    out: list[KnowledgeItem] = []
    for it in items:
        if it.id in seen:
            continue
        seen.add(it.id)
        out.append(it)
    return out


def _mode_context_notes(mode: str) -> list[str]:
    m = (mode or "research").lower()
    lines = [
        f"Mode={m}: supplemental types = {', '.join(MODE_SUPPLEMENTAL_TYPES.get(m, ())) or '—'}.",
        "Anchors for graph expansion = pinned + recent findings + recent conclusions (supplemental not used as anchors).",
        "Merge order before global rank: pinned, findings, conclusions, related, supplemental.",
    ]
    if m == "research":
        lines.append("Research shaping: larger finding + source/question pools.")
    elif m == "decide":
        lines.append("Decide shaping: emphasizes conclusions, claims/facts, and open tasks.")
    elif m == "build":
        lines.append("Build shaping: more artifacts + implementation notes (outputs, notes, task-knowledge).")
    elif m == "learn":
        lines.append("Learn shaping: summaries, exercises (output), and notes.")
    return lines


def assemble_retrieval_context(
    db: Session,
    *,
    project_id: uuid.UUID,
    mode: str,
    limits: ContextAssemblyLimits | None = None,
) -> tuple[str, SelectedContextDebug]:
    """
    Returns (markdown_block_for_llm, structured_debug_bundle).

    `mode` biases supplemental knowledge types and soft caps; ranking stays global.
    """
    mode_l = (mode or "research").lower()
    if mode_l not in {"research", "decide", "build", "learn"}:
        mode_l = "research"

    project = db.get(Project, project_id)
    if project is None:
        raise ValueError("Project not found")

    lim = limits or default_limits_for_mode(mode_l)

    pinned_rows = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.is_pinned.is_(True),
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(
                KnowledgeItem.importance_score.desc().nulls_last(),
                KnowledgeItem.updated_at.desc(),
            )
            .limit(lim.max_pinned_knowledge)
        )
        .scalars()
        .all()
    )

    finding_rows = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "finding",
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(lim.max_recent_findings)
        )
        .scalars()
        .all()
    )

    conclusion_rows = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "conclusion",
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(lim.max_recent_conclusions)
        )
        .scalars()
        .all()
    )

    anchor_ids: set[uuid.UUID] = (
        {k.id for k in pinned_rows} | {k.id for k in finding_rows} | {k.id for k in conclusion_rows}
    )

    related: list[KnowledgeItem] = []
    if anchor_ids:
        rels = (
            db.execute(
                select(KnowledgeItemRelation).where(
                    or_(
                        KnowledgeItemRelation.from_knowledge_id.in_(anchor_ids),
                        KnowledgeItemRelation.to_knowledge_id.in_(anchor_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        peer_ids: set[uuid.UUID] = set()
        for r in rels:
            if r.from_knowledge_id in anchor_ids:
                peer_ids.add(r.to_knowledge_id)
            if r.to_knowledge_id in anchor_ids:
                peer_ids.add(r.from_knowledge_id)
        peer_ids -= anchor_ids
        if peer_ids:
            related = (
                db.execute(
                    select(KnowledgeItem).where(
                        KnowledgeItem.project_id == project_id,
                        KnowledgeItem.id.in_(peer_ids),
                        KnowledgeItem.is_archived.is_(False),
                    )
                )
                .scalars()
                .all()
            )
            related = rank_knowledge_for_context(related)[: lim.max_related_knowledge]

    sup_types = MODE_SUPPLEMENTAL_TYPES.get(mode_l, ())
    supplemental_rows: list[KnowledgeItem] = []
    if sup_types and lim.max_supplemental_knowledge > 0:
        supplemental_rows = (
            db.execute(
                select(KnowledgeItem)
                .where(
                    KnowledgeItem.project_id == project_id,
                    KnowledgeItem.type.in_(sup_types),
                    KnowledgeItem.is_archived.is_(False),
                )
                .order_by(KnowledgeItem.updated_at.desc())
                .limit(lim.max_supplemental_knowledge)
            )
            .scalars()
            .all()
        )

    merged = _dedupe_preserve_order(
        list(pinned_rows) + list(finding_rows) + list(conclusion_rows) + list(related) + list(supplemental_rows)
    )
    ranked_knowledge = rank_knowledge_for_context(merged)[: lim.max_knowledge_in_prompt]

    selection_for_id: dict[uuid.UUID, tuple[str, str]] = {}
    for k in pinned_rows:
        selection_for_id[k.id] = ("pinned", "pinned")
    for k in finding_rows:
        selection_for_id.setdefault(k.id, ("finding", "recent_finding"))
    for k in conclusion_rows:
        selection_for_id.setdefault(k.id, ("conclusion", "recent_conclusion"))
    for k in related:
        selection_for_id.setdefault(k.id, ("related", "graph_neighbor_of_priority_knowledge"))
    reason_supp = f"mode_{mode_l}_supplemental_types"
    for k in supplemental_rows:
        selection_for_id.setdefault(k.id, ("supplemental", reason_supp))

    task_rows = (
        db.execute(
            select(TaskItem)
            .where(
                TaskItem.project_id == project_id,
                TaskItem.status.in_(("todo", "in_progress")),
            )
            .order_by(TaskItem.priority.asc(), TaskItem.updated_at.desc())
            .limit(lim.max_open_tasks)
        )
        .scalars()
        .all()
    )

    artifact_rows = (
        db.execute(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.project_id == project_id)
            .order_by(GeneratedArtifact.updated_at.desc())
            .limit(lim.max_recent_artifacts)
        )
        .scalars()
        .all()
    )

    notes = _mode_context_notes(mode_l)
    notes.append(
        f"Counts — pinned:{len(pinned_rows)} findings:{len(finding_rows)} conclusions:{len(conclusion_rows)} "
        f"related:{len(related)} supplemental:{len(supplemental_rows)} → merged unique:{len(merged)} "
        f"→ after rank+cap:{len(ranked_knowledge)}.",
    )

    project_summary = ProjectSummaryRef(
        project_id=project.id,
        title=project.title,
        goal=project.goal,
        description_excerpt=truncate_text(project.description or "", 400) or None,
    )

    # --- Prompt block (compact, deterministic) ---
    header = f"## Retrieved project context (mode={mode_l}; curated, read-only)"
    lines: list[str] = [header, "", f"### Project: {project.title}"]
    if project_summary.description_excerpt:
        lines.append(project_summary.description_excerpt)

    k_lines: list[str] = []
    total_chars = 0
    for k in ranked_knowledge:
        excerpt = truncate_text(k.content, lim.max_chars_per_knowledge)
        role, reason = selection_for_id.get(k.id, ("supplemental", "ranked_merge"))
        block = (
            f"- **[{k.type}]** {k.title} (id={k.id}; pinned={k.is_pinned}; rank_role={role}; "
            f"why={reason}; importance={k.importance_score if k.importance_score is not None else 'n/a'})\n"
            f"  {excerpt}"
        )
        if total_chars + len(block) > lim.max_total_retrieval_chars:
            k_lines.append("- _(additional knowledge omitted due to size cap)_")
            break
        k_lines.append(block)
        total_chars += len(block)

    lines.append("### Knowledge")
    lines.extend(k_lines if k_lines else ["- _(none)_"])

    lines.append("### Open tasks")
    if task_rows:
        for t in task_rows:
            desc = truncate_text(t.description or "", 200)
            extra = f" — {desc}" if desc else ""
            lines.append(f"- [p{t.priority}] ({t.status}) {t.title}{extra}")
    else:
        lines.append("- _(none)_")

    lines.append("### Recent artifacts")
    if artifact_rows:
        for a in artifact_rows:
            excerpt = truncate_text(a.content, lim.max_chars_per_artifact)
            lines.append(f"- **[{a.artifact_type}]** {a.title}\n  {excerpt}")
    else:
        lines.append("- _(none)_")

    prompt_block = "\n".join(lines)

    knowledge_refs: list[RetrievedKnowledgeRef] = []
    for k in ranked_knowledge:
        role_s, reason_s = selection_for_id.get(k.id, ("supplemental", "ranked_merge"))
        knowledge_refs.append(
            RetrievedKnowledgeRef(
                id=k.id,
                type=k.type,
                title=k.title,
                content_excerpt=truncate_text(k.content, lim.max_chars_per_knowledge),
                is_pinned=bool(k.is_pinned),
                importance_score=k.importance_score,
                role=role_s,  # type: ignore[arg-type]
                selection_reason=reason_s,
            )
        )

    debug = SelectedContextDebug(
        mode=cast(Literal["research", "decide", "build", "learn"], mode_l),
        project_summary=project_summary,
        knowledge_items=knowledge_refs,
        tasks=[
            RetrievedTaskRef(id=t.id, title=t.title, status=t.status, priority=t.priority) for t in task_rows
        ],
        artifacts=[
            RetrievedArtifactRef(
                id=a.id,
                artifact_type=a.artifact_type,
                title=a.title,
                content_excerpt=truncate_text(a.content, lim.max_chars_per_artifact),
            )
            for a in artifact_rows
        ],
        context_notes=notes,
        caps={
            "max_pinned_knowledge": lim.max_pinned_knowledge,
            "max_recent_findings": lim.max_recent_findings,
            "max_recent_conclusions": lim.max_recent_conclusions,
            "max_supplemental_knowledge": lim.max_supplemental_knowledge,
            "max_related_knowledge": lim.max_related_knowledge,
            "max_knowledge_in_prompt": lim.max_knowledge_in_prompt,
            "max_open_tasks": lim.max_open_tasks,
            "max_recent_artifacts": lim.max_recent_artifacts,
            "max_chars_per_knowledge": lim.max_chars_per_knowledge,
            "max_chars_per_artifact": lim.max_chars_per_artifact,
            "max_total_retrieval_chars": lim.max_total_retrieval_chars,
            "selected_knowledge_count": len(ranked_knowledge),
            "selected_task_count": len(task_rows),
            "selected_artifact_count": len(artifact_rows),
        },
    )

    return prompt_block, debug
