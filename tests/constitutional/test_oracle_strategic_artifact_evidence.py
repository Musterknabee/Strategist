from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleAdvisoryInput
from strategy_validator.validator.oracle_campaign_execution import build_oracle_strategic_campaign_execution_report, render_oracle_strategic_campaign_execution_markdown
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_diagnostics import build_oracle_operator_diagnostic_from_report
from strategy_validator.validator.oracle_campaign_planner import build_oracle_strategic_campaign_report
from strategy_validator.validator.oracle_doctrine_adaptation import build_oracle_doctrine_adaptation_report, render_oracle_doctrine_adaptation_markdown
from strategy_validator.validator.oracle_research_planner import build_oracle_research_priority_report
from strategy_validator.validator.oracle_strategic_artifact_evidence import (
    build_oracle_strategic_artifact_evidence_bundle,
    verify_oracle_strategic_artifact_evidence_bundle,
)
from strategy_validator.validator.oracle_strategic_memory_horizon import build_oracle_strategic_memory_horizon_report
from strategy_validator.validator.oracle_strategic_narrative import build_oracle_strategic_narrative_report
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair

_NOW = datetime(2026, 4, 14, 8, 30, tzinfo=timezone.utc)


def _payload(*, stressed: bool = False) -> OracleAdvisoryInput:
    return OracleAdvisoryInput.model_validate(
        {
            "generated_for_utc": "2026-04-14T08:30:00Z",
            "universe_label": "US_EQ_FACTORS",
            "sensors": {
                "semantic": {
                    "inflation_hawkishness_score": 0.64 if stressed else -0.08,
                    "geopolitical_risk_index": 0.74 if stressed else 0.16,
                    "narrative_contradiction_count": 4 if stressed else 1,
                    "tribunal_belief_conflict": 0.72 if stressed else 0.12,
                },
                "microstructure": {
                    "vpin": 0.68 if stressed else 0.18,
                    "order_flow_imbalance": -0.28 if stressed else 0.12,
                    "spread_variance_zscore": 1.7 if stressed else 0.1,
                    "liquidity_thinning_score": 0.71 if stressed else 0.11,
                },
                "macro": {
                    "yield_curve_slope_bps": -24.0 if stressed else 96.0,
                    "high_yield_credit_spread_bps": 430.0 if stressed else 285.0,
                    "equity_bond_correlation": 0.66 if stressed else -0.28,
                    "cross_asset_correlation_stress": 0.81 if stressed else 0.10,
                    "realized_volatility_zscore": 1.7 if stressed else -0.20,
                },
            },
            "strategies": [
                {
                    "strategy_id": "trend-a",
                    "strategy_type": "TREND_FOLLOWING",
                    "prior_edge_confidence": 0.74,
                    "deflated_sharpe_ratio": 0.91,
                    "cpcv_lower_bound": 0.29,
                    "realized_live_sharpe": -0.10 if stressed else 0.59,
                    "recent_win_rate": 0.39 if stressed else 0.57,
                    "drawdown_fraction": 0.15 if stressed else 0.03,
                    "expected_regimes": ["RISK_ON_LOW_VOL", "TRANSITION"],
                }
            ],
        }
    )


def _sealed_memory(now: datetime = _NOW):
    current = build_oracle_strategic_narrative_report(_payload(stressed=True), now_utc=now)
    prior = build_oracle_strategic_narrative_report(_payload(stressed=False), now_utc=now.replace(hour=7))
    return build_oracle_strategic_memory_horizon_report(
        current,
        sealed_history_reports=[prior],
        sealed_history_manifest_paths=["docs/artifacts/oracle/STACK_07.json"],
        require_sealed_history=True,
        now_utc=now,
    )


