import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.artifact import ArtifactRead
from app.schemas.context_assembly import SelectedContextDebug
from app.schemas.knowledge import KnowledgeRead
from app.schemas.task import TaskRead


class AgentRunRequest(BaseModel):
    project_id: uuid.UUID
    conversation_id: uuid.UUID
    mode: Literal["research", "decide", "build", "learn"]
    prompt: str = Field(..., min_length=1)


class AgentRunResponse(BaseModel):
    assistant_message_id: uuid.UUID
    display_markdown: str
    structured: dict[str, Any]
    saved_knowledge: list[KnowledgeRead]
    saved_artifacts: list[ArtifactRead]
    saved_tasks: list[TaskRead]
    saved_source_ids: list[uuid.UUID]
    selected_context: SelectedContextDebug = Field(
        ...,
        description="Deterministic retrieval bundle (markdown is also derived from this selection)",
    )
