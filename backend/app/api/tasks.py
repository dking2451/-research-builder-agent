import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.task import TaskItem
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate
from app.services.user_scope import assert_project_owned, get_or_create_default_user

router = APIRouter(tags=["tasks"])


def _assert_task_access(db: Session, *, user_id: uuid.UUID, task_id: uuid.UUID) -> TaskItem:
    row = db.get(TaskItem, task_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        assert_project_owned(db, user_id=user_id, project_id=row.project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Task not found")
    return row


@router.get("/projects/{project_id}/tasks", response_model=list[TaskRead])
def list_tasks(project_id: uuid.UUID, db: Session = Depends(get_db)) -> list[TaskItem]:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    rows = (
        db.execute(select(TaskItem).where(TaskItem.project_id == project_id).order_by(TaskItem.updated_at.desc()))
        .scalars()
        .all()
    )
    return list(rows)


@router.post("/projects/{project_id}/tasks", response_model=TaskRead)
def create_task(project_id: uuid.UUID, payload: TaskCreate, db: Session = Depends(get_db)) -> TaskItem:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    row = TaskItem(
        project_id=project_id,
        title=payload.title,
        description=payload.description,
        status=payload.status,
        priority=payload.priority,
        due_date=payload.due_date,
        metadata_json=payload.metadata_json,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def patch_task(task_id: uuid.UUID, payload: TaskUpdate, db: Session = Depends(get_db)) -> TaskItem:
    user = get_or_create_default_user(db)
    row = _assert_task_access(db, user_id=user.id, task_id=task_id)
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = datetime.now(tz=UTC)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
