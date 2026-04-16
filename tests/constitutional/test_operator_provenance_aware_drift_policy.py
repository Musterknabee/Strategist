from __future__ import annotations
import json
from datetime import UTC, datetime
from pathlib import Path
import pytest
from strategy_validator.control_plane import build_operator_provenance_aware_drift_policy_request, materialize_operator_provenance_aware_drift_policy, assess_governance_plane, materialize_governance_work_queue_state, run_operator_queue_query
from strategy_validator.cli.rollout_ops import main

@pytest.mark.constitutional
def test_provenance_aware_drift_policy_materializes(tmp_path: Path) -> None:
    gp = assess_governance_plane(evidence_freshness_status='EVIDENCE_CURRENT', evidence_integrity_status='INTEGRITY_VERIFIED', evidence_coverage_status='COVERAGE_COMPLETE', support_verification_status='SUPPORT_VERIFIED', support_chain_trust_status='TRUSTED', support_chain_remediation_status='NO_REMEDIATION', support_chain_remediation_actions=[], operator_readiness='READY_FOR_REVIEW', surface_label='status pack')
    q = run_operator_queue_query(governance_work_queue=materialize_governance_work_queue_state(governance_plane=gp, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)))
    report = materialize_operator_provenance_aware_drift_policy(build_operator_provenance_aware_drift_policy_request(policy_root=tmp_path/'policy', board_label='ops_board', evaluated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), operator_queue_query_result=q, board_label='ops_board')
    assert report.schema_version == 'oracle_operator_provenance_aware_drift_policy/v1'
    assert (tmp_path/'policy'/'ORACLE_OPERATOR_PROVENANCE_AWARE_DRIFT_POLICY.json').exists()
    assert report.policy_count >= 0

@pytest.mark.constitutional
def test_cli_policy_emits_report(tmp_path: Path) -> None:
    output = tmp_path/'out.json'
    rc = main(['oracle-operator-provenance-aware-drift-policy','--issued-at-utc','2026-04-15T10:00:00Z','--surface-label','status pack','--board-label','ops_board','--policy-root',str(tmp_path/'policy'),'--output',str(output)])
    assert rc == 0
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_provenance_aware_drift_policy/v1'
