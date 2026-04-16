from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.oracle_advisory import load_oracle_input
from strategy_validator.validator.oracle_strategic_briefing import (
    build_oracle_strategic_briefing,
    render_oracle_strategic_briefing_markdown,
)
from strategy_validator.validator.oracle_strategic_stack_evidence import (
    build_oracle_strategic_stack_evidence_bundle,
    verify_oracle_strategic_stack_evidence_bundle,
)
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _payload() -> dict:
    return {
        "generated_for_utc": "2026-04-14T08:10:00Z",
        "universe_label": "US_EQ_FACTORS",
        "sensors": {
            "semantic": {"inflation_hawkishness_score": 0.3, "geopolitical_risk_index": 0.18, "narrative_contradiction_count": 1, "tribunal_belief_conflict": 0.12},
            "microstructure": {"vpin": 0.22, "order_flow_imbalance": 0.05, "spread_variance_zscore": 0.1, "liquidity_thinning_score": 0.09},
            "macro": {"yield_curve_slope_bps": 72.0, "high_yield_credit_spread_bps": 310.0, "equity_bond_correlation": -0.25, "cross_asset_correlation_stress": 0.08, "realized_volatility_zscore": -0.2},
        },
        "strategies": [
            {
                "strategy_id": "trend-a",
                "strategy_type": "TREND_FOLLOWING",
                "prior_edge_confidence": 0.72,
                "deflated_sharpe_ratio": 0.88,
                "cpcv_lower_bound": 0.22,
                "realized_live_sharpe": 0.61,
                "recent_win_rate": 0.57,
                "drawdown_fraction": 0.03,
                "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
            }
        ],
    }


def _write_stack_artifacts(base_dir: Path) -> tuple[Path, Path, Path]:
    payload = _payload()
    input_path = base_dir / "ORACLE_ADVISORY_INPUT.json"
    input_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    report = build_oracle_strategic_briefing(load_oracle_input(input_path))
    briefing_path = base_dir / "ORACLE_STRATEGIC_BRIEFING_REPORT.json"
    briefing_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path = base_dir / "ORACLE_STRATEGIC_BRIEFING_REPORT.md"
    markdown_path.write_text(render_oracle_strategic_briefing_markdown(report), encoding="utf-8")
    return input_path, briefing_path, markdown_path


@pytest.mark.constitutional
def test_oracle_strategic_stack_evidence_round_trip(tmp_path: Path) -> None:
    input_path, briefing_path, markdown_path = _write_stack_artifacts(tmp_path)
    private_key = tmp_path / "oracle_private.pem"
    public_key = tmp_path / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest, envelope = build_oracle_strategic_stack_evidence_bundle(
        input_path=input_path,
        briefing_report_path=briefing_path,
        markdown_path=markdown_path,
        repo_root=tmp_path,
        signing_private_key_path=private_key,
    )
    assert envelope is not None
    manifest_path = tmp_path / "ORACLE_STRATEGIC_STACK_EVIDENCE.json"
    dsse_path = tmp_path / "ORACLE_STRATEGIC_STACK_EVIDENCE.dsse.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    verification = verify_oracle_strategic_stack_evidence_bundle(
        manifest_path=manifest_path,
        repo_root=tmp_path,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )
    assert verification.status == "VERIFIED"
    assert verification.signature_verified is True
    assert verification.verified_subject_count == 3


@pytest.mark.constitutional
def test_oracle_strategic_stack_evidence_marks_missing_artifact_incomplete(tmp_path: Path) -> None:
    input_path, briefing_path, markdown_path = _write_stack_artifacts(tmp_path)
    manifest, _ = build_oracle_strategic_stack_evidence_bundle(
        input_path=input_path,
        briefing_report_path=briefing_path,
        markdown_path=markdown_path,
        repo_root=tmp_path,
    )
    manifest_path = tmp_path / "ORACLE_STRATEGIC_STACK_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path.unlink()

    verification = verify_oracle_strategic_stack_evidence_bundle(manifest_path=manifest_path, repo_root=tmp_path)
    assert verification.status == "INCOMPLETE"
    assert any(path.endswith("ORACLE_STRATEGIC_BRIEFING_REPORT.md") for path in verification.missing_artifact_paths)


@pytest.mark.constitutional
def test_oracle_strategic_stack_evidence_rejects_universe_mismatch(tmp_path: Path) -> None:
    input_path, briefing_path, markdown_path = _write_stack_artifacts(tmp_path)
    mismatched = {
        "schema_version": "oracle_strategic_narrative_report/v1",
        "generated_at_utc": "2026-04-14T08:10:00Z",
        "universe_label": "EU_MACRO",
        "summary_line": "Mismatch.",
        "narrative_state": "FRAGILE",
        "conviction_balance": 0.2,
        "fragility_balance": 0.8,
        "trust_bias": "LOW_CONFIDENCE",
        "primary_driver": "stress",
        "driver_distribution": [],
        "narrative_lines": [],
        "operator_actions": [],
    }
    mismatch_path = tmp_path / "MISMATCH.json"
    mismatch_path.write_text(json.dumps(mismatched, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="matching universe_label"):
        build_oracle_strategic_stack_evidence_bundle(
            input_path=input_path,
            briefing_report_path=briefing_path,
            markdown_path=markdown_path,
            artifact_paths=[mismatch_path],
            repo_root=tmp_path,
        )


@pytest.mark.constitutional
def test_oracle_strategic_stack_evidence_cli_round_trip(tmp_path: Path) -> None:
    input_path, briefing_path, markdown_path = _write_stack_artifacts(tmp_path)
    private_key = tmp_path / "oracle_private.pem"
    public_key = tmp_path / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest_path = tmp_path / "ORACLE_STRATEGIC_STACK_EVIDENCE.json"
    dsse_path = tmp_path / "ORACLE_STRATEGIC_STACK_EVIDENCE.dsse.json"
    verification_path = tmp_path / "ORACLE_STRATEGIC_STACK_EVIDENCE.verification.json"

    rc = main([
        "oracle-strategic-stack-evidence",
        str(input_path),
        str(briefing_path),
        "--repo-root", str(tmp_path),
        "--markdown-path", str(markdown_path),
        "--signing-private-key", str(private_key),
        "--output", str(manifest_path),
        "--dsse-output", str(dsse_path),
    ])
    assert rc == 0

    rc = main([
        "verify-oracle-strategic-stack-evidence",
        str(manifest_path),
        "--repo-root", str(tmp_path),
        "--dsse", str(dsse_path),
        "--public-key", str(public_key),
        "--output", str(verification_path),
    ])
    assert rc == 0
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    assert verification["status"] == "VERIFIED"
