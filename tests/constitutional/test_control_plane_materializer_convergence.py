from __future__ import annotations

from pathlib import Path


_CONVERTED_MODULES = [
    Path("strategy_validator/control_plane/operator_decision_execution.py"),
    Path("strategy_validator/control_plane/operator_escalation_packet.py"),
    Path("strategy_validator/control_plane/operator_freeze_release_gate.py"),
    Path("strategy_validator/control_plane/operator_reentry_assignment.py"),
    Path("strategy_validator/control_plane/operator_reentry_acceptance.py"),
    Path("strategy_validator/control_plane/operator_return_activation.py"),
]


def test_selected_control_plane_materializers_use_shared_writer() -> None:
    for module_path in _CONVERTED_MODULES:
        source = module_path.read_text(encoding="utf-8")
        assert "write_json_markdown_artifacts" in source
        assert "json.dumps(report.to_payload()" not in source
