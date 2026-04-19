"""Rich project overview for the command center UI."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.artifact import ArtifactRead
from app.schemas.knowledge import KnowledgeRead
from app.schemas.task import TaskRead


class OpenLoopItem(BaseModel):
    """Single actionable open loop (V1 heuristic)."""

    kind: Literal["open_question", "open_task", "low_confidence_finding", "unverified_claim"]
    entity: Literal["knowledge", "task"]
    id: uuid.UUID
    title: str
    reason: str


class ActivityEvent(BaseModel):
    occurred_at: datetime
    kind: Literal["message", "knowledge", "artifact", "task"]
    entity_id: uuid.UUID
    title: str
    subtitle: str | None = None


class ProjectCommandCenter(BaseModel):
    project_id: uuid.UUID
    pinned_knowledge: list[KnowledgeRead]
    key_findings: list[KnowledgeRead]
    latest_conclusions: list[KnowledgeRead]
    open_questions: list[KnowledgeRead]
    next_tasks: list[TaskRead]
    recent_artifacts: list[ArtifactRead]
    open_loops: list[OpenLoopItem]
    timeline: list[ActivityEvent]