@pytest.mark.constitutional
def test_oracle_strategic_artifact_evidence_round_trip_for_doctrine(tmp_path: Path) -> None:
    memory = _sealed_memory()
    report = build_oracle_doctrine_adaptation_report(_payload(stressed=True), strategic_memory_horizon_report=memory, now_utc=_NOW)
    report_path = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.md"
    markdown_path.write_text(render_oracle_doctrine_adaptation_markdown(report), encoding="utf-8")

    private_key = tmp_path / "oracle_private.pem"
    public_key = tmp_path / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest, envelope = build_oracle_strategic_artifact_evidence_bundle(
        report_path=report_path,
        markdown_path=markdown_path,
        repo_root=tmp_path,
        signing_private_key_path=private_key,
    )
    assert envelope is not None
    assert manifest.artifact_kind == "doctrine_adaptation"
    assert manifest.preferred_strategic_backing_classification == "SEALED_STRATEGIC_STACK_BACKED"

    manifest_path = tmp_path / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json"
    dsse_path = tmp_path / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.dsse.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    dsse_path.write_text(json.dumps(envelope.model_dump(mode="json"), indent=2), encoding="utf-8")

    verification = verify_oracle_strategic_artifact_evidence_bundle(
        manifest_path=manifest_path,
        repo_root=tmp_path,
        dsse_path=dsse_path,
        public_key_path=public_key,
    )
    assert verification.status == "VERIFIED"
    assert verification.signature_verified is True
    assert verification.verified_subject_count == 2


