from __future__ import annotations
from strategy_validator.application import ui_semantic_validator_handoff_resolution_plan as p

def _board(empty=False, blocked=False):
    if empty: return {'schema_version':'ui_semantic_validator_handoff_escalation_board/v1','search_root':'synthetic','summary':{'source_action_count_total':0},'degraded':[],'escalation_cards':[]}
    lane='IMMEDIATE_BLOCKER' if blocked else 'EXTERNAL_ARTIFACT_NEEDED'
    return {'schema_version':'ui_semantic_validator_handoff_escalation_board/v1','search_root':'synthetic','summary':{'source_action_count_total':1},'degraded':['IMMEDIATE_SEMANTIC_VALIDATOR_HANDOFF_BLOCKER_PRESENT'] if blocked else [],'escalation_cards':[{'escalation_id':'esc-1','escalation_rank':100,'escalation_lane':lane,'escalation_reason':'reason','owner_hint':'human_operator_blocker_owner' if blocked else 'external_operator_artifact_owner','action_id':'action-1','audit_packet_id':'packet-1','audit_packet_digest':'digest-1','experiment_id':'EXP-PLAN-1','priority':'P0' if blocked else 'P1','severity':'HIGH' if blocked else 'WARN','trust_banner':'UNTRUSTED' if blocked else 'TRUST_RESTRICTED','queue_state':'BLOCKED_ACTION_REQUIRED' if blocked else 'EXTERNAL_ARTIFACT_REQUIRED','source':'exception' if blocked else 'evidence_gap','source_id':'src-1','operator_action':'FIX','route':'/ui/semantic-validator-handoff/closure','issue_codes':['ISSUE'],'external_artifact_required':not blocked,'blocked':blocked}]}

def test_resolution_plan_external(monkeypatch):
    monkeypatch.setattr(p,'build_ui_semantic_validator_handoff_escalation_board_payload',lambda **_: _board())
    payload=p.build_ui_semantic_validator_handoff_resolution_plan_payload(requires_external_artifact=True)
    step=payload['resolution_steps'][0]
    assert step['phase']=='EXTERNAL_ARTIFACT_COLLECTION'
    assert step['step_state']=='WAITING_EXTERNAL_ARTIFACT'
    assert step['blocks_handoff_clearance'] is True
    assert step['authority']['repair_execution_allowed'] is False

def test_resolution_plan_blocker(monkeypatch):
    monkeypatch.setattr(p,'build_ui_semantic_validator_handoff_escalation_board_payload',lambda **_: _board(blocked=True))
    payload=p.build_ui_semantic_validator_handoff_resolution_plan_payload(phase=('BLOCKER_TRIAGE',),blocks_handoff_clearance=True)
    step=payload['resolution_steps'][0]
    assert step['phase']=='BLOCKER_TRIAGE'
    assert step['step_state']=='BLOCKING_HUMAN_TRIAGE_REQUIRED'
    assert step['validator_submission_authority']=='none_read_plane'
    assert 'BLOCKING_SEMANTIC_VALIDATOR_HANDOFF_RESOLUTION_STEP_PRESENT' in payload['degraded']
