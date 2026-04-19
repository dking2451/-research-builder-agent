from __future__ import annotations

import re
import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeItem, KnowledgeItemRelation, KnowledgeItemSourceLink
from app.models.project import Project
from app.models.source import SourceRecord
from app.models.task import TaskItem
from app.schemas.agent import AgentRunResponse
from app.schemas.artifact import ArtifactRead
from app.schemas.knowledge import KnowledgeRead
from app.schemas.llm_output import AgentLLMEnvelope
from app.schemas.task import TaskRead
from app.services.artifact_service import create_artifact_from_draft
from app.services.context_assembly_service import assemble_retrieval_context
from app.services.extraction_pipeline import process_agent_envelope
from app.services.knowledge_extraction_service import normalize_knowledge_draft
from app.services.openai_client import run_stub_agent, run_structured_agent
from app.services.research_service import build_project_context_block


def _title_key(title: str) -> str:
    return re.sub(r"\s+", " ", (title or "").strip().lower())


def _recent_conversation_text(db: Session, conversation_id: uuid.UUID, limit: int = 12) -> str:
    msgs = (
        db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    msgs = list(reversed(msgs))
    lines: list[str] = []
    for m in msgs:
        lines.append(f"{m.role.upper()}: {m.content}")
    return "\n".join(lines)


def run_agent(
    db: Session,
    *,
    project_id: uuid.UUID,
    conversation_id: uuid.UUID,
    mode: str,
    prompt: str,
) -> AgentRunResponse:
    if mode not in {"research", "decide", "build", "learn"}:
        raise ValueError("Invalid mode")

    project = db.get(Project, project_id)
    if project is None:
        raise ValueError("Project not found")
    conv = db.get(Conversation, conversation_id)
    if conv is None or conv.project_id != project_id:
        raise ValueError("Conversation not found")

    user_msg = Message(conversation_id=conversation_id, role="user", content=prompt)
    db.add(user_msg)
    db.flush()

    project_ctx = build_project_context_block(
        title=project.title, goal=project.goal, description=project.description
    )
    retrieval_block, selected_ctx = assemble_retrieval_context(db, project_id=project_id, mode=mode)
    conv_ctx = _recent_conversation_text(db, conversation_id)

    settings = get_settings()
    envelope: AgentLLMEnvelope
    if settings.use_stub_agent or not settings.openai_api_key.strip():
        envelope = run_stub_agent(mode=mode, user_prompt=prompt, retrieval_context_block=retrieval_block)
    else:
        envelope = run_structured_agent(
            mode=mode,
            user_prompt=prompt,
            project_context=project_ctx,
            retrieval_context_block=retrieval_block,
            conversation_context=conv_ctx,
        )

    processed = process_agent_envelope(envelope, mode=mode)
    envelope = processed.envelope

    assistant = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=envelope.display_markdown,
    )
    db.add(assistant)
    db.flush()

    saved_sources: list[SourceRecord] = []
    url_to_source: dict[str, uuid.UUID] = {}
    for s in envelope.source_records:
        row = SourceRecord(
            project_id=project_id,
            title=s.title[:500],
            url=s.url,
            source_type=s.source_type,
            author=s.author,
            published_at=None,
            retrieved_at=datetime.now(tz=UTC),
            notes=s.notes,
            credibility_score=s.credibility_score,
        )
        db.add(row)
        db.flush()
        saved_sources.append(row)
        if s.url:
            url_to_source[s.url.strip()] = row.id

    norm_drafts = [normalize_knowledge_draft(k) for k in envelope.knowledge_items]
    saved_knowledge: list[KnowledgeItem] = []
    for nk in norm_drafts:
        row = KnowledgeItem(
            project_id=project_id,
            type=nk.type,
            title=nk.title,
            content=nk.content,
            source_name=nk.source_name,
            source_url=nk.source_url,
            confidence=nk.confidence,
            importance_score=nk.importance_score,
            is_pinned=bool(nk.is_pinned),
            verification_status=nk.verification_status or "unverified",
            evidence_strength=nk.evidence_strength or "medium",
            tags=nk.tags or [],
            metadata_json=nk.metadata or {},
            created_by="system",
        )
        db.add(row)
        db.flush()
        saved_knowledge.append(row)
        link_urls: list[str] = []
        if nk.source_url and nk.source_url.strip():
            link_urls.append(nk.source_url.strip())
        for u in nk.linked_source_urls or []:
            u = (u or "").strip()
            if u and u not in link_urls:
                link_urls.append(u)
        seen_sid: set[uuid.UUID] = set()
        for u in link_urls:
            sid = url_to_source.get(u)
            if sid and sid not in seen_sid:
                seen_sid.add(sid)
                db.add(KnowledgeItemSourceLink(knowledge_item_id=row.id, source_record_id=sid))

    title_to_id: dict[str, uuid.UUID] = {}
    for row in saved_knowledge:
        key = _title_key(row.title)
        if key and key not in title_to_id:
            title_to_id[key] = row.id

    seen_edges: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for row, nk in zip(saved_knowledge, norm_drafts, strict=True):
        for rt in nk.related_titles:
            tid = title_to_id.get(_title_key(rt))
            if not tid or tid == row.id:
                continue
            edge = (row.id, tid)
            if edge in seen_edges:
                continue
            seen_edges.add(edge)
            db.add(KnowledgeItemRelation(from_knowledge_id=row.id, to_knowledge_id=tid, relation_type="related"))
    relation_edges_saved = len(seen_edges)

    saved_artifacts = []
    for a in envelope.artifacts:
        saved_artifacts.append(create_artifact_from_draft(db, project_id=project_id, draft=a))

    saved_tasks: list[TaskItem] = []
    for t in envelope.tasks:
        due: date | None = None
        if t.due_date:
            try:
                due = date.fromisoformat(t.due_date)
            except ValueError:
                due = None
        row = TaskItem(
            project_id=project_id,
            title=t.title[:500],
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=due,
            metadata_json={
                "source": "agent_run",
                "assistant_message_id": str(assistant.id),
            },
        )
        db.add(row)
        db.flush()
        saved_tasks.append(row)

    db.commit()

    structured: dict[str, Any] = {
        "knowledge_count": len(saved_knowledge),
        "artifact_count": len(saved_artifacts),
        "task_count": len(saved_tasks),
        "source_count": len(saved_sources),
        "relation_edges_saved": relation_edges_saved,
        "retrieval_knowledge_selected": len(selected_ctx.knowledge_items),
        "retrieval_tasks_selected": len(selected_ctx.tasks),
        "retrieval_artifacts_selected": len(selected_ctx.artifacts),
    }

    return AgentRunResponse(
        assistant_message_id=assistant.id,
        display_markdown=envelope.display_markdown,
        structured=structured,
        saved_knowledge=[KnowledgeRead.model_validate(x) for x in saved_knowledge],
        saved_artifacts=[ArtifactRead.model_validate(x) for x in saved_artifacts],
        saved_tasks=[TaskRead.model_validate(x) for x in saved_tasks],
        saved_source_ids=[x.id for x in saved_sources],
        selected_context=selected_ctx,
    )
