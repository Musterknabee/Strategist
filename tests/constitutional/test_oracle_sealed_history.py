from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_sealed_history import load_verified_strategic_stack_history_bundle
from strategy_validator.validator.oracle_strategic_briefing import build_oracle_strategic_briefing
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.oracle_strategic_stack_evidence import (
    build_oracle_strategic_stack_evidence_bundle,
    verify_oracle_strategic_stack_evidence_bundle,
)
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


_NOW = datetime(2026, 4, 14, 8, 0, tzinfo=timezone.utc)


def _payload(ts: str) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": ts,
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.15,
                    "geopolitical_risk_index": 0.18,
                    "narrative_contradiction_count": 1,
                    "tribunal_belief_conflict": 0.12,
                },
                "microstructure": {
                    "vpin": 0.22,
                    "order_flow_imbalance": 0.10,
                    "spread_variance_zscore": -0.1,
                    "liquidity_thinning_score": 0.09,
                },
                "macro": {
                    "yield_curve_slope_bps": 88.0,
                    "high_yield_credit_spread_bps": 295.0,
                    "equity_bond_correlation": -0.22,
                    "cross_asset_correlation_stress": 0.10,
                    "realized_volatility_zscore": -0.15,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-a",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.72,
                    "deflated_sharpe_ratio": 0.89,
                    "cpcv_lower_bound": 0.24,
                    "realized_live_sharpe": 0.60,
                    "recent_win_rate": 0.57,
                    "drawdown_fraction": 0.04,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                }
            ],
        }
    )


def _write_verified_history_bundle(base_dir: Path, *, timestamp: str, hour: int) -> tuple[Path, Path, Path, Path]:
    payload = _payload(timestamp)
    input_path = base_dir / f"INPUT_{hour}.json"
    narrative_path = base_dir / f"NARRATIVE_{hour}.json"
    briefing_path = base_dir / f"BRIEFING_{hour}.json"
    manifest_path = base_dir / f"STACK_{hour}.json"
    verification_path = base_dir / f"STACK_{hour}.verification.json"
    private_key = base_dir / f"oracle_private_{hour}.pem"
    public_key = base_dir / f"oracle_public_{hour}.pem"

    input_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
    narrative = build_oracle_strategic_narrative_report(payload, now_utc=_NOW.replace(hour=hour))
    briefing = build_oracle_strategic_briefing(payload, strategic_narrative_report=narrative, now_utc=_NOW.replace(hour=hour))
    narrative_path.write_text(json.dumps(narrative.model_dump(mode="json"), indent=2), encoding="utf-8")
    briefing_path.write_text(json.dumps(briefing.model_dump(mode="json"), indent=2), encoding="utf-8")
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)
    manifest, envelope = build_oracle_strategic_stack_evidence_bundle(
        input_path=input_path,
        briefing_report_path=briefing_path,
        repo_root=base_dir,
        signing_private_key_path=private_key,
        now_utc=_NOW.replace(hour=hour),
    )
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path = base_dir / f"STACK_{hour}.dsse.json"
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")
    verification = verify_oracle_strategic_stack_evidence_bundle(
        manifest_path=manifest_path,
        repo_root=base_dir,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )
    verification_path.write_text(json.dumps(verification.model_dump(mode="json"), indent=2), encoding="utf-8")
    return narrative_path, manifest_path, verification_path, input_path


@pytest.mark.constitutional
def test_load_verified_strategic_stack_history_bundle_rejects_unverified(tmp_path: Path) -> None:
    narrative_path, manifest_path, verification_path, _ = _write_verified_history_bundle(
        tmp_path,
        timestamp="2026-04-14T06:00:00Z",
        hour=6,
    )
    payload = json.loads(verification_path.read_text(encoding="utf-8"))
    payload["status"] = "UNVERIFIED"
    verification_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="VERIFIED stack evidence verification"):
        load_verified_strategic_stack_history_bundle(
            narrative_report_path=narrative_path,
            manifest_path=manifest_path,
            verification_path=verification_path,
        )


@pytest.mark.constitutional
def test_memory_horizon_prefers_verified_history_when_required(tmp_path: Path) -> None:
    narrative_path, manifest_path, verification_path, _ = _write_verified_history_bundle(
        tmp_path,
        timestamp="2026-04-14T06:00:00Z",
        hour=6,
    )
    historical, manifest, _ = load_verified_strategic_stack_history_bundle(
        narrative_report_path=narrative_path,
        manifest_path=manifest_path,
        verification_path=verification_path,
    )
    unsealed = build_oracle_strategic_narrative_report(_payload("2026-04-14T07:00:00Z"), now_utc=_NOW.replace(hour=7))
    current = build_oracle_strategic_narrative_report(_payload("2026-04-14T08:00:00Z"), now_utc=_NOW.replace(hour=8))

    report = build_oracle_strategic_memory_horizon_report(
        current,
        history_reports=[unsealed],
        sealed_history_reports=[historical],
        sealed_history_manifest_paths=[str(manifest_path)],
        require_sealed_history=True,
        now_utc=_NOW,
    )

    assert report.history_integrity_status == "SEALED_HISTORY"
    assert report.sealed_history_observation_count == 1
    assert report.unsealed_history_excluded_count == 1
    assert manifest_path.name in report.source_stack_manifest_paths[0]


@pytest.mark.constitutional
def test_cli_emits_memory_horizon_from_verified_history_bundle(tmp_path: Path) -> None:
    narrative_path, manifest_path, verification_path, _ = _write_verified_history_bundle(
        tmp_path,
        timestamp="2026-04-14T06:00:00Z",
        hour=6,
    )
    current_payload = _payload("2026-04-14T08:00:00Z")
    current = build_oracle_strategic_narrative_report(current_payload, now_utc=_NOW.replace(hour=8))
    current_path = tmp_path / "CURRENT.json"
    current_path.write_text(json.dumps(current.model_dump(mode="json"), indent=2), encoding="utf-8")
    unsealed = build_oracle_strategic_narrative_report(_payload("2026-04-14T07:00:00Z"), now_utc=_NOW.replace(hour=7))
    unsealed_path = tmp_path / "UNSEALED.json"
    unsealed_path.write_text(json.dumps(unsealed.model_dump(mode="json"), indent=2), encoding="utf-8")

    output_path = tmp_path / "ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json"
    rc = main([
        "oracle-strategic-memory-horizon",
        str(current_path),
        "--history-report", str(unsealed_path),
        "--verified-history-bundle", f"{narrative_path}:{manifest_path}:{verification_path}",
        "--require-sealed-history",
        "--output", str(output_path),
    ])

    assert rc == 0
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["history_integrity_status"] == "SEALED_HISTORY"
    assert payload["sealed_history_observation_count"] == 1
    assert payload["unsealed_history_excluded_count"] == 1
