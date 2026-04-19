"""Structured retrieval context for agent runs (deterministic, explainable)."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProjectSummaryRef(BaseModel):
    """Compact static project fields included with retrieval context."""

    project_id: uuid.UUID
    title: str
    goal: str | None = None
    description_excerpt: str | None = Field(
        default=None, description="Truncated description for prompt + debug"
    )


class RetrievedKnowledgeRef(BaseModel):
    id: uuid.UUID
    type: str
    title: str
    content_excerpt: str = Field(..., description="Truncated body used in the prompt")
    is_pinned: bool
    importance_score: float | None
    role: Literal["pinned", "finding", "conclusion", "related", "supplemental"]
    selection_reason: str = Field(
        ...,
        description="Why this row entered the bundle (e.g. recent_finding, related_to_priority)",
    )


class RetrievedTaskRef(BaseModel):
    id: uuid.UUID
    title: str
    status: str
    priority: int


class RetrievedArtifactRef(BaseModel):
    id: uuid.UUID
    artifact_type: str
    title: str
    content_excerpt: str


class SelectedContextDebug(BaseModel):
    """
    Full retrieval bundle passed to the model (echoed in /agent/run for inspection).

    `knowledge_items` is the final capped, ranked list after merge + dedupe.
    """

    mode: Literal["research", "decide", "build", "learn"]
    project_summary: ProjectSummaryRef
    knowledge_items: list[RetrievedKnowledgeRef] = Field(default_factory=list)
    tasks: list[RetrievedTaskRef] = Field(default_factory=list)
    artifacts: list[RetrievedArtifactRef] = Field(default_factory=list)
    context_notes: list[str] = Field(
        default_factory=list,
        description="Human-readable notes on caps, mode shaping, and merge order",
    )
    caps: dict[str, Any] = Field(default_factory=dict)


# Backward-compatible alias for imports / older references
AgentContextAssemblyDebug = SelectedContextDebug
