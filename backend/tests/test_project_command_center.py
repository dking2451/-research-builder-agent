"""Unit tests for command center open-loop composition."""

from __future__ import annotations

import uuid
from types import SimpleNamespace

from app.services.project_command_center_service import build_open_loops


def _k(id_hex: str, title: str, **kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(id=uuid.UUID(id_hex), title=title, **kwargs)


def test_open_loops_includes_each_bucket() -> None:
    tasks = [_k("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "Do thing", status="todo", priority=1)]
    questions = [_k("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "Why X?", type="question")]
    findings = [_k("cccccccc-cccc-4ccc-8ccc-cccccccccccc", "Maybe Y", confidence=0.2)]
    claims = [_k("dddddddd-dddd-4ddd-8ddd-dddddddddddd", "Z is true", type="claim")]

    loops = build_open_loops(
        questions=questions,
        open_tasks=tasks,
        low_conf_findings=findings,
        unverified_claims=claims,
        max_items=20,
    )
    kinds = {x.kind for x in loops}
    assert "open_task" in kinds
    assert "open_question" in kinds
    assert "low_confidence_finding" in kinds
    assert "unverified_claim" in kinds


def test_open_loops_respects_max_items() -> None:
    tasks = [SimpleNamespace(id=uuid.uuid4(), title=f"T{i}", status="todo", priority=2) for i in range(20)]
    loops = build_open_loops(
        questions=[],
        open_tasks=tasks,
        low_conf_findings=[],
        unverified_claims=[],
        max_items=6,
    )
    assert len(loops) <= 6
