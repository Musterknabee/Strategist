from __future__ import annotations
from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_custody_board as m

def _source():
    def row(lane,status,readiness,ready=False):
        return {"release_handoff_id":f"rh-{lane}","evidence_lane":lane,"release_handoff_status":status,"release_handoff_readiness":readiness,"ready_for_human_transfer_observation":ready,"blocked":readiness=="FAIL_CLOSED","waiting":readiness=="WAITING","requires_acceptance_observation":status=="CLEARANCE_RELEASE_HANDOFF_WAITING_ACCEPTANCE","requires_external_artifact":status=="CLEARANCE_RELEASE_HANDOFF_WAITING_EXTERNAL_ARTIFACT","requires_release_packet_review":status=="CLEARANCE_RELEASE_HANDOFF_WAITING_PACKET_REVIEW","requires_investigation":status=="CLEARANCE_RELEASE_HANDOFF_INVESTIGATION_REQUIRED","priority":"P2","severity":"INFO","trust_banner":"TRUSTED" if ready else "TRUST_RESTRICTED","owner_hint":"human_operator_clearance_owner","issue_codes":[f"ISSUE_{lane}"],"experiment_ids":["EXP-1"],"source_release_packet_status":"X","source_release_packet_readiness":"Y"}
    return {"schema_version":"ui_semantic_validator_handoff_clearance_release_handoff_board/v1","search_root":"synthetic","degraded":["UPSTREAM_DEGRADED"],"release_handoffs":[row("BLOCKER","CLEARANCE_RELEASE_HANDOFF_BLOCKED","FAIL_CLOSED"),row("EXTERNAL","CLEARANCE_RELEASE_HANDOFF_WAITING_EXTERNAL_ARTIFACT","WAITING"),row("ACCEPT","CLEARANCE_RELEASE_HANDOFF_WAITING_ACCEPTANCE","WAITING"),row("REVIEW","CLEARANCE_RELEASE_HANDOFF_WAITING_PACKET_REVIEW","WAITING"),row("READY","CLEARANCE_RELEASE_HANDOFF_READY_FOR_HUMAN_TRANSFER_OBSERVATION","HUMAN_TRANSFER_READY_OBSERVATION",True)]}

def test_custody_projects_handoffs_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m,"build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload",lambda **_: _source())
    payload=m.build_ui_semantic_validator_handoff_clearance_release_custody_board_payload()
    assert payload["schema_version"]=="ui_semantic_validator_handoff_clearance_release_custody_board/v1"
    assert payload["read_plane_only"] is True
    assert payload["release_custodies"][0]["release_custody_status"]=="CLEARANCE_RELEASE_CUSTODY_BLOCKED"
    assert payload["release_custodies"][0]["release_custody_write_authority"]=="none_read_plane"
    assert payload["summary"]["custody_transfer_allowed_count"]==0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_CUSTODY_FAIL_CLOSED_PRESENT" in payload["degraded"]

def test_custody_filters_ready(monkeypatch):
    monkeypatch.setattr(m,"build_ui_semantic_validator_handoff_clearance_release_handoff_board_payload",lambda **_: _source())
    payload=m.build_ui_semantic_validator_handoff_clearance_release_custody_board_payload(ready_for_human_custody_observation=True)
    assert payload["summary"]["release_custody_count_returned"]==1
    assert payload["release_custodies"][0]["evidence_lane"]=="READY"
    assert "writes no custody" in payload["release_custodies"][0]["release_custody_instruction"]
