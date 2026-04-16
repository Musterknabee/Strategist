from strategy_validator.control_plane.claims_service import summarize_claim_item
from strategy_validator.control_plane.escalation_service import summarize_escalation_item
from strategy_validator.control_plane.transition_engine import evaluate_transition


def test_claim_summary_detects_claimed_and_leased() -> None:
    summary = summarize_claim_item({'pack_kind': 'status', 'claim_state': 'CLAIMED', 'lease_state': 'LEASE_ACTIVE'})
    assert summary['is_claimed'] is True
    assert summary['has_active_lease'] is True
    assert summary['posture'] == 'CLAIMED_AND_LEASED'



def test_escalation_summary_normalizes_priority() -> None:
    summary = summarize_escalation_item({'priority_band': 'p1', 'status': 'escalated'})
    assert summary['priority_band'] == 'HIGH'
    assert summary['is_escalated'] is True
    assert summary['posture'] == 'ESCALATED_HIGH'



def test_transition_engine_rejects_invalid_transition() -> None:
    result = evaluate_transition(current_state='QUEUED', desired_state='COMPLETED')
    assert result['allowed'] is False
