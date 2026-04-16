from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.contracts.operational import (
    ClosureSnapshotInvariantSet,
    ClosureSnapshotManifest,
    ClosureSnapshotOperationalSummary,
    RolloutScope,
)
from strategy_validator.validator.oracle_advisory import (
    build_oracle_evidence_bundle,
    build_oracle_morning_attestation,
    render_oracle_morning_attestation_markdown,
    verify_oracle_evidence_bundle,
)
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


@pytest.mark.constitutional
def test_oracle_evidence_signed_round_trip_with_linked_closure(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_dir = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_dir.mkdir(parents=True)

    closure_manifest = ClosureSnapshotManifest(
        generated_at_utc=datetime(2026, 4, 13, 10, 0, tzinfo=timezone.utc),
        closure_id="closure-abc123",
        closure_dir="docs/artifacts/release_closure_2026-04-13",
        integrity_status="VERIFIED",
        subjects=[],
        missing_artifact_paths=[],
        invariants=ClosureSnapshotInvariantSet(
            interface_freeze_id="0.1.0rc1",
            policy_sha256="a" * 64,
            config_fingerprint="cfg-123",
            runtime_mode="DEV",
            release_commit="abc123",
            release_tag=None,
            host_kind="KEYED_OPERATOR_HOST",
        ),
        scope=RolloutScope(
            environment="paper",
            provider="alpaca_data_v2",
            symbols=["SPY"],
            allowed_actions=["observe"],
            operator_signoff_required=True,
        ),
        operational_summary=ClosureSnapshotOperationalSummary(
            startup_check_passed=True,
            readiness_status="READY",
            provider_availability_ok=True,
            freshness_anomaly_count=0,
            fallback_count=0,
            circuit_open_count=0,
            auth_rate_limit_count=0,
            timeout_count=0,
            policy_change_justified=False,
            release_decision="KEEP_CURRENT_RELEASE",
            observe_only_flags=[],
            must_fix_flags=[],
        ),
    )
    closure_path = artifacts_dir / "CLOSURE_SNAPSHOT.json"
    closure_path.write_text(json.dumps(closure_manifest.model_dump(mode="json"), indent=2), encoding="utf-8")

    input_payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": -0.2,
                "geopolitical_risk_index": 0.10,
                "narrative_contradiction_count": 0,
                "tribunal_belief_conflict": 0.05,
            },
            "microstructure": {
                "vpin": 0.21,
                "order_flow_imbalance": 0.18,
                "spread_variance_zscore": -0.1,
                "liquidity_thinning_score": 0.12,
            },
            "macro": {
                "yield_curve_slope_bps": 95.0,
                "high_yield_credit_spread_bps": 280.0,
                "equity_bond_correlation": -0.35,
                "cross_asset_correlation_stress": 0.08,
                "realized_volatility_zscore": -0.45,
            },
        },
        "strategies": [
            {
                "strategy_id": "trend-b",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.72,
                "deflated_sharpe_ratio": 0.94,
                "cpcv_lower_bound": 0.30,
                "realized_live_sharpe": 0.58,
                "recent_win_rate": 0.57,
                "drawdown_fraction": 0.04,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            }
        ],
    }
    input_path = artifacts_dir / "oracle_input.json"
    input_path.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    from strategy_validator.validator.oracle_advisory import load_oracle_input

    payload = load_oracle_input(input_path)
    attestation = build_oracle_morning_attestation(payload=payload, now_utc=datetime(2026, 4, 13, 8, 11, tzinfo=timezone.utc))
    attestation_path = artifacts_dir / "ORACLE_MORNING_ATTESTATION.json"
    attestation_path.write_text(json.dumps(attestation.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path = artifacts_dir / "ORACLE_MORNING_ATTESTATION.md"
    markdown_path.write_text(render_oracle_morning_attestation_markdown(attestation), encoding="utf-8")

    private_key = repo_root / "keys" / "oracle_private.pem"
    public_key = repo_root / "keys" / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest, envelope = build_oracle_evidence_bundle(
        input_path=input_path,
        attestation_path=attestation_path,
        markdown_path=markdown_path,
        repo_root=repo_root,
        closure_snapshot_path=closure_path,
        signing_private_key_path=private_key,
    )
    assert envelope is not None
    manifest_path = artifacts_dir / "ORACLE_EVIDENCE.json"
    dsse_path = artifacts_dir / "ORACLE_EVIDENCE.dsse.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    verification = verify_oracle_evidence_bundle(
        manifest_path=manifest_path,
        repo_root=repo_root,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )

    assert verification.status == "VERIFIED"
    assert verification.artifact_digests_verified is True
    assert verification.signature_verified is True
    assert verification.linked_closure_present is True
    assert manifest.linked_closure_id == "closure-abc123"


@pytest.mark.constitutional
def test_oracle_evidence_cli_emits_signed_manifest(tmp_path: Path) -> None:
    input_payload = {
        "generated_for_utc": "2026-04-13T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": 0.1,
                "geopolitical_risk_index": 0.18,
                "narrative_contradiction_count": 1,
                "tribunal_belief_conflict": 0.09,
            },
            "microstructure": {
                "vpin": 0.31,
                "order_flow_imbalance": 0.12,
                "spread_variance_zscore": 0.1,
                "liquidity_thinning_score": 0.15,
            },
            "macro": {
                "yield_curve_slope_bps": 84.0,
                "high_yield_credit_spread_bps": 305.0,
                "equity_bond_correlation": -0.15,
                "cross_asset_correlation_stress": 0.11,
                "realized_volatility_zscore": 0.05,
            },
        },
        "strategies": [],
    }
    input_path = tmp_path / "oracle_input.json"
    input_path.write_text(json.dumps(input_payload, indent=2), encoding="utf-8")

    private_key = tmp_path / "oracle_private.pem"
    public_key = tmp_path / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    from strategy_validator.cli.rollout_ops import main

    manifest_path = tmp_path / "ORACLE_EVIDENCE.json"
    dsse_path = tmp_path / "ORACLE_EVIDENCE.dsse.json"
    rc = main([
        "oracle-evidence",
        str(input_path),
        "--signing-private-key",
        str(private_key),
        "--output",
        str(manifest_path),
        "--dsse-output",
        str(dsse_path),
    ])
    assert rc == 0
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["execution_authority"] == "ADVISORY_ONLY"

    verify_output = tmp_path / "ORACLE_EVIDENCE.verification.json"
    rc = main([
        "verify-oracle-evidence",
        str(manifest_path),
        "--dsse",
        str(dsse_path),
        "--public-key",
        str(public_key),
        "--output",
        str(verify_output),
    ])
    assert rc == 0
    verification = json.loads(verify_output.read_text(encoding="utf-8"))
    assert verification["status"] == "VERIFIED"
    assert verification["signature_verified"] is True
