import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ArtifactCreate(BaseModel):
    artifact_type: str = Field(..., max_length=64)
    title: str = Field(..., max_length=500)
    content: str
    format: str = "markdown"
    is_pinned: bool = False
    importance_score: float | None = Field(default=None, ge=0.0, le=1.0)


class ArtifactRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    project_id: uuid.UUID
    artifact_type: str
    title: str
    content: str
    format: str = Field(validation_alias="content_format")
    is_pinned: bool = False
    importance_score: float | None = None
    created_at: datetime
    updated_at: datetime


class ArtifactUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    content: str | None = None
    format: str | None = None
    is_pinned: bool | None = None
    importance_score: float | None = Field(default=None, ge=0.0, le=1.0)
