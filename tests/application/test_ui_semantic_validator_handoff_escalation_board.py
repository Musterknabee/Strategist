from __future__ import annotations
from strategy_validator.application import ui_semantic_validator_handoff_escalation_board as b

def _actions(empty=False, blocked=False, external=False):
    if empty: return {'schema_version':'ui_semantic_validator_handoff_action_queue/v1','search_root':'synthetic','summary':{'source_audit_packet_count':1},'degraded':[],'action_rows':[]}
    state='BLOCKED_ACTION_REQUIRED' if blocked else 'EXTERNAL_ARTIFACT_REQUIRED' if external else 'OPERATOR_ACTION_REQUIRED'
    return {'schema_version':'ui_semantic_validator_handoff_action_queue/v1','search_root':'synthetic','summary':{'source_audit_packet_count':1},'degraded':[],'action_rows':[{'action_id':'action-1','audit_packet_id':'packet-1','audit_packet_digest':'digest-1','experiment_id':'EXP-ESC-1','queue_state':state,'priority':'P0' if blocked else 'P1','severity':'HIGH' if blocked else 'WARN','trust_banner':'UNTRUSTED' if blocked else 'TRUST_RESTRICTED','source':'exception' if blocked else 'evidence_gap','source_id':'src-1','operator_action':'FIX','route':'/ui/semantic-validator-handoff/closure','issue_codes':['ISSUE'],'external_artifact_required':external,'blocked':blocked}]}

def test_escalation_board_blocker(monkeypatch):
    monkeypatch.setattr(b,'build_ui_semantic_validator_handoff_action_queue_payload',lambda **_: _actions(blocked=True))
    payload=b.build_ui_semantic_validator_handoff_escalation_board_payload(escalation_lane=('IMMEDIATE_BLOCKER',), blocked=True)
    assert payload['summary']['immediate_blocker_count']==1
    card=payload['escalation_cards'][0]
    assert card['escalation_lane']=='IMMEDIATE_BLOCKER'
    assert card['acknowledgment_authority']=='none_read_plane'
    assert card['authority']['execution_allowed'] is False

def test_escalation_board_external(monkeypatch):
    monkeypatch.setattr(b,'build_ui_semantic_validator_handoff_action_queue_payload',lambda **_: _actions(external=True))
    payload=b.build_ui_semantic_validator_handoff_escalation_board_payload(external_artifact_required=True)
    card=payload['escalation_cards'][0]
    assert card['escalation_lane']=='EXTERNAL_ARTIFACT_NEEDED'
    assert card['owner_hint']=='external_operator_artifact_owner'
    assert 'EXTERNAL_ARTIFACT_SEMANTIC_VALIDATOR_HANDOFF_ESCALATION_PRESENT' in payload['degraded']
