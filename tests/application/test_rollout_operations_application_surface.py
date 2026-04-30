from strategy_validator.application import (
    build_closure_release_attestation_payload,
    build_closure_snapshot_payload,
    build_daily_checklist_payload,
    build_governed_exception_memo_payload,
    build_rollout_bundle_payload,
    default_startup_json_bundle_payload,
    generate_host_fingerprint_payload,
    generate_snapshot_signing_keypair_payload,
    load_controlled_rollout_rules_payload,
    parse_analyze_summary_payload,
    render_decision_reconciliation_markdown_payload,
    render_final_release_signoff_markdown_payload,
    render_governed_exception_markdown_payload,
    review_runtime_evidence_payload,
    verify_closure_snapshot_payload,
    verify_governed_exception_memo_payload,
)


def test_rollout_operations_application_exports_resolve() -> None:
    assert callable(generate_host_fingerprint_payload)
    assert callable(generate_snapshot_signing_keypair_payload)
    assert callable(build_rollout_bundle_payload)
    assert callable(parse_analyze_summary_payload)
    assert callable(default_startup_json_bundle_payload)
    assert callable(load_controlled_rollout_rules_payload)
    assert callable(build_daily_checklist_payload)
    assert callable(review_runtime_evidence_payload)
    assert callable(build_closure_snapshot_payload)
    assert callable(verify_closure_snapshot_payload)
    assert callable(build_governed_exception_memo_payload)
    assert callable(verify_governed_exception_memo_payload)
    assert callable(render_governed_exception_markdown_payload)
    assert callable(build_closure_release_attestation_payload)
    assert callable(render_final_release_signoff_markdown_payload)
    assert callable(render_decision_reconciliation_markdown_payload)
