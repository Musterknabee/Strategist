from datetime import datetime, UTC

from strategy_validator.application.operator_queue_commands import build_transition_policy_payload
from strategy_validator.application.operator_pack_assembly import build_pack_claim_lease_payload


def test_transition_policy_payload_is_dict() -> None:
    payload = build_transition_policy_payload(
        issued_at_utc=datetime(2026, 1, 1, tzinfo=UTC),
        surface_label='ops surface',
        board_label='ops',
    )
    assert isinstance(payload, dict)
    assert payload['board_label'] == 'ops'



def test_pack_claim_lease_payload_is_dict(tmp_path) -> None:
    payload = build_pack_claim_lease_payload(
        search_root=tmp_path,
        repo_root=tmp_path,
        current_pack_kind='status',
        pack_kinds=['status'],
        trust_statuses=[],
        summary_line_contains='',
        output_artifact_label_contains='',
        max_items=2,
        sustained_degraded_threshold=2,
        queue_key='ops',
        review_target='supervisor',
        priority_band='HIGH',
        action_owner_lane='primary',
        backup_owner_lane='secondary',
        ack_owner_lane='ack',
        board_label='ops',
        owner_label_prefix='',
        lease_label_prefix='',
    )
    assert isinstance(payload, dict)
    assert payload['board_label'] == 'ops'
