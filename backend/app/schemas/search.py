import uuid
from typing import Literal

from pydantic import BaseModel


class SearchHit(BaseModel):
    entity: Literal["project", "knowledge", "artifact", "message"]
    id: uuid.UUID
    project_id: uuid.UUID | None
    title: str
    snippet: str
