import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.knowledge import KnowledgeItem, KnowledgeItemRelation, KnowledgeItemSourceLink
from app.models.project import Project
from app.models.source import SourceRecord
from app.schemas.knowledge import KnowledgeCreate, KnowledgeRead, KnowledgeUpdate
from app.schemas.knowledge_evidence import KnowledgeCitationCreate, SourceCitationOut
from app.schemas.knowledge_evidence import normalize_evidence_strength, normalize_verification_status
from app.schemas.knowledge_relations import KnowledgeDetailRead, KnowledgeRelationCreate, RelatedKnowledgeRef
from app.services.user_scope import assert_project_owned, get_or_create_default_user

router = APIRouter(tags=["knowledge"])

_SORT_NEWEST = "newest"
_SORT_IMPORTANCE = "importance"
_SORT_PINNED_FIRST = "pinned_first"


def _knowledge_list_filters(
    stmt: Any,
    *,
    type: str | None,
    q: str | None,
    is_pinned: bool | None,
    verification_status: str | None,
    include_archived: bool,
) -> Any:
    if not include_archived:
        stmt = stmt.where(KnowledgeItem.is_archived.is_(False))
    if type:
        stmt = stmt.where(KnowledgeItem.type == type)
    if is_pinned is not None:
        stmt = stmt.where(KnowledgeItem.is_pinned.is_(bool(is_pinned)))
    if verification_status:
        stmt = stmt.where(KnowledgeItem.verification_status == verification_status.strip().lower())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(KnowledgeItem.title.ilike(like), KnowledgeItem.content.ilike(like)))
    return stmt


def _knowledge_list_order(stmt: Any, sort: str | None) -> Any:
    s = (sort or _SORT_NEWEST).strip().lower()
    if s == _SORT_IMPORTANCE:
        return stmt.order_by(KnowledgeItem.importance_score.desc().nulls_last(), KnowledgeItem.updated_at.desc())
    if s == _SORT_PINNED_FIRST:
        return stmt.order_by(
            KnowledgeItem.is_pinned.desc(),
            KnowledgeItem.importance_score.desc().nulls_last(),
            KnowledgeItem.updated_at.desc(),
        )
    return stmt.order_by(KnowledgeItem.updated_at.desc())


def _linked_sources_for_knowledge(db: Session, knowledge_id: uuid.UUID) -> list[SourceCitationOut]:
    links = (
        db.execute(select(KnowledgeItemSourceLink).where(KnowledgeItemSourceLink.knowledge_item_id == knowledge_id))
        .scalars()
        .all()
    )
    out: list[SourceCitationOut] = []
    for link in links:
        src = db.get(SourceRecord, link.source_record_id)
        if src is None:
            continue
        out.append(
            SourceCitationOut(
                source_record_id=src.id,
                title=src.title,
                url=src.url,
                source_type=src.source_type,
                citation_note=link.citation_note,
                locator=link.locator,
            )
        )
    return out


def _knowledge_to_detail(db: Session, row: KnowledgeItem) -> KnowledgeDetailRead:
    rels = (
        db.execute(
            select(KnowledgeItemRelation).where(
                or_(
                    KnowledgeItemRelation.from_knowledge_id == row.id,
                    KnowledgeItemRelation.to_knowledge_id == row.id,
                )
            )
        )
        .scalars()
        .all()
    )
    related: list[RelatedKnowledgeRef] = []
    for rel in rels:
        if rel.from_knowledge_id == row.id:
            peer_id = rel.to_knowledge_id
            direction = "outgoing"
        else:
            peer_id = rel.from_knowledge_id
            direction = "incoming"
        peer = db.get(KnowledgeItem, peer_id)
        if peer is None:
            continue
        related.append(
            RelatedKnowledgeRef(
                knowledge_id=peer.id,
                title=peer.title,
                direction=direction,
                relation_type=rel.relation_type,
            )
        )

    linked = _linked_sources_for_knowledge(db, row.id)

    return KnowledgeDetailRead(
        id=row.id,
        project_id=row.project_id,
        type=row.type,
        title=row.title,
        content=row.content,
        source_name=row.source_name,
        source_url=row.source_url,
        confidence=row.confidence,
        importance_score=row.importance_score,
        is_pinned=row.is_pinned,
        is_archived=row.is_archived,
        verification_status=row.verification_status,
        evidence_strength=row.evidence_strength,
        tags=row.tags,
        metadata_json=row.metadata_json,
        created_by=row.created_by,
        embedding_ref=row.embedding_ref,
        created_at=row.created_at,
        updated_at=row.updated_at,
        related=related,
        linked_sources=linked,
    )


