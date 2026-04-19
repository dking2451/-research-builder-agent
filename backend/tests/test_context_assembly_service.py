"""Tests for retrieval context ranking, caps, related inclusion, and determinism."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.context_assembly_service import (
    ContextAssemblyLimits,
    assemble_retrieval_context,
    default_limits_for_mode,
    knowledge_retrieval_sort_key,
    rank_knowledge_for_context,
    truncate_text,
)


def test_knowledge_rank_pinned_over_unpinned() -> None:
    older = datetime(2020, 1, 1, tzinfo=UTC)
    newer = datetime(2025, 1, 1, tzinfo=UTC)
    unpinned_high = SimpleNamespace(
        is_pinned=False,
        importance_score=0.99,
        updated_at=newer,
        created_at=older,
    )
    pinned_low = SimpleNamespace(
        is_pinned=True,
        importance_score=0.1,
        updated_at=older,
        created_at=older,
    )
    ranked = rank_knowledge_for_context([unpinned_high, pinned_low])
    assert ranked[0] is pinned_low
    assert ranked[1] is unpinned_high


def test_knowledge_rank_importance_when_same_pinned() -> None:
    ts = datetime(2024, 6, 1, tzinfo=UTC)
    a = SimpleNamespace(is_pinned=True, importance_score=0.5, updated_at=ts, created_at=ts)
    b = SimpleNamespace(is_pinned=True, importance_score=0.9, updated_at=ts, created_at=ts)
    ranked = rank_knowledge_for_context([a, b])
    assert ranked[0] is b
    assert ranked[1] is a


def test_knowledge_rank_recency_when_same_pinned_and_importance() -> None:
    old = datetime(2021, 1, 1, tzinfo=UTC)
    new = datetime(2025, 1, 1, tzinfo=UTC)
    ts0 = datetime(2024, 6, 1, tzinfo=UTC)
    a = SimpleNamespace(is_pinned=False, importance_score=0.5, updated_at=old, created_at=ts0)
    b = SimpleNamespace(is_pinned=False, importance_score=0.5, updated_at=new, created_at=ts0)
    ranked = rank_knowledge_for_context([a, b])
    assert ranked[0] is b
    assert ranked[1] is a


def test_knowledge_rank_created_at_tiebreak_when_same_updated() -> None:
    ts_u = datetime(2024, 6, 1, tzinfo=UTC)
    c_old = datetime(2020, 1, 1, tzinfo=UTC)
    c_new = datetime(2023, 1, 1, tzinfo=UTC)
    a = SimpleNamespace(is_pinned=False, importance_score=0.5, updated_at=ts_u, created_at=c_old)
    b = SimpleNamespace(is_pinned=False, importance_score=0.5, updated_at=ts_u, created_at=c_new)
    ranked = rank_knowledge_for_context([a, b])
    assert ranked[0] is b
    assert ranked[1] is a


def test_sort_key_none_importance_sorts_as_zero() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    a = SimpleNamespace(is_pinned=False, importance_score=None, updated_at=ts, created_at=ts)
    b = SimpleNamespace(is_pinned=False, importance_score=0.01, updated_at=ts, created_at=ts)
    ranked = rank_knowledge_for_context([a, b])
    assert ranked[0] is b


def test_truncate_text_adds_ellipsis() -> None:
    assert truncate_text("hello world", 20) == "hello world"
    long = "x" * 50
    out = truncate_text(long, 10)
    assert out.endswith("…")
    assert len(out) == 10


def test_global_rank_then_cap_limits_knowledge() -> None:
    """Pinned + findings merge, re-rank globally, then cap to max_knowledge_in_prompt."""
    pid = uuid.uuid4()
    pinned = [_mk_knowledge(pid, f"p{i}", is_pinned=True, importance_score=0.5 + i * 0.01, days_ago=i) for i in range(8)]
    findings = [_mk_knowledge(pid, f"f{i}", is_pinned=False, importance_score=0.9, days_ago=100 + i) for i in range(10)]

    # execute order: pinned, findings, conclusions, relations, tasks, artifacts (supplemental skipped when cap=0)
    queue: list[list[object]] = [
        pinned,
        findings,
        [],  # conclusions
        [],  # relations
        [],  # tasks
        [],  # artifacts
    ]

    def fake_execute(_stmt: object) -> MagicMock:
        m = MagicMock()
        m.scalars.return_value.all.return_value = queue.pop(0)
        return m

    db = MagicMock()
    db.get.return_value = SimpleNamespace(
        id=pid,
        title="T",
        goal=None,
        description="D",
    )
    db.execute.side_effect = fake_execute

    lim = ContextAssemblyLimits(
        max_pinned_knowledge=50,
        max_recent_findings=50,
        max_recent_conclusions=50,
        max_supplemental_knowledge=0,
        max_related_knowledge=0,
        max_knowledge_in_prompt=5,
        max_open_tasks=5,
        max_recent_artifacts=3,
        max_chars_per_knowledge=200,
        max_chars_per_artifact=200,
        max_total_retrieval_chars=50_000,
    )
    _, debug = assemble_retrieval_context(db, project_id=pid, mode="research", limits=lim)
    assert len(debug.knowledge_items) == 5
    assert debug.caps["selected_knowledge_count"] == 5


def test_related_knowledge_included_when_graph_present() -> None:
    pid = uuid.uuid4()
    anchor = _mk_knowledge(pid, "anchor", is_pinned=True, importance_score=0.9, days_ago=1)
    peer = _mk_knowledge(pid, "peer", is_pinned=False, importance_score=0.2, days_ago=2)
    rel = SimpleNamespace(from_knowledge_id=anchor.id, to_knowledge_id=peer.id)

    # Order matches service: pinned, findings, conclusions, relations, related knowledge, supplemental, tasks, artifacts
    queue: list[list[object]] = [
        [anchor],
        [],
        [],
        [rel],
        [peer],
        [],
        [],
        [],
    ]

    def fake_execute(_stmt: object) -> MagicMock:
        m = MagicMock()
        m.scalars.return_value.all.return_value = queue.pop(0)
        return m

    db = MagicMock()
    db.get.return_value = SimpleNamespace(id=pid, title="Proj", goal=None, description=None)
    db.execute.side_effect = fake_execute

    _, debug = assemble_retrieval_context(db, project_id=pid, mode="research", limits=ContextAssemblyLimits())
    ids = {k.id for k in debug.knowledge_items}
    assert anchor.id in ids
    assert peer.id in ids
    peer_ref = next(k for k in debug.knowledge_items if k.id == peer.id)
    assert peer_ref.role == "related"
    assert "graph_neighbor" in peer_ref.selection_reason


def test_deterministic_order_same_inputs() -> None:
    ts = datetime(2024, 1, 1, tzinfo=UTC)
    xs = [
        SimpleNamespace(is_pinned=False, importance_score=0.5, updated_at=ts, created_at=ts),
        SimpleNamespace(is_pinned=True, importance_score=0.2, updated_at=ts, created_at=ts),
        SimpleNamespace(is_pinned=False, importance_score=0.9, updated_at=ts, created_at=ts),
    ]
    a = rank_knowledge_for_context(xs)
    b = rank_knowledge_for_context(list(reversed(xs)))
    assert [id(x) for x in a] == [id(x) for x in b]


def test_default_limits_for_mode_changes_caps() -> None:
    r = default_limits_for_mode("research")
    d = default_limits_for_mode("decide")
    assert r.max_recent_findings != d.max_recent_findings
    assert d.max_recent_conclusions >= r.max_recent_conclusions


def test_knowledge_retrieval_sort_key_tuple_ordering() -> None:
    ts_old = datetime(2000, 1, 1, tzinfo=UTC)
    ts_new = datetime(2026, 1, 1, tzinfo=UTC)
    a = SimpleNamespace(is_pinned=False, importance_score=0.5, updated_at=ts_new, created_at=ts_new)
    b = SimpleNamespace(is_pinned=True, importance_score=0.1, updated_at=ts_old, created_at=ts_old)
    assert knowledge_retrieval_sort_key(b) > knowledge_retrieval_sort_key(a)


def _mk_knowledge(
    project_id: uuid.UUID,
    title: str,
    *,
    is_pinned: bool,
    importance_score: float | None,
    days_ago: int,
) -> SimpleNamespace:
    base = datetime(2025, 1, 15, tzinfo=UTC)
    ts = base - timedelta(days=days_ago)
    return SimpleNamespace(
        id=uuid.uuid4(),
        project_id=project_id,
        type="finding" if not is_pinned else "note",
        title=title,
        content="x" * 40,
        is_pinned=is_pinned,
        is_archived=False,
        importance_score=importance_score,
        updated_at=ts,
        created_at=ts,
    )
