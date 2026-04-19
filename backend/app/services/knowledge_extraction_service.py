"""Normalize and lightly validate extracted knowledge before persistence."""

import re

from app.schemas.llm_output import KnowledgeDraft
from app.schemas.knowledge_evidence import normalize_evidence_strength, normalize_verification_status

ALLOWED_TYPES = {
    "fact",
    "claim",
    "note",
    "finding",
    "source",
    "summary",
    "conclusion",
    "output",
    "task",
}


def _clamp01(x: float | None) -> float | None:
    if x is None:
        return None
    return max(0.0, min(1.0, float(x)))


def normalize_knowledge_draft(d: KnowledgeDraft) -> KnowledgeDraft:
    t = (d.type or "").strip().lower()
    if t not in ALLOWED_TYPES:
        t = "note"
    title = (d.title or "").strip() or "Untitled"
    content = (d.content or "").strip() or title
    tags = [x.strip() for x in (d.tags or []) if x and x.strip()]

    meta = dict(d.metadata or {})
    related = list(d.related_titles or [])
    if not related:
        raw = meta.get("related_titles")
        if isinstance(raw, list):
            related = [str(x).strip() for x in raw if str(x).strip()]

    related = [re.sub(r"\s+", " ", x).strip() for x in related if x.strip()][:20]

    urls = list(d.linked_source_urls or [])
    if not urls and isinstance(meta.get("linked_source_urls"), list):
        urls = [str(u).strip() for u in meta["linked_source_urls"] if str(u).strip()]
    if d.source_url:
        urls = [d.source_url.strip()] + [u for u in urls if u.strip() != d.source_url.strip()]
    seen_u: set[str] = set()
    linked_urls: list[str] = []
    for u in urls:
        u = u.strip()
        if not u or u in seen_u:
            continue
        seen_u.add(u)
        linked_urls.append(u)
    linked_urls = linked_urls[:12]

    vstatus = normalize_verification_status(d.verification_status or meta.get("verification_status"))
    estrength = normalize_evidence_strength(d.evidence_strength or meta.get("evidence_strength"))

    if t in {"finding", "claim"} and linked_urls and vstatus == "unverified":
        vstatus = "partially_verified"
    if t in {"finding", "fact"} and (d.confidence or 0) >= 0.75 and estrength == "medium":
        estrength = "strong"

    return KnowledgeDraft(
        type=t,
        title=title[:500],
        content=content,
        source_name=d.source_name,
        source_url=d.source_url,
        confidence=_clamp01(d.confidence),
        importance_score=_clamp01(d.importance_score),
        is_pinned=bool(d.is_pinned),
        verification_status=vstatus,
        evidence_strength=estrength,
        linked_source_urls=linked_urls,
        related_titles=related,
        tags=tags[:50],
        metadata=meta,
    )
