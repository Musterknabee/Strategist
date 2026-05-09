from __future__ import annotations
from strategy_validator.application import ui_semantic_validator_handoff_clearance_release_receipt_board as m

def _source():
    def row(lane,status,readiness,ready=False):
        return {"release_custody_id":f"rc-{lane}","evidence_lane":lane,"release_custody_status":status,"release_custody_readiness":readiness,"ready_for_human_custody_observation":ready,"blocked":readiness=="FAIL_CLOSED","waiting":readiness=="WAITING","requires_acceptance_observation":status=="CLEARANCE_RELEASE_CUSTODY_WAITING_ACCEPTANCE","requires_external_artifact":status=="CLEARANCE_RELEASE_CUSTODY_WAITING_EXTERNAL_ARTIFACT","requires_release_handoff_review":status=="CLEARANCE_RELEASE_CUSTODY_WAITING_HANDOFF_REVIEW","requires_investigation":status=="CLEARANCE_RELEASE_CUSTODY_INVESTIGATION_REQUIRED","priority":"P2","severity":"INFO","trust_banner":"TRUSTED" if ready else "TRUST_RESTRICTED","owner_hint":"human_operator_clearance_owner","issue_codes":[f"ISSUE_{lane}"],"experiment_ids":["EXP-1"],"source_release_handoff_status":"X","source_release_handoff_readiness":"Y"}
    return {"schema_version":"ui_semantic_validator_handoff_clearance_release_custody_board/v1","search_root":"synthetic","degraded":["UPSTREAM_DEGRADED"],"release_custodies":[row("BLOCKER","CLEARANCE_RELEASE_CUSTODY_BLOCKED","FAIL_CLOSED"),row("EXTERNAL","CLEARANCE_RELEASE_CUSTODY_WAITING_EXTERNAL_ARTIFACT","WAITING"),row("ACCEPT","CLEARANCE_RELEASE_CUSTODY_WAITING_ACCEPTANCE","WAITING"),row("REVIEW","CLEARANCE_RELEASE_CUSTODY_WAITING_HANDOFF_REVIEW","WAITING"),row("READY","CLEARANCE_RELEASE_CUSTODY_READY_FOR_HUMAN_CUSTODY_OBSERVATION","HUMAN_CUSTODY_READY_OBSERVATION",True)]}

def test_receipt_projects_custodies_and_preserves_firewall(monkeypatch):
    monkeypatch.setattr(m,"build_ui_semantic_validator_handoff_clearance_release_custody_board_payload",lambda **_: _source())
    payload=m.build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload()
    first=payload["release_receipts"][0]
    assert payload["schema_version"]=="ui_semantic_validator_handoff_clearance_release_receipt_board/v1"
    assert payload["read_plane_only"] is True
    assert first["release_receipt_status"]=="CLEARANCE_RELEASE_RECEIPT_BLOCKED"
    assert first["release_receipt_write_authority"]=="none_read_plane"
    assert first["custody_receipt_record_authority"]=="none_read_plane"
    assert payload["summary"]["release_receipt_write_allowed_count"]==0
    assert payload["summary"]["custody_receipt_record_allowed_count"]==0
    assert "SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_RELEASE_RECEIPT_FAIL_CLOSED_PRESENT" in payload["degraded"]

def test_receipt_filters_ready(monkeypatch):
    monkeypatch.setattr(m,"build_ui_semantic_validator_handoff_clearance_release_custody_board_payload",lambda **_: _source())
    payload=m.build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload(ready_for_human_receipt_observation=True)
    assert payload["summary"]["release_receipt_count_returned"]==1
    assert payload["release_receipts"][0]["evidence_lane"]=="READY"
    assert "writes no receipt" in payload["release_receipts"][0]["release_receipt_instruction"]

def test_receipt_filters_custody_review(monkeypatch):
    monkeypatch.setattr(m,"build_ui_semantic_validator_handoff_clearance_release_custody_board_payload",lambda **_: _source())
    payload=m.build_ui_semantic_validator_handoff_clearance_release_receipt_board_payload(release_receipt_status=("CLEARANCE_RELEASE_RECEIPT_WAITING_CUSTODY_REVIEW",))
    assert payload["summary"]["release_receipt_count_returned"]==1
    assert payload["release_receipts"][0]["release_receipt_gate"]=="release_custody_reclassified_to_known_receipt_state"

def test_receipt_latest(monkeypatch):
    monkeypatch.setattr(m,"build_ui_semantic_validator_handoff_clearance_release_custody_board_payload",lambda **_: _source())
    payload=m.build_ui_semantic_validator_handoff_clearance_release_receipt_board_latest_payload()
    assert payload["summary"]["release_receipt_count_returned"]==1
    assert payload["latest"]==payload["release_receipts"][0]
