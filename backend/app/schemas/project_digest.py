import uuid

from pydantic import BaseModel

from app.schemas.artifact import ArtifactRead
from app.schemas.knowledge import KnowledgeRead
from app.schemas.task import TaskRead


class ProjectDigest(BaseModel):
    project_id: uuid.UUID
    pinned_knowledge: list[KnowledgeRead]
    latest_findings: list[KnowledgeRead]
    latest_artifacts: list[ArtifactRead]
    next_tasks: list[TaskRead]
