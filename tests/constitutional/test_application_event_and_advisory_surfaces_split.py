from __future__ import annotations

from strategy_validator import application


def test_application_root_routes_event_and_advisory_exports_to_split_modules() -> None:
    assert application.build_event_checkpoint_payload.__module__ == 'strategy_validator.application.oracle_event_surfaces'
    assert application.build_memory_review_payload.__module__ == 'strategy_validator.application.oracle_event_surfaces'
    assert application.build_oracle_evidence_bundle_payload.__module__ == 'strategy_validator.application.oracle_advisory_surfaces'
    assert application.build_operator_diagnostic_from_report_payload.__module__ == 'strategy_validator.application.oracle_advisory_surfaces'
