from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SNAPSHOT_PATH = REPO_ROOT / 'strategy_validator' / 'control_plane' / 'operator_queue_snapshot.py'
PROJECTION_PATH = REPO_ROOT / 'strategy_validator' / 'projections' / 'operator_action_workboard.py'


def test_operator_queue_snapshot_consumes_projection_backed_operator_action_materialization() -> None:
    source = SNAPSHOT_PATH.read_text(encoding='utf-8')
    assert 'from strategy_validator.projections.operator_action_workboard import materialize_operator_action_workboard_projection' in source
    assert 'from strategy_validator.ledger.operator_actions import read_operator_action_events' not in source
    assert 'journal_projection = materialize_operator_action_workboard_projection(queue_state)' in source
    assert 'journal_items = journal_projection.work_items' in source
    assert 'journal_projection_summary_line=journal_projection.summary_line' in source
    assert 'journal_operator_count=journal_projection.operator_count' in source


def test_operator_action_workboard_projection_owns_journaled_work_item_materialization() -> None:
    source = PROJECTION_PATH.read_text(encoding='utf-8')
    assert 'def operator_action_projection_enabled()' in source
    assert 'class OperatorActionWorkboardProjection' in source
    assert 'latest_action_created_at_utc: datetime | None' in source
    assert 'operator_count: int = 0' in source
    assert 'action_count: int = 0' in source
    assert 'summary_line: str' in source
    assert 'recommended_next_actions: tuple[str, ...]' in source
    assert 'current_work_item_count: int = 0' in source
    assert 'aging_work_item_count: int = 0' in source
    assert 'stale_work_item_count: int = 0' in source
    assert 'primary_merge_pending_count: int = 0' in source
    assert 'auxiliary_merge_pending_count: int = 0' in source
    assert 'post_merge_ready_count: int = 0' in source
    assert 'post_merge_review_required_count: int = 0' in source
    assert 'post_merge_stale_count: int = 0' in source
    assert 'downstream_closure_ready_count: int = 0' in source
    assert 'downstream_closure_review_required_count: int = 0' in source
    assert 'downstream_closure_blocked_count: int = 0' in source
    assert 'def materialize_operator_action_workboard_projection(' in source
    assert 'projection_freshness_state' in source
    assert 'projection_recommended_actions' in source
    assert 'projection_governed_merge_state' in source
    assert 'projection_governed_summary_line' in source
    assert 'projection_post_merge_lifecycle_state' in source
    assert 'projection_post_merge_summary_line' in source
    assert 'projection_downstream_closure_state' in source
    assert 'projection_downstream_closure_summary_line' in source
    assert 'def _projection_downstream_closure_fields(' in source
    assert 'def materialize_journaled_operator_work_items(' in source
    assert 'read_operator_action_events(' in source
