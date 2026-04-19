from __future__ import annotations

import uuid
from typing import Sequence

from sqlalchemy import String, cast, or_, select, union_all
from sqlalchemy.orm import Session

from app.models.artifact import GeneratedArtifact
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeItem
from app.models.project import Project
from app.schemas.search import SearchHit


def search_all(db: Session, *, user_id: uuid.UUID, q: str, limit: int = 50) -> Sequence[SearchHit]:
    q = (q or "").strip()
    if not q:
        return []

    like = f"%{q}%"

    proj_stmt = (
        select(
            cast("project", String).label("entity"),
            Project.id.label("id"),
            Project.id.label("project_id"),
            Project.title.label("title"),
            Project.description.label("snippet"),
        )
        .where(Project.user_id == user_id)
        .where(or_(Project.title.ilike(like), Project.description.ilike(like), Project.goal.ilike(like)))
    )

    know_stmt = (
        select(
            cast("knowledge", String).label("entity"),
            KnowledgeItem.id.label("id"),
            KnowledgeItem.project_id.label("project_id"),
            KnowledgeItem.title.label("title"),
            KnowledgeItem.content.label("snippet"),
        )
        .join(Project, Project.id == KnowledgeItem.project_id)
        .where(Project.user_id == user_id, KnowledgeItem.is_archived.is_(False))
        .where(or_(KnowledgeItem.title.ilike(like), KnowledgeItem.content.ilike(like)))
    )

    art_stmt = (
        select(
            cast("artifact", String).label("entity"),
            GeneratedArtifact.id.label("id"),
            GeneratedArtifact.project_id.label("project_id"),
            GeneratedArtifact.title.label("title"),
            GeneratedArtifact.content.label("snippet"),
        )
        .join(Project, Project.id == GeneratedArtifact.project_id)
        .where(Project.user_id == user_id)
        .where(or_(GeneratedArtifact.title.ilike(like), GeneratedArtifact.content.ilike(like)))
    )

    msg_stmt = (
        select(
            cast("message", String).label("entity"),
            Message.id.label("id"),
            Conversation.project_id.label("project_id"),
            cast("Message", String).label("title"),
            Message.content.label("snippet"),
        )
        .select_from(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .join(Project, Project.id == Conversation.project_id)
        .where(Project.user_id == user_id)
        .where(Message.content.ilike(like))
    )

    stmt = union_all(proj_stmt, know_stmt, art_stmt, msg_stmt).limit(limit)
    rows = db.execute(stmt).all()
    hits: list[SearchHit] = []
    for entity, _id, project_id, title, snippet in rows:
        snippet_text = (snippet or "")[:240]
        hits.append(
            SearchHit(
                entity=entity,  # type: ignore[arg-type]
                id=_id,
                project_id=project_id,
                title=str(title)[:500],
                snippet=snippet_text,
            )
        )
    return hits
