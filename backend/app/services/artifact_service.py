from sqlalchemy.orm import Session

from app.models.artifact import GeneratedArtifact
from app.schemas.llm_output import ArtifactDraft


def create_artifact_from_draft(db: Session, *, project_id, draft: ArtifactDraft) -> GeneratedArtifact:
    row = GeneratedArtifact(
        project_id=project_id,
        artifact_type=draft.artifact_type,
        title=draft.title[:500],
        content=draft.content,
        content_format=draft.format or "markdown",
        is_pinned=False,
        importance_score=None,
    )
    db.add(row)
    db.flush()
    return row
