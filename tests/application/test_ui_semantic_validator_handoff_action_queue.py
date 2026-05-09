from __future__ import annotations
from strategy_validator.application import ui_semantic_validator_handoff_action_queue as q

def _packet_payload(kind='external'):
    if kind=='empty': return {'schema_version':'ui_semantic_validator_handoff_audit_packet/v1','search_root':'synthetic','degraded':[],'audit_packets':[]}
    blocked=kind=='blocked'
    return {'schema_version':'ui_semantic_validator_handoff_audit_packet/v1','search_root':'synthetic','degraded':[],'audit_packets':[{'audit_packet_id':'packet-1','audit_packet_digest':'digest-1','experiment_id':'EXP-AQ-1','continuity_id':'cont-1','chain_id':'chain-1','chain_digest':'chain-d','packet_status':'OPEN_EXCEPTIONS_BLOCKING' if blocked else 'AWAITING_EXTERNAL_ARTIFACT','packet_lane':'blocked' if blocked else 'external_artifact','trust_banner':'UNTRUSTED' if blocked else 'TRUST_RESTRICTED','audit_ready':False,'operator_attention_required':True,'required_actions':[{'source':'exception' if blocked else 'evidence_gap','source_id':'src-1','priority':'P0' if blocked else 'P1','severity':'HIGH' if blocked else 'WARN','operator_action':'RESOLVE_BLOCKING_EXCEPTION' if blocked else 'CREATE_EXTERNAL_ARTIFACT_EXTERNALLY','route':'/ui/semantic-validator-handoff/exceptions' if blocked else '/ui/semantic-validator-handoff/closure','issue_codes':['BLOCKING_EXCEPTION'] if blocked else ['EXTERNAL_CLOSURE_ATTESTATION_MISSING']}]}]}

def test_action_queue_external(monkeypatch):
    monkeypatch.setattr(q,'build_ui_semantic_validator_handoff_audit_packet_payload',lambda **_: _packet_payload('external'))
    payload=q.build_ui_semantic_validator_handoff_action_queue_payload(external_artifact_required=True)
    assert payload['schema_version']=='ui_semantic_validator_handoff_action_queue/v1'
    assert payload['summary']['external_artifact_required_count']==1
    row=payload['action_rows'][0]
    assert row['queue_state']=='EXTERNAL_ARTIFACT_REQUIRED'
    assert row['external_artifact_required'] is True
    assert row['external_artifact_write_authority']=='none_read_plane'
    assert row['authority']['execution_allowed'] is False

def test_action_queue_blocked(monkeypatch):
    monkeypatch.setattr(q,'build_ui_semantic_validator_handoff_audit_packet_payload',lambda **_: _packet_payload('blocked'))
    payload=q.build_ui_semantic_validator_handoff_action_queue_payload(blocked=True)
    row=payload['action_rows'][0]
    assert row['queue_state']=='BLOCKED_ACTION_REQUIRED'
    assert row['priority']=='P0'
    assert row['blocked'] is True
    assert 'BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_ACTION_PRESENT' in payload['degraded']
