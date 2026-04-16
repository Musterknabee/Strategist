from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.validator.oracle_advisory import build_oracle_morning_attestation
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_policy import oracle_policy_sha256
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report


def _payload() -> dict:
    return {
        "generated_for_utc": "2026-04-13T08:00:00Z",
        "universe_label": "core",
        "sensors": {
            "semantic": {
                "inflation_hawkishness_score": 0.15,
                "geopolitical_risk_index": 0.2,
                "narrative_contradiction_count": 1,
                "tribunal_belief_conflict": 0.2
            },
            "macro": {
                "yield_curve_slope_bps": -12.0,
                "high_yield_credit_spread_bps": 355.0,
                "equity_bond_correlation": 0.32,
                "cross_asset_correlation_stress": 0.3,
                "realized_volatility_zscore": 0.1
            },
            "microstructure": {
                "vpin": 0.3,
                "order_flow_imbalance": 0.05,
                "spread_variance_zscore": 0.2,
                "liquidity_thinning_score": 0.2
            }
        },
        "strategies": [
            {
                "strategy_id": "s1",
                "strategy_type": "stat_arb",
                "prior_edge_confidence": 0.66,
                "deflated_sharpe_ratio": 0.71,
                "cpcv_lower_bound": 0.4,
                "realized_live_sharpe": 0.9,
                "drawdown_fraction": 0.08,
                "recent_win_rate": 0.57,
                "expected_regimes": ["RISK_ON_LOW_VOL"]
            }
        ]
    }


def test_oracle_reports_embed_canonical_policy_digest(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    source_policy = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(source_policy, encoding="utf-8")
    expected_version, expected_sha256, expected_path = oracle_policy_sha256(repo_root=repo_root)

    payload = json.loads(json.dumps(_payload()))
    from strategy_validator.contracts.oracle import OracleAdvisoryInput
    advisory_input = OracleAdvisoryInput.model_validate(payload)

    attestation = build_oracle_morning_attestation(advisory_input, now_utc=datetime(2026, 4, 13, 8, 15, tzinfo=timezone.utc), repo_root=repo_root)
    fusion = build_oracle_strategic_fusion_report(advisory_input, now_utc=datetime(2026, 4, 13, 8, 15, tzinfo=timezone.utc), repo_root=repo_root, search_root=repo_root)

    assert attestation.oracle_policy_version == expected_version
    assert attestation.oracle_policy_sha256 == expected_sha256
    assert attestation.oracle_policy_path == expected_path
    assert fusion.oracle_policy_version == expected_version
    assert fusion.oracle_policy_sha256 == expected_sha256
    assert fusion.oracle_policy_path == expected_path


def test_briefing_pack_embeds_canonical_policy_digest(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts"
    artifacts_root.mkdir(parents=True)
    (repo_root / "strategy_validator" / "policies").mkdir(parents=True)
    source_policy = Path("strategy_validator/policies/oracle_policy.json").read_text(encoding="utf-8")
    (repo_root / "strategy_validator" / "policies" / "oracle_policy.json").write_text(source_policy, encoding="utf-8")
    expected_version, expected_sha256, expected_path = oracle_policy_sha256(repo_root=repo_root)

    report = build_oracle_briefing_pack(repo_root=repo_root, search_root=artifacts_root)

    assert report.oracle_policy_version == expected_version
    assert report.oracle_policy_sha256 == expected_sha256
    assert report.oracle_policy_path == expected_path
