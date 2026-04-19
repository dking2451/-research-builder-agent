import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.user import User


def get_or_create_default_user(db: Session) -> User:
    settings = get_settings()
    email = settings.default_user_email
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user:
        return user
    user = User(email=email, display_name="Owner")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def assert_project_owned(db: Session, *, user_id: uuid.UUID, project_id: uuid.UUID) -> None:
    from app.models.project import Project

    p = db.get(Project, project_id)
    if p is None or p.user_id != user_id:
        raise PermissionError("Project not found")
