import json
import logging
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.prompts.mode_prompts import BUILD_SYSTEM, DECIDE_SYSTEM, LEARN_SYSTEM, RESEARCH_SYSTEM
from app.schemas.llm_output import AgentLLMEnvelope, ArtifactDraft, KnowledgeDraft, TaskDraft

logger = logging.getLogger(__name__)

MODE_TO_SYSTEM = {
    "research": RESEARCH_SYSTEM,
    "decide": DECIDE_SYSTEM,
    "build": BUILD_SYSTEM,
    "learn": LEARN_SYSTEM,
}


def _client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAI(api_key=settings.openai_api_key)


def run_structured_agent(
    *,
    mode: str,
    user_prompt: str,
    project_context: str,
    retrieval_context_block: str,
    conversation_context: str,
) -> AgentLLMEnvelope:
    settings = get_settings()
    if settings.openai_api_key.strip() == "":
        raise RuntimeError("OPENAI_API_KEY is empty")

    system = MODE_TO_SYSTEM[mode]
    user = (
        "## Static project summary\n"
        f"{project_context}\n\n"
        "## Retrieved project context (curated; deterministic)\n"
        f"{retrieval_context_block}\n\n"
        "## Recent conversation (may be empty)\n"
        f"{conversation_context}\n\n"
        "## Current user request\n"
        f"{user_prompt}\n"
    )

    client = _client()
    completion = client.beta.chat.completions.parse(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format=AgentLLMEnvelope,
        temperature=0.4,
    )
    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise RuntimeError("Model returned no parsed structured output")
    return parsed


def run_stub_agent(
    *,
    mode: str,
    user_prompt: str,
    retrieval_context_block: str = "",
) -> AgentLLMEnvelope:
    """Deterministic offline response for local demos / tests without an API key."""
    ctx_hint = ""
    if retrieval_context_block.strip():
        ctx_hint = "\n\n### Retrieval context preview (truncated)\n\n" + retrieval_context_block[:1200] + "\n"

    md = (
        f"## Stub `{mode}` response\n\n"
        f"_OpenAI is not configured._ This is a canned preview.\n\n"
        f"**Your prompt:** {user_prompt[:400]}\n"
        f"{ctx_hint}\n"
        "### Key points\n"
        "- The extraction pipeline can still persist structured rows from stub output.\n"
        "- Bullets like this can be auto-captured when the model omits JSON.\n\n"
        "### Next steps\n"
        "- Set `OPENAI_API_KEY` in `backend/.env` and restart the API.\n"
        "- Next step: run a real model call and compare saved knowledge quality.\n"
    )
    k1 = KnowledgeDraft(
        type="finding",
        title="Stub runs should still exercise persistence",
        content="Even without OpenAI, the UI should show messages, optional auto-extraction, and manual saves.",
        importance_score=0.72,
        is_pinned=True,
        verification_status="partially_verified",
        evidence_strength="medium",
        linked_source_urls=[],
        tags=["stub", mode],
        metadata={"origin": "stub"},
    )
    k2 = KnowledgeDraft(
        type="fact",
        title="Structured JSON is more reliable than fragile regex",
        content="Prefer schema-constrained outputs for machine-ingested fields; keep markdown for humans.",
        importance_score=0.62,
        verification_status="unverified",
        evidence_strength="strong",
        linked_source_urls=[],
        related_titles=[k1.title],
        tags=["engineering"],
        metadata={"origin": "stub"},
    )
    art = ArtifactDraft(
        artifact_type="memo",
        title=f"Stub session memo ({mode})",
        content=f"## Memo\n\n{md}\n",
        format="markdown",
    )
    tasks = [
        TaskDraft(
            title="Configure OpenAI and rerun this prompt",
            description="Flip off stub mode by setting OPENAI_API_KEY.",
            status="todo",
            priority=1,
        )
    ]
    return AgentLLMEnvelope(
        display_markdown=md,
        knowledge_items=[k1, k2],
        source_records=[],
        artifacts=[art],
        tasks=tasks,
    )


def try_recover_envelope_from_text(raw: str) -> AgentLLMEnvelope | None:
    """Best-effort JSON extraction if parse fails."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        data: dict[str, Any] = json.loads(raw)
        return AgentLLMEnvelope.model_validate(data)
    except Exception:
        logger.exception("Failed to recover AgentLLMEnvelope from model text")
        return None
