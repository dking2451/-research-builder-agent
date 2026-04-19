"""Evidence / verification enums and citation payloads (V1 string enums in DB)."""

import uuid
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

VerificationStatus = Literal["unverified", "partially_verified", "verified", "disputed"]
EvidenceStrength = Literal["weak", "medium", "strong"]

VERIFICATION_STATUSES = frozenset({"unverified", "partially_verified", "verified", "disputed"})
EVIDENCE_STRENGTHS = frozenset({"weak", "medium", "strong"})


def normalize_verification_status(value: object) -> str:
    if value is None:
        v = "unverified"
    else:
        v = str(value).strip().lower()
    return v if v in VERIFICATION_STATUSES else "unverified"


def normalize_evidence_strength(value: object) -> str:
    if value is None:
        v = "medium"
    else:
        v = str(value).strip().lower()
    return v if v in EVIDENCE_STRENGTHS else "medium"


class SourceCitationOut(BaseModel):
    source_record_id: uuid.UUID
    title: str
    url: str | None
    source_type: str | None
    citation_note: str | None
    locator: str | None


class KnowledgeCitationCreate(BaseModel):
    source_record_id: uuid.UUID
    citation_note: str | None = Field(default=None, max_length=4000)
    locator: str | None = Field(default=None, max_length=200)


class SourceRecordSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    url: str | None
    source_type: str | None