@router.get("/knowledge/library", response_model=list[KnowledgeRead])
def list_knowledge_library(
    db: Session = Depends(get_db),
    project_id: uuid.UUID | None = Query(default=None),
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    q: str | None = Query(default=None),
    is_pinned: bool | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> list[KnowledgeItem]:
    user = get_or_create_default_user(db)

    stmt = select(KnowledgeItem).join(Project, Project.id == KnowledgeItem.project_id).where(Project.user_id == user.id)
    if project_id:
        stmt = stmt.where(KnowledgeItem.project_id == project_id)
    stmt = _knowledge_list_filters(
        stmt,
        type=type,
        q=q,
        is_pinned=is_pinned,
        verification_status=verification_status,
        include_archived=include_archived,
    )
    stmt = _knowledge_list_order(stmt, sort).limit(500)
    rows = db.execute(stmt).scalars().all()
    if tag:
        tag_l = tag.lower()
        rows = [r for r in rows if (r.tags or []) and any(str(t).lower() == tag_l for t in (r.tags or []))]
    return list(rows)


def _assert_knowledge_access(db: Session, *, user_id: uuid.UUID, knowledge_id: uuid.UUID) -> KnowledgeItem:
    row = db.get(KnowledgeItem, knowledge_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    try:
        assert_project_owned(db, user_id=user_id, project_id=row.project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return row


@router.get("/projects/{project_id}/knowledge", response_model=list[KnowledgeRead])
def list_knowledge(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    type: str | None = Query(default=None),
    tag: str | None = Query(default=None),
    q: str | None = Query(default=None),
    is_pinned: bool | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    sort: str | None = Query(default=None),
    include_archived: bool = Query(default=False),
) -> list[KnowledgeItem]:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")

    stmt = select(KnowledgeItem).where(KnowledgeItem.project_id == project_id)
    stmt = _knowledge_list_filters(
        stmt,
        type=type,
        q=q,
        is_pinned=is_pinned,
        verification_status=verification_status,
        include_archived=include_archived,
    )
    stmt = _knowledge_list_order(stmt, sort)
    rows = db.execute(stmt).scalars().all()
    if tag:
        tag_l = tag.lower()
        rows = [r for r in rows if (r.tags or []) and any(str(t).lower() == tag_l for t in (r.tags or []))]
    return list(rows)


@router.post("/projects/{project_id}/knowledge", response_model=KnowledgeRead)
def create_knowledge(
    project_id: uuid.UUID, payload: KnowledgeCreate, db: Session = Depends(get_db)
) -> KnowledgeItem:
    user = get_or_create_default_user(db)
    try:
        assert_project_owned(db, user_id=user.id, project_id=project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Project not found")
    row = KnowledgeItem(
        project_id=project_id,
        type=payload.type,
        title=payload.title,
        content=payload.content,
        source_name=payload.source_name,
        source_url=payload.source_url,
        confidence=payload.confidence,
        importance_score=payload.importance_score,
        is_pinned=payload.is_pinned,
        is_archived=payload.is_archived,
        verification_status=normalize_verification_status(payload.verification_status),
        evidence_strength=normalize_evidence_strength(payload.evidence_strength),
        tags=payload.tags,
        metadata_json=payload.metadata_json,
        created_by=payload.created_by,
    )
    db.add(row)
    db.flush()

    for edge in payload.related_to:
        peer = db.get(KnowledgeItem, edge.to_knowledge_id)
        if peer is None or peer.project_id != project_id:
            raise HTTPException(status_code=400, detail="Invalid related knowledge target")
        if peer.id == row.id:
            continue
        db.add(
            KnowledgeItemRelation(
                from_knowledge_id=row.id,
                to_knowledge_id=peer.id,
                relation_type=edge.relation_type or "related",
            )
        )

    for cit in payload.source_citations:
        src = db.get(SourceRecord, cit.source_record_id)
        if src is None or src.project_id != project_id:
            raise HTTPException(status_code=400, detail="Invalid source record for citation")
        db.add(
            KnowledgeItemSourceLink(
                knowledge_item_id=row.id,
                source_record_id=cit.source_record_id,
                citation_note=cit.citation_note,
                locator=cit.locator,
            )
        )

    db.commit()
    db.refresh(row)
    return row


@router.get("/knowledge/{knowledge_id}", response_model=KnowledgeDetailRead)
def get_knowledge(knowledge_id: uuid.UUID, db: Session = Depends(get_db)) -> KnowledgeDetailRead:
    user = get_or_create_default_user(db)
    row = _assert_knowledge_access(db, user_id=user.id, knowledge_id=knowledge_id)
    return _knowledge_to_detail(db, row)


@router.post("/knowledge/{knowledge_id}/relations", response_model=KnowledgeDetailRead)
def add_knowledge_relation(
    knowledge_id: uuid.UUID, payload: KnowledgeRelationCreate, db: Session = Depends(get_db)
) -> KnowledgeDetailRead:
    user = get_or_create_default_user(db)
    src = _assert_knowledge_access(db, user_id=user.id, knowledge_id=knowledge_id)
    dst = db.get(KnowledgeItem, payload.to_knowledge_id)
    if dst is None:
        raise HTTPException(status_code=404, detail="Target knowledge item not found")
    try:
        assert_project_owned(db, user_id=user.id, project_id=dst.project_id)
    except PermissionError:
        raise HTTPException(status_code=404, detail="Target knowledge item not found")
    if dst.project_id != src.project_id:
        raise HTTPException(status_code=400, detail="Knowledge items must belong to the same project")
    if dst.id == src.id:
        raise HTTPException(status_code=400, detail="Cannot relate a knowledge item to itself")

    exists = db.execute(
        select(KnowledgeItemRelation).where(
            KnowledgeItemRelation.from_knowledge_id == src.id,
            KnowledgeItemRelation.to_knowledge_id == dst.id,
        )
    ).scalar_one_or_none()
    if exists is None:
        db.add(
            KnowledgeItemRelation(
                from_knowledge_id=src.id,
                to_knowledge_id=dst.id,
                relation_type=payload.relation_type or "related",
            )
        )
    db.commit()
    db.refresh(src)
    return _knowledge_to_detail(db, src)


@router.post("/knowledge/{knowledge_id}/citations", response_model=KnowledgeDetailRead)
def add_knowledge_citation(
    knowledge_id: uuid.UUID, payload: KnowledgeCitationCreate, db: Session = Depends(get_db)
) -> KnowledgeDetailRead:
    user = get_or_create_default_user(db)
    row = _assert_knowledge_access(db, user_id=user.id, knowledge_id=knowledge_id)
    src = db.get(SourceRecord, payload.source_record_id)
    if src is None or src.project_id != row.project_id:
        raise HTTPException(status_code=400, detail="Invalid source record for this project")

    existing = db.execute(
        select(KnowledgeItemSourceLink).where(
            KnowledgeItemSourceLink.knowledge_item_id == row.id,
            KnowledgeItemSourceLink.source_record_id == payload.source_record_id,
        )
    ).scalar_one_or_none()
    if existing is None:
        db.add(
            KnowledgeItemSourceLink(
                knowledge_item_id=row.id,
                source_record_id=payload.source_record_id,
                citation_note=payload.citation_note,
                locator=payload.locator,
            )
        )
    else:
        existing.citation_note = payload.citation_note
        existing.locator = payload.locator
        db.add(existing)
    db.commit()
    db.refresh(row)
    return _knowledge_to_detail(db, row)


@router.delete("/knowledge/{knowledge_id}/citations/{source_record_id}", response_model=KnowledgeDetailRead)
def remove_knowledge_citation(
    knowledge_id: uuid.UUID, source_record_id: uuid.UUID, db: Session = Depends(get_db)
) -> KnowledgeDetailRead:
    user = get_or_create_default_user(db)
    row = _assert_knowledge_access(db, user_id=user.id, knowledge_id=knowledge_id)
    link = db.execute(
        select(KnowledgeItemSourceLink).where(
            KnowledgeItemSourceLink.knowledge_item_id == row.id,
            KnowledgeItemSourceLink.source_record_id == source_record_id,
        )
    ).scalar_one_or_none()
    if link:
        db.delete(link)
    db.commit()
    db.refresh(row)
    return _knowledge_to_detail(db, row)


@router.patch("/knowledge/{knowledge_id}", response_model=KnowledgeRead)
def patch_knowledge(
    knowledge_id: uuid.UUID, payload: KnowledgeUpdate, db: Session = Depends(get_db)
) -> KnowledgeItem:
    user = get_or_create_default_user(db)
    row = _assert_knowledge_access(db, user_id=user.id, knowledge_id=knowledge_id)
    data = payload.model_dump(exclude_unset=True)
    if "verification_status" in data and data["verification_status"] is not None:
        data["verification_status"] = normalize_verification_status(data["verification_status"])
    if "evidence_strength" in data and data["evidence_strength"] is not None:
        data["evidence_strength"] = normalize_evidence_strength(data["evidence_strength"])
    for k, v in data.items():
        setattr(row, k, v)
    row.updated_at = datetime.now(tz=UTC)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/knowledge/{knowledge_id}", status_code=204)
def delete_knowledge(knowledge_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    user = get_or_create_default_user(db)
    row = _assert_knowledge_access(db, user_id=user.id, knowledge_id=knowledge_id)
    db.delete(row)
    db.commit()
