import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.conversation import Conversation, Message
from app.models.project import Project
from app.schemas.conversation import ConversationDetail, MessageCreate, MessageRead
from app.services.user_scope import get_or_create_default_user

router = APIRouter(tags=["conversations"])


def _assert_conv_access(db: Session, *, user_id: uuid.UUID, conversation_id: uuid.UUID) -> Conversation:
    conv = db.get(Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    project = db.get(Project, conv.project_id)
    if project is None or project.user_id != user_id:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: uuid.UUID, db: Session = Depends(get_db)) -> ConversationDetail:
    user = get_or_create_default_user(db)
    conv = _assert_conv_access(db, user_id=user.id, conversation_id=conversation_id)
    msgs = (
        db.execute(
            select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.asc())
        )
        .scalars()
        .all()
    )
    return ConversationDetail(
        id=conv.id,
        project_id=conv.project_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=[MessageRead.model_validate(m) for m in msgs],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageRead)
def post_message(
    conversation_id: uuid.UUID, payload: MessageCreate, db: Session = Depends(get_db)
) -> Message:
    user = get_or_create_default_user(db)
    _assert_conv_access(db, user_id=user.id, conversation_id=conversation_id)
    row = Message(conversation_id=conversation_id, role=payload.role, content=payload.content)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row
