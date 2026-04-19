import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.artifact import GeneratedArtifact
from app.models.conversation import Conversation
from app.models.knowledge import KnowledgeItem
from app.models.project import Project
from app.models.source import SourceRecord
from app.models.task import TaskItem
from app.schemas.artifact import ArtifactRead
from app.schemas.conversation import ConversationCreate, ConversationRead
from app.schemas.knowledge import KnowledgeRead
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.schemas.knowledge_evidence import SourceRecordSummary
from app.schemas.project_command_center import ProjectCommandCenter
from app.schemas.project_digest import ProjectDigest
from app.schemas.task import TaskRead
from app.services.project_command_center_service import build_project_command_center
from app.services.user_scope import assert_project_owned, get_or_create_default_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    user = get_or_create_default_user(db)
    row = Project(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        goal=payload.goal,
        mode_default=payload.mode_default,
        status=payload.status,
        tags=payload.tags,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    user = get_or_create_default_user(db)
    rows = db.execute(select(Project).where(Project.user_id == user.id).order_by(Project.updated_at.desc())).scalars().all()
    return list(rows)


@router.get("/{project_id}/digest", response_model=ProjectDigest)
def get_project_digest(project_id: uuid.UUID, db: Session = Depends(get_db)) -> ProjectDigest:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")

    pinned = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.is_pinned.is_(True),
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.importance_score.desc().nulls_last(), KnowledgeItem.updated_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )
    findings = (
        db.execute(
            select(KnowledgeItem)
            .where(
                KnowledgeItem.project_id == project_id,
                KnowledgeItem.type == "finding",
                KnowledgeItem.is_archived.is_(False),
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )
    artifacts = (
        db.execute(
            select(GeneratedArtifact)
            .where(GeneratedArtifact.project_id == project_id)
            .order_by(GeneratedArtifact.updated_at.desc())
            .limit(5)
        )
        .scalars()
        .all()
    )
    tasks = (
        db.execute(
            select(TaskItem)
            .where(TaskItem.project_id == project_id, TaskItem.status.in_(("todo", "in_progress")))
            .order_by(TaskItem.priority.asc(), TaskItem.updated_at.desc())
            .limit(8)
        )
        .scalars()
        .all()
    )

    return ProjectDigest(
        project_id=project_id,
        pinned_knowledge=[KnowledgeRead.model_validate(x) for x in pinned],
        latest_findings=[KnowledgeRead.model_validate(x) for x in findings],
        latest_artifacts=[ArtifactRead.model_validate(x) for x in artifacts],
        next_tasks=[TaskRead.model_validate(x) for x in tasks],
    )


@router.get("/{project_id}/command-center", response_model=ProjectCommandCenter)
def get_project_command_center(project_id: uuid.UUID, db: Session = Depends(get_db)) -> ProjectCommandCenter:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    return build_project_command_center(db, project_id=project_id)


@router.get("/{project_id}/source-records", response_model=list[SourceRecordSummary])
def list_project_source_records(project_id: uuid.UUID, db: Session = Depends(get_db)) -> list[SourceRecordSummary]:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    rows = (
        db.execute(
            select(SourceRecord)
            .where(SourceRecord.project_id == project_id)
            .order_by(SourceRecord.updated_at.desc())
            .limit(200)
        )
        .scalars()
        .all()
    )
    return [SourceRecordSummary.model_validate(x) for x in rows]


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db)) -> Project:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    row = db.get(Project, project_id)
    assert row is not None
    return row


@router.patch("/{project_id}", response_model=ProjectRead)
def patch_project(
    project_id: uuid.UUID, payload: ProjectUpdate, db: Session = Depends(get_db)
) -> Project:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    row = db.get(Project, project_id)
    assert row is not None
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/{project_id}/conversations", response_model=ConversationRead)
def create_conversation(
    project_id: uuid.UUID, payload: ConversationCreate, db: Session = Depends(get_db)
) -> Conversation:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    row = Conversation(project_id=project_id, title=payload.title)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{project_id}/conversations", response_model=list[ConversationRead])
def list_conversations(project_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Conversation]:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    rows = (
        db.execute(
            select(Conversation)
            .where(Conversation.project_id == project_id)
            .order_by(Conversation.updated_at.desc())
        )
        .scalars()
        .all()
    )
    return list(rows)
