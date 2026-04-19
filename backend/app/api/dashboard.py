from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.artifact import GeneratedArtifact
from app.models.knowledge import KnowledgeItem
from app.models.project import Project
from app.schemas.artifact import ArtifactRead
from app.schemas.dashboard import DashboardSummary
from app.schemas.knowledge import KnowledgeRead
from app.schemas.project import ProjectRead
from app.services.user_scope import get_or_create_default_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(db: Session = Depends(get_db)) -> DashboardSummary:
    user = get_or_create_default_user(db)
    projects = (
        db.execute(select(Project).where(Project.user_id == user.id).order_by(Project.updated_at.desc()).limit(8))
        .scalars()
        .all()
    )
    knowledge = (
        db.execute(
            select(KnowledgeItem)
            .join(Project, Project.id == KnowledgeItem.project_id)
            .where(Project.user_id == user.id, KnowledgeItem.is_archived.is_(False))
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(10)
        )
        .scalars()
        .all()
    )
    artifacts = (
        db.execute(
            select(GeneratedArtifact)
            .join(Project, Project.id == GeneratedArtifact.project_id)
            .where(Project.user_id == user.id)
            .order_by(GeneratedArtifact.updated_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )
    return DashboardSummary(
        recent_projects=[ProjectRead.model_validate(p) for p in projects],
        recent_knowledge=[KnowledgeRead.model_validate(k) for k in knowledge],
        recent_artifacts=[ArtifactRead.model_validate(a) for a in artifacts],
        default_user_id=user.id,
    )
