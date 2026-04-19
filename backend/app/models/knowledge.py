import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class KnowledgeItemSourceLink(Base):
    """Citations: many sources per knowledge item (optional note / page locator)."""

    __tablename__ = "knowledge_item_source_links"

    knowledge_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_items.id", ondelete="CASCADE"), primary_key=True
    )
    source_record_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("source_records.id", ondelete="CASCADE"), primary_key=True
    )
    citation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    locator: Mapped[str | None] = mapped_column(String(200), nullable=True)

    knowledge_item = relationship("KnowledgeItem", back_populates="source_links")
    source_record = relationship("SourceRecord", back_populates="knowledge_links")


class KnowledgeItemRelation(Base):
    """Directed link between two knowledge items in the same project."""

    __tablename__ = "knowledge_item_relations"
    __table_args__ = (UniqueConstraint("from_knowledge_id", "to_knowledge_id", name="uq_knowledge_rel_edge"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_knowledge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_items.id", ondelete="CASCADE"), index=True
    )
    to_knowledge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("knowledge_items.id", ondelete="CASCADE"), index=True
    )
    relation_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    importance_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    verification_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="unverified", index=True
    )
    evidence_strength: Mapped[str] = mapped_column(String(16), nullable=False, default="medium")
    tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_by: Mapped[str] = mapped_column(String(32), nullable=False, default="system")
    embedding_ref: Mapped[str | None] = mapped_column(String(200), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    project = relationship("Project", back_populates="knowledge_items")
    source_links = relationship(
        "KnowledgeItemSourceLink", back_populates="knowledge_item", cascade="all, delete-orphan"
    )