@pytest.mark.constitutional
def test_oracle_strategic_artifact_evidence_rejects_cross_run_artifact(tmp_path: Path) -> None:
    memory = _sealed_memory()
    report = build_oracle_research_priority_report(_payload(stressed=True), strategic_memory_horizon_report=memory, now_utc=_NOW)
    report_path = tmp_path / "ORACLE_RESEARCH_PRIORITY_REPORT.json"
    report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")

    mismatch = build_oracle_doctrine_adaptation_report(_payload(stressed=True), now_utc=_NOW.replace(hour=9))
    mismatch_payload = mismatch.model_dump(mode="json")
    mismatch_payload["oracle_run_id"] = "foreign-run-epoch"
    mismatch_path = tmp_path / "MISMATCH.json"
    mismatch_path.write_text(json.dumps(mismatch_payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="matching oracle_run_id"):
        build_oracle_strategic_artifact_evidence_bundle(
            report_path=report_path,
            artifact_paths=[mismatch_path],
            repo_root=tmp_path,
        )


@pytest.mark.constitutional
def test_oracle_strategic_artifact_evidence_cli_round_trip_for_campaign_execution(tmp_path: Path) -> None:
    memory = _sealed_memory()
    campaign = build_oracle_strategic_campaign_report(_payload(stressed=True), strategic_memory_horizon_report=memory, now_utc=_NOW)
    execution = build_oracle_strategic_campaign_execution_report(campaign, strategic_memory_horizon_report=memory, now_utc=_NOW)
    report_path = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json"
    report_path.write_text(json.dumps(execution.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path = tmp_path / "ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.md"
    markdown_path.write_text(render_oracle_strategic_campaign_execution_markdown(execution), encoding="utf-8")

    private_key = tmp_path / "oracle_private.pem"
    public_key = tmp_path / "oracle_public.pem"
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    manifest_path = tmp_path / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json"
    dsse_path = tmp_path / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.dsse.json"
    verification_path = tmp_path / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.verification.json"

    rc = main([
        "oracle-strategic-artifact-evidence",
        str(report_path),
        "--repo-root", str(tmp_path),
        "--markdown-path", str(markdown_path),
        "--signing-private-key", str(private_key),
        "--output", str(manifest_path),
        "--dsse-output", str(dsse_path),
    ])
    assert rc == 0

    rc = main([
        "verify-oracle-strategic-artifact-evidence",
        str(manifest_path),
        "--repo-root", str(tmp_path),
        "--dsse", str(dsse_path),
        "--public-key", str(public_key),
        "--output", str(verification_path),
    ])
    assert rc == 0
    verification = json.loads(verification_path.read_text(encoding="utf-8"))
    assert verification["status"] == "VERIFIED"


@pytest.mark.constitutional
def test_oracle_strategic_artifact_evidence_marks_missing_markdown_incomplete(tmp_path: Path) -> None:
    memory = _sealed_memory()
    report = build_oracle_doctrine_adaptation_report(_payload(stressed=True), strategic_memory_horizon_report=memory, now_utc=_NOW)
    report_path = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path = tmp_path / "ORACLE_DOCTRINE_ADAPTATION_REPORT.md"
    markdown_path.write_text(render_oracle_doctrine_adaptation_markdown(report), encoding="utf-8")

    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(
        report_path=report_path,
        markdown_path=markdown_path,
        repo_root=tmp_path,
    )
    manifest_path = tmp_path / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    markdown_path.unlink()

    verification = verify_oracle_strategic_artifact_evidence_bundle(manifest_path=manifest_path, repo_root=tmp_path)
    assert verification.status == "INCOMPLETE"
    assert any(path.endswith("ORACLE_DOCTRINE_ADAPTATION_REPORT.md") for path in verification.missing_artifact_paths)


@pytest.mark.constitutional
def test_briefing_pack_prefers_per_artifact_evidence_for_doctrine_section(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)

    memory = _sealed_memory()
    report = build_oracle_doctrine_adaptation_report(_payload(stressed=True), strategic_memory_horizon_report=memory, now_utc=_NOW)
    report_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")

    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=repo_root)
    manifest_path = artifacts_root / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    verification_path = artifacts_root / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.verification.json"
    verification_path.write_text(json.dumps({
        "verified_at_utc": _NOW.isoformat(),
        "manifest_path": str(manifest_path),
        "status": "VERIFIED",
        "artifact_digests_verified": True,
        "signature_verified": False,
        "verified_subject_count": 1,
        "digest_mismatches": [],
        "missing_artifact_paths": [],
        "notes": [],
    }, indent=2), encoding="utf-8")

    briefing = build_oracle_briefing_pack(repo_root=repo_root, search_root=repo_root / "docs" / "artifacts")
    doctrine_section = next(section for section in briefing.sections if section.section_id == "doctrine_adaptation")
    assert any("strategic_artifact_evidence_manifest=" in fact for fact in doctrine_section.facts)
    assert any("strategic_artifact_evidence_kind=doctrine_adaptation" == fact for fact in doctrine_section.facts)
    assert any(ref == "strategic_artifact_evidence:doctrine_adaptation" for ref in doctrine_section.provenance_refs)


@pytest.mark.constitutional
def test_operator_diagnostic_names_exact_sealed_strategic_evidence_subject(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts_root = repo_root / "docs" / "artifacts" / "oracle"
    artifacts_root.mkdir(parents=True)

    memory = _sealed_memory()
    report = build_oracle_doctrine_adaptation_report(_payload(stressed=True), strategic_memory_horizon_report=memory, now_utc=_NOW)
    report_path = artifacts_root / "ORACLE_DOCTRINE_ADAPTATION_REPORT.json"
    report_path.write_text(json.dumps(report.model_dump(mode="json"), indent=2), encoding="utf-8")

    manifest, _ = build_oracle_strategic_artifact_evidence_bundle(report_path=report_path, repo_root=repo_root)
    manifest_path = artifacts_root / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.json"
    manifest_path.write_text(json.dumps(manifest.model_dump(mode="json"), indent=2), encoding="utf-8")
    (artifacts_root / "ORACLE_STRATEGIC_ARTIFACT_EVIDENCE.verification.json").write_text(json.dumps({
        "verified_at_utc": _NOW.isoformat(),
        "manifest_path": str(manifest_path),
        "status": "VERIFIED",
        "artifact_digests_verified": True,
        "signature_verified": False,
        "verified_subject_count": 1,
        "digest_mismatches": [],
        "missing_artifact_paths": [],
        "notes": [],
    }, indent=2), encoding="utf-8")

    diagnostic = build_oracle_operator_diagnostic_from_report(report_path, repo_root=repo_root)
    assert any(reason.startswith("sealed_strategic_evidence_manifest=") for reason in diagnostic.reasons)
    assert any(reason == "sealed_strategic_evidence_kind=doctrine_adaptation" for reason in diagnostic.reasons)
