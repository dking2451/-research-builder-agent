"""Assemble project command center payload (overview, open loops, activity timeline)."""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.artifact import GeneratedArtifact
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeItem
from app.models.task import TaskItem
from app.schemas.artifact import ArtifactRead
from app.schemas.knowledge import KnowledgeRead
from app.schemas.project_command_center import ActivityEvent, OpenLoopItem, ProjectCommandCenter
from app.schemas.task import TaskRead


def build_open_loops(
    *,
    questions: Sequence[KnowledgeItem],
    open_tasks: Sequence[TaskItem],
    low_conf_findings: Sequence[KnowledgeItem],
    unverified_claims: Sequence[KnowledgeItem],
    max_items: int = 24,
) -> list[OpenLoopItem]:
    """Deterministic merge: tasks, questions, findings, claims (each bucket capped)."""
    out: list[OpenLoopItem] = []
    cap_each = max(4, max_items // 4)

    for t in open_tasks[:cap_each]:
        out.append(
            OpenLoopItem(
                kind="open_task",
                entity="task",
                id=t.id,
                title=t.title,
                reason=f"Status {t.status} · priority {t.priority}",
            )
        )
    for k in questions[:cap_each]:
        out.append(
            OpenLoopItem(
                kind="open_question",
                entity="knowledge",
                id=k.id,
                title=k.title,
                reason="Open question (knowledge type)",
            )
        )
    for k in low_conf_findings[:cap_each]:
        c = k.confidence
        reason = "Finding with no confidence set" if c is None else f"Finding with low confidence ({c:.2f})"
        out.append(
            OpenLoopItem(
                kind="low_confidence_finding",
                entity="knowledge",
                id=k.id,
                title=k.title,
                reason=reason,
            )
        )
    for k in unverified_claims[:cap_each]:
        out.append(
            OpenLoopItem(
                kind="unverified_claim",
                entity="knowledge",
                id=k.id,
                title=k.title,
                reason="Claim not yet verified",
            )
        )
    return out[:max_items]


def build_project_command_center(db: Session, *, project_id: uuid.UUID) -> ProjectCommandCenter:
    pinned = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.is_pinned.is_(True),
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.importance_score.desc().nulls_last(), KnowledgeItem.updated_at.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    findings = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "finding",
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )
    conclusions = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "conclusion",
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(6)
        )
        .scalars()
        .all()
    )
    questions = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "question",
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(12)
        )
        .scalars()
        .all()
    )
    open_tasks = (
        db.execute(
            select(TaskItem)
            .where(TaskItem.project_id == project_id, TaskItem.status.in_(("todo", "in_progress")))
            .order_by(TaskItem.priority.asc(), TaskItem.updated_at.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    artifacts = (
        db.execute(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.project_id == project_id)
            .order_by(GeneratedArtifact.is_pinned.desc(), GeneratedArtifact.updated_at.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )

    low_conf_findings = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "finding",
                KnowledgeItem.is_archived.is_(False),
                or_(KnowledgeItem.confidence.is_(None), KnowledgeItem.confidence < 0.45),
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(12)
        )
        .scalars()
        .all()
    )
    unverified_claims = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "claim",
                KnowledgeItem.is_archived.is_(False),
                KnowledgeItem.verification_status == "unverified",
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(12)
        )
        .scalars()
        .all()
    )

    loops = build_open_loops(
        questions=questions,
        open_tasks=open_tasks,
        low_conf_findings=low_conf_findings,
        unverified_claims=unverified_claims,
    )

    timeline = _build_timeline(db, project_id=project_id)

    return ProjectCommandCenter(
        project_id=project_id,
        pinned_knowledge=[KnowledgeRead.model_validate(x) for x in pinned],
        key_findings=[KnowledgeRead.model_validate(x) for x in findings],
        latest_conclusions=[KnowledgeRead.model_validate(x) for x in conclusions],
        open_questions=[KnowledgeRead.model_validate(x) for x in questions],
        next_tasks=[TaskRead.model_validate(x) for x in open_tasks],
        recent_artifacts=[ArtifactRead.model_validate(x) for x in artifacts],
        open_loops=loops,
        timeline=timeline,
    )


def _build_timeline(db: Session, *, project_id: uuid.UUID, limit: int = 28) -> list[ActivityEvent]:
    conv_ids = (
        db.execute(select(Conversation.id).where(Conversation.project_id == project_id)).scalars().all()
    )
    raw: list[ActivityEvent] = []
    if conv_ids:
        msgs = (
            db.execute(
                select(Message)
                .where(Message.conversation_id.in_(conv_ids))
                .order_by(Message.created_at.desc())
                .limit(18)
            )
            .scalars()
            .all()
        )
        for m in msgs:
            snippet = (m.content or "").replace("\n", " ").strip()[:80]
            raw.append(
                ActivityEvent(
                    occurred_at=m.created_at,
                    kind="message",
                    entity_id=m.id,
                    title=f"{m.role}: {(m.content or '')[:60]}{'…' if len(m.content or '') > 60 else ''}",
                    subtitle=snippet + ("…" if len(m.content or "") > 80 else ""),
                )
            )

    know = (
        db.execute(
            select(KnowledgeItem)
            .where(KnowledgeItem.project_id == project_id, KnowledgeItem.is_archived.is_(False))
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(12)
        )
        .scalars()
        .all()
    )
    for k in know:
        raw.append(
            ActivityEvent(
                occurred_at=k.updated_at,
                kind="knowledge",
                entity_id=k.id,
                title=k.title,
                subtitle=k.type,
            )
        )

    arts = (
        db.execute(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.project_id == project_id)
            .order_by(GeneratedArtifact.updated_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )
    for a in arts:
        raw.append(
            ActivityEvent(
                occurred_at=a.updated_at,
                kind="artifact",
                entity_id=a.id,
                title=a.title,
                subtitle=a.artifact_type,
            )
        )

    trows = (
        db.execute(
            select(TaskItem)
            .where(TaskItem.project_id == project_id)
            .order_by(TaskItem.updated_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )
    for t in trows:
        raw.append(
            ActivityEvent(
                occurred_at=t.updated_at,
                kind="task",
                entity_id=t.id,
                title=t.title,
                subtitle=t.status,
            )
        )

    raw.sort(key=lambda e: e.occurred_at.timestamp(), reverse=True)
    return raw[:limit]
