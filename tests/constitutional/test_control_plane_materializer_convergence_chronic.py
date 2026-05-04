from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONVERTED = [
    "strategy_validator/control_plane/operator_chronic_exit_certification.py",
    "strategy_validator/control_plane/operator_chronic_exit_return_bridge.py",
    "strategy_validator/control_plane/operator_chronic_instability_packet.py",
    "strategy_validator/control_plane/operator_chronic_origin_restoration_audit_overlay.py",
    "strategy_validator/control_plane/operator_chronic_origin_restoration_provenance.py",
    "strategy_validator/control_plane/operator_chronic_remediation_mandate_ledger.py",
    "strategy_validator/control_plane/operator_chronic_remediation_satisfaction.py",
    "strategy_validator/control_plane/operator_chronic_watch_audit_convergence.py",
    "strategy_validator/control_plane/operator_chronic_watch_handoff.py",
    "strategy_validator/control_plane/operator_chronic_watch_outcome.py",
    "strategy_validator/control_plane/operator_converged_normalization_attestation.py",
    "strategy_validator/control_plane/operator_escalation_closure.py",
    "strategy_validator/control_plane/operator_escalation_routing.py",
    "strategy_validator/control_plane/operator_freeze_release_attestation.py",
    "strategy_validator/control_plane/operator_monitored_rejoin_activation.py",
    "strategy_validator/control_plane/operator_monitored_rejoin_normalization_bridge.py",
]


def test_chronic_and_escalation_modules_use_shared_materializer() -> None:
    for relative in CONVERTED:
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert "from strategy_validator.control_plane.materialization import write_json_markdown_artifacts" in source
        assert "write_json_markdown_artifacts(" in source
        assert "json.dumps(report.to_payload()" not in source
