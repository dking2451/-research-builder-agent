import uuid
from datetime import date, datetime

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(..., max_length=500)
    description: str | None = None
    status: str = "todo"
    priority: int = Field(default=2, ge=1, le=3)
    due_date: date | None = None
    metadata_json: dict[str, Any] | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    description: str | None = None
    status: str | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    due_date: date | None = None
    metadata_json: dict[str, Any] | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    description: str | None
    status: str
    priority: int
    due_date: date | None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime
