"""
Seed demo content for the default user:
- one research project
- one decision project
- one build project

Run from `backend/`:
  python -m scripts.seed_demo
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, date, datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select

from app.config import get_settings
from app.database import init_db
from app.models.artifact import GeneratedArtifact
from app.models.conversation import Conversation, Message
from app.models.knowledge import KnowledgeItem, KnowledgeItemRelation, KnowledgeItemSourceLink
from app.models.project import Project
from app.models.source import SourceRecord
from app.models.task import TaskItem
from app.models.user import User

RESEARCH_TITLE = "Seed: Research — vector databases for personal RAG"
DECIDE_TITLE = "Seed: Decide — buy vs build for a personal agent"
BUILD_TITLE = "Seed: Build — Research Builder Agent V1 hardening"


def main() -> None:
    settings = get_settings()
    init_db(settings.database_url)
    from app.database import _SessionLocal  # type: ignore[attr-defined]

    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == settings.default_user_email)).scalar_one_or_none()
        if user is None:
            user = User(email=settings.default_user_email, display_name="Owner")
            db.add(user)
            db.commit()
            db.refresh(user)

        existing_titles = {
            str(t)
            for t in db.execute(select(Project.title).where(Project.user_id == user.id)).scalars().all()
        }
        if {RESEARCH_TITLE, DECIDE_TITLE, BUILD_TITLE}.issubset(existing_titles):
            print("Seed projects already present; skipping.")
            return

        def ensure_project(title: str, **kwargs) -> Project:
            p = db.execute(select(Project).where(Project.user_id == user.id).where(Project.title == title)).scalar_one_or_none()
            if p:
                return p
            row = Project(user_id=user.id, title=title, status="active", tags=["seed"], **kwargs)
            db.add(row)
            db.flush()
            return row

        # --- Research project ---
        pr = ensure_project(
            RESEARCH_TITLE,
            description="Compare embedding stores and retrieval strategies for a single-user knowledge base.",
            goal="Pick a practical storage approach for notes + artifacts + chat history.",
            mode_default="research",
        )
        conv_r = Conversation(project_id=pr.id, title="Literature scan")
        db.add(conv_r)
        db.flush()
        db.add(
            Message(
                conversation_id=conv_r.id,
                role="assistant",
                content="Start by defining latency, cost, and privacy constraints before comparing pgvector vs hosted vector DBs.",
            )
        )
        k_r1 = KnowledgeItem(
            project_id=pr.id,
            type="finding",
            title="pgvector keeps ops simple for solo builders",
            content="If you already run Postgres, pgvector avoids a second system of record for metadata joins.",
            confidence=0.65,
            importance_score=0.78,
            is_pinned=True,
            verification_status="partially_verified",
            evidence_strength="strong",
            tags=["rag", "postgres"],
            metadata_json={"origin": "seed"},
            created_by="system",
        )
        k_r2 = KnowledgeItem(
            project_id=pr.id,
            type="claim",
            title="Hosted vector DBs win on elastic scale",
            content="For bursty ingestion and huge corpora, managed vector search can reduce tuning time at higher $.",
            confidence=0.55,
            importance_score=0.62,
            is_pinned=False,
            verification_status="disputed",
            evidence_strength="weak",
            tags=["rag", "hosted"],
            metadata_json={"origin": "seed"},
            created_by="system",
        )
        db.add_all([k_r1, k_r2])
        db.flush()
        db.add(KnowledgeItemRelation(from_knowledge_id=k_r2.id, to_knowledge_id=k_r1.id, relation_type="supports"))
        src = SourceRecord(
            project_id=pr.id,
            title="pgvector README",
            url="https://github.com/pgvector/pgvector",
            source_type="repo",
            retrieved_at=datetime.now(tz=UTC),
            notes="Good starting point for capabilities and limits.",
            credibility_score=0.8,
        )
        db.add(src)
        db.flush()
        db.add_all(
            [
                KnowledgeItemSourceLink(
                    knowledge_item_id=k_r1.id,
                    source_record_id=src.id,
                    citation_note="Primary reference for ops simplicity claim",
                    locator=None,
                ),
                KnowledgeItemSourceLink(
                    knowledge_item_id=k_r2.id,
                    source_record_id=src.id,
                    citation_note="Contrasting scale assumptions",
                    locator="README#comparison",
                ),
            ]
        )
        db.add(
            GeneratedArtifact(
                project_id=pr.id,
                artifact_type="report",
                title="Vector DB comparison (seed)",
                content="## Dimensions\n- Ops burden\n- Cost\n- Query patterns\n\n## Recommendation sketch\nStart with Postgres + pgvector for V1; revisit hosted if corpus explodes.\n",
                content_format="markdown",
            )
        )
        db.add_all(
            [
                TaskItem(
                    project_id=pr.id,
                    title="Benchmark retrieval on 5k notes",
                    description="Measure p95 latency for hybrid keyword + vector.",
                    status="todo",
                    priority=1,
                    due_date=None,
                ),
                TaskItem(
                    project_id=pr.id,
                    title="Document privacy constraints",
                    description="List what must never leave your VPC.",
                    status="in_progress",
                    priority=2,
                    due_date=date.today(),
                ),
            ]
        )

        # --- Decision project ---
        pd = ensure_project(
            DECIDE_TITLE,
            description="Frame a buy-vs-build decision for the personal agent stack.",
            goal="Choose a path that balances time-to-value and long-term control.",
            mode_default="decide",
        )
        conv_d = Conversation(project_id=pd.id, title="Decision workshop")
        db.add(conv_d)
        db.flush()
        k_d1 = KnowledgeItem(
            project_id=pd.id,
            type="conclusion",
            title="Bias toward build for the memory layer",
            content="The memory schema is the product; outsourcing core schema early creates rework.",
            confidence=0.6,
            importance_score=0.85,
            is_pinned=True,
            verification_status="verified",
            evidence_strength="medium",
            tags=["strategy"],
            metadata_json={"origin": "seed"},
            created_by="system",
        )
        k_d2 = KnowledgeItem(
            project_id=pd.id,
            type="note",
            title="Buy UI components, own the data plane",
            content="Use off-the-shelf UI patterns but keep artifacts/knowledge in your DB under explicit models.",
            importance_score=0.58,
            is_pinned=False,
            verification_status="unverified",
            evidence_strength="medium",
            tags=["strategy", "ui"],
            metadata_json={"origin": "seed"},
            created_by="system",
        )
        db.add_all([k_d1, k_d2])
        db.flush()
        db.add(KnowledgeItemRelation(from_knowledge_id=k_d2.id, to_knowledge_id=k_d1.id, relation_type="supports"))
        db.add(
            GeneratedArtifact(
                project_id=pd.id,
                artifact_type="memo",
                title="Decision memo (seed)",
                content="## Options\n- Buy chat shell + integrate API\n- Build bespoke workbench\n\n## Recommendation\nBuild the workbench; buy LLM inference.\n",
                content_format="markdown",
            )
        )
        db.add(
            TaskItem(
                project_id=pd.id,
                title="Validate recommendation with 3 scenarios",
                description="Personal notes, PDFs, and chat transcripts.",
                status="todo",
                priority=1,
                due_date=None,
            )
        )

        # --- Build project ---
        pb = ensure_project(
            BUILD_TITLE,
            description="Hardening checklist for the Research Builder Agent V1.",
            goal="Ship reliable persistence, extraction, and UI flows.",
            mode_default="build",
        )
        conv_b = Conversation(project_id=pb.id, title="Implementation log")
        db.add(conv_b)
        db.flush()
        k_b1 = KnowledgeItem(
            project_id=pb.id,
            type="output",
            title="Migrations must ship before UI depends on new columns",
            content="Add Alembic revisions for any KnowledgeItem field used by the API response models.",
            importance_score=0.7,
            is_pinned=True,
            verification_status="partially_verified",
            evidence_strength="strong",
            tags=["engineering"],
            metadata_json={"origin": "seed"},
            created_by="system",
        )
        db.add(k_b1)
        db.add(
            GeneratedArtifact(
                project_id=pb.id,
                artifact_type="plan",
                title="V1 hardening plan (seed)",
                content="## Workstreams\n- DB migrations + backfills\n- Extraction pipeline tests\n- UI: pinned digest + manual save\n",
                content_format="markdown",
            )
        )
        db.add_all(
            [
                TaskItem(
                    project_id=pb.id,
                    title="Add integration test for /agent/run persistence",
                    status="todo",
                    priority=1,
                    due_date=None,
                ),
                TaskItem(
                    project_id=pb.id,
                    title="Smoke test seed + digest endpoints",
                    status="todo",
                    priority=2,
                    due_date=None,
                ),
            ]
        )

        db.commit()
        print(f"Seeded demo projects for user={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
