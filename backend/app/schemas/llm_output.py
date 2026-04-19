"""Structured outputs expected from the LLM (OpenAI parse / JSON recovery)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    title: str
    content: str
    source_name: str | None = None
    source_url: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    importance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    is_pinned: bool = False
    verification_status: str | None = None
    evidence_strength: str | None = None
    linked_source_urls: list[str] = Field(default_factory=list)
    related_titles: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class SourceDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    url: str | None = None
    source_type: str | None = None
    author: str | None = None
    notes: str | None = None
    credibility_score: float | None = Field(default=None, ge=0.0, le=1.0)


class ArtifactDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    artifact_type: str
    title: str
    content: str
    format: str = "markdown"


class TaskDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str | None = None
    status: Literal["todo", "in_progress", "done"] = "todo"
    priority: int = Field(default=2, ge=1, le=3)
    due_date: str | None = None  # ISO date string optional


class AgentLLMEnvelope(BaseModel):
    """Root object returned by the model for all modes."""

    model_config = ConfigDict(extra="forbid")

    display_markdown: str
    knowledge_items: list[KnowledgeDraft] = Field(default_factory=list)
    source_records: list[SourceDraft] = Field(default_factory=list)
    artifacts: list[ArtifactDraft] = Field(default_factory=list)
    tasks: list[TaskDraft] = Field(default_factory=list)
