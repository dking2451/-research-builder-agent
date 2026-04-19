import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.artifact import GeneratedArtifact
from app.models.project import Project
from app.schemas.artifact import ArtifactCreate, ArtifactRead, ArtifactUpdate
from app.services.artifact_service import create_artifact_from_draft
from app.services.user_scope import assert_project_owned, get_or_create_default_user
from app.schemas.llm_output import ArtifactDraft

router = APIRouter(tags=["artifacts"])


def _assert_artifact_access(db: Session, *, user_id: uuid.UUID, artifact_id: uuid.UUID) -> GeneratedArtifact:
    row = db.get(GeneratedArtifact, artifact_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Artifact not found")
    try:
        assert_project_owned(db, user_id=user_id, project_id=row.project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return row


@router.get("/artifacts/library", response_model=list[ArtifactRead])
def list_artifact_library(
    db: Session = Depends(get_db),
    project_id: uuid.UUID | None = Query(default=None),
    artifact_type: str | None = Query(default=None, alias="type"),
    q: str | None = Query(default=None),
) -> list[GeneratedArtifact]:
    user = get_or_create_default_user(db)
    stmt = (
        select(GeneratedArtifact)
        .join(Project, Project.id == GeneratedArtifact.project_id)
        .where(Project.user_id == user.id)
    )
    if project_id:
        stmt = stmt.where(GeneratedArtifact.project_id == project_id)
    if artifact_type:
        stmt = stmt.where(GeneratedArtifact.artifact_type == artifact_type)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(GeneratedArtifact.title.ilike(like), GeneratedArtifact.content.ilike(like)))
    stmt = stmt.order_by(GeneratedArtifact.updated_at.desc()).limit(500)
    return list(db.execute(stmt).scalars().all())


@router.get("/projects/{project_id}/artifacts", response_model=list[ArtifactRead])
def list_artifacts(project_id: uuid.UUID, db: Session = Depends(get_db)) -> list[GeneratedArtifact]:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    rows = (
        db.execute(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.project_id == project_id)
            .order_by(GeneratedArtifact.updated_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)


@router.post("/projects/{project_id}/artifacts", response_model=ArtifactRead)
def create_artifact(project_id: uuid.UUID, payload: ArtifactCreate, db: Session = Depends(get_db)) -> GeneratedArtifact:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    draft = ArtifactDraft(
        artifact_type=payload.artifact_type,
        title=payload.title,
        content=payload.content,
        format=payload.format,
    )
    row = create_artifact_from_draft(db, project_id=project_id, draft=draft)
    row.is_pinned = bool(payload.is_pinned)
    row.importance_score = payload.importance_score
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
def get_artifact(artifact_id: uuid.UUID, db: Session = Depends(get_db)) -> GeneratedArtifact:
    user = get_or_create_default_user(db)
    return _assert_artifact_access(db, user_id=user.id, artifact_id=artifact_id)


@router.patch("/artifacts/{artifact_id}", response_model=ArtifactRead)
def patch_artifact(
    artifact_id: uuid.UUID, payload: ArtifactUpdate, db: Session = Depends(get_db)
) -> GeneratedArtifact:
    user = get_or_create_default_user(db)
    row = _assert_artifact_access(db, user_id=user.id, artifact_id=artifact_id)
    data = payload.model_dump(exclude_unset=True)
    if "format" in data and data["format"] is not None:
        data["content_format"] = data.pop("format")
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = datetime.now(tz=UTC)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
