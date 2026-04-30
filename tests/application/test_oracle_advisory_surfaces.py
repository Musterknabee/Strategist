from __future__ import annotations

from strategy_validator import application


def test_application_root_routes_advisory_surfaces_to_dedicated_module() -> None:
    assert application.build_oracle_evidence_bundle_payload.__module__ == 'strategy_validator.application.oracle_advisory_surfaces'
    assert application.render_oracle_trust_banner_payload.__module__ == 'strategy_validator.application.oracle_advisory_surfaces'
    assert application.explain_report_from_path_payload.__module__ == 'strategy_validator.application.oracle_advisory_surfaces'


def test_application_root_routes_event_surfaces_to_dedicated_module() -> None:
    assert application.build_event_checkpoint_payload.__module__ == 'strategy_validator.application.oracle_event_surfaces'
    assert application.render_constitutional_gate_markdown_payload.__module__ == 'strategy_validator.application.oracle_event_surfaces'
    assert application.verify_event_checkpoint_payload.__module__ == 'strategy_validator.application.oracle_event_surfaces'
