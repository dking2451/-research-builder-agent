import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.knowledge_evidence import SourceCitationOut


class KnowledgeRelationCreate(BaseModel):
    to_knowledge_id: uuid.UUID
    relation_type: str | None = Field(default=None, max_length=64)


class RelatedKnowledgeRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    knowledge_id: uuid.UUID
    title: str
    direction: str  # "outgoing" | "incoming"
    relation_type: str | None = None


class KnowledgeDetailRead(BaseModel):
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
    related: list[RelatedKnowledgeRef] = Field(default_factory=list)
    linked_sources: list[SourceCitationOut] = Field(default_factory=list)
