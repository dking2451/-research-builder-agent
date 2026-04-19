import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.knowledge_evidence import KnowledgeCitationCreate


class KnowledgeRelatedEdgeIn(BaseModel):
    to_knowledge_id: uuid.UUID
    relation_type: str | None = Field(default=None, max_length=64)


class KnowledgeCreate(BaseModel):
    type: str = Field(..., max_length=40)
    title: str = Field(..., max_length=500)
    content: str
    source_name: str | None = None
    source_url: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    importance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    is_pinned: bool = False
    is_archived: bool = False
    verification_status: Literal["unverified", "partially_verified", "verified", "disputed"] = "unverified"
    evidence_strength: Literal["weak", "medium", "strong"] = "medium"
    tags: list[str] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_by: str = "user"
    related_to: list[KnowledgeRelatedEdgeIn] = Field(default_factory=list)
    source_citations: list[KnowledgeCitationCreate] = Field(default_factory=list)


class KnowledgeUpdate(BaseModel):
    type: str | None = Field(default=None, max_length=40)
    title: str | None = Field(default=None, max_length=500)
    content: str | None = None
    source_name: str | None = None
    source_url: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    importance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    is_pinned: bool | None = None
    is_archived: bool | None = None
    verification_status: Literal["unverified", "partially_verified", "verified", "disputed"] | None = None
    evidence_strength: Literal["weak", "medium", "strong"] | None = None
    tags: list[str] | None = None
    metadata_json: dict[str, Any] | None = None


class KnowledgeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    type: str
    title: str
    content: str
    source_name: str | None
    source_url: str | None
    confidence: float | None
    importance_score: float | None
    is_pinned: bool
    is_archived: bool
    verification_status: str
    evidence_strength: str
    tags: list | None
    metadata_json: dict | None
    created_by: str
    embedding_ref: str | None
    created_at: datetime
    updated_at: datetime
