import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.artifact import ArtifactRead
from app.schemas.knowledge import KnowledgeRead
from app.schemas.project import ProjectRead


class DashboardSummary(BaseModel):
    recent_projects: list[ProjectRead]
    recent_knowledge: list[KnowledgeRead]
    recent_artifacts: list[ArtifactRead]
    default_user_id: uuid.UUID
