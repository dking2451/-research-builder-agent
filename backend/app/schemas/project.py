import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    goal: str | None = None
    mode_default: str | None = None
    status: str = "active"
    tags: list[str] = Field(default_factory=list)


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    goal: str | None = None
    mode_default: str | None = None
    status: str | None = None
    tags: list[str] | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None
    goal: str | None
    mode_default: str | None
    status: str
    tags: list | None
    created_at: datetime
    updated_at: datetime
