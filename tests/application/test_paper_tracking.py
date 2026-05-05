from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.application.paper_tracking_ops import (
    append_daily_snapshot,
    assess_paper_tracking,
    derive_candidate_lifecycle_assessment,
    enroll_strategies_from_batch_run,
    evaluate_paper_tracking,
)
from strategy_validator.application.ui_paper_tracking import build_ui_paper_tracking_latest_payload
from strategy_validator.cli.paper_track import main as paper_track_main
from strategy_validator.contracts.candidate_lifecycle import CandidateLifecycleState
from strategy_validator.contracts.paper_tracking import (
    ExecutionRealismDecayLevel,
    FalsificationRuleKind,
    KillState,
    PaperTrackingCandidate,
    PaperTrackingManifest,
    PaperTrackingScorecard,
    PortfolioCarryForward,
    TriggeredRule,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.contracts.strategy_batch import PitPolicy, StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.contracts.strategy_data_snapshot import LocalBarsDataSourceConfig, StrategyPitSnapshotStatus

REPO = Path(__file__).resolve().parents[2]


def _execution_realism_assumptions_base() -> dict[str, float | bool]:
    return {
        "starting_capital": 1_000_000.0,
        "max_participation_rate": 0.12,
        "fee_bps": 1.0,
        "slippage_bps": 5.0,
        "min_average_daily_volume": 50_000.0,
        "allow_short": False,
        "borrow_required": False,
    }


def _local_bars_spec(tmp: Path) -> StrategyBatchSpec:
    return StrategyBatchSpec(
        batch_id="pt-local-batch",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(tmp / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="pt-local-momo",
                strategy_type="momentum",
                universe="DEMO",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=90,
                params={"signal_window": 15},
                data_source=LocalBarsDataSourceConfig(
                    path="tests/fixtures/strategy_data/demo_daily_bars.csv",
                    pit_status=StrategyPitSnapshotStatus.PIT_VERIFIED,
                ),
                execution_assumptions={
                    "friction_bps": 5.0,
                    "paper_only": True,
                    **_execution_realism_assumptions_base(),
                },
            ),
        ],
    )


def test_enroll_snapshot_evaluate_and_read_plane(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from strategy_validator.research.strategy_batch_runner import run_strategy_batch

    pt_root = tmp_path / "paper_tracking"
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(pt_root))
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "paper-track-batch")
    monkeypatch.chdir(REPO)

    spec = _local_bars_spec(tmp_path)
    summary = run_strategy_batch(spec, allow_synthetic=True)
    run_dir = Path(summary.output_dir)
    manifests = enroll_strategies_from_batch_run(run_dir, allow_synthetic_demo=False)
    assert len(manifests) == 1
    assert manifests[0].candidate.promotion_eligible_at_enrollment is True
    tid = manifests[0].tracking_id
    assert (pt_root / tid / "paper_tracking_manifest.json").is_file()

    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE", "2026-05-02")
    append_daily_snapshot(tid)
    sc = evaluate_paper_tracking(tid)
    assert sc.tracking_id == tid
    assert sc.kill_state.value in ("ACTIVE", "WARNED", "KILLED")

    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(pt_root))
    payload = build_ui_paper_tracking_latest_payload(repo_root=REPO)
    assert payload["latest"] is not None
    assert payload["latest"]["tracking_id"] == tid
    assert payload["latest"]["scorecard"] is not None
    assert payload["latest"]["lifecycle_state"] == CandidateLifecycleState.PROMOTION_REVIEW_READY.value
    assess_paper_tracking(tid)
    assert (pt_root / tid / "lifecycle_assessment.json").is_file()


def test_enroll_cli_json_synthetic_demo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from strategy_validator.research.strategy_batch_runner import run_strategy_batch

    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "pt"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "cli-pt")
    spec = StrategyBatchSpec(
        batch_id="syn",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="syn1",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=40,
            ),
        ],
    )
    summary = run_strategy_batch(spec, allow_synthetic=True)
    code = paper_track_main(
        [
            "enroll",
            "--batch-run",
            str(Path(summary.output_dir)),
            "--allow-synthetic-demo",
            "--json",
        ]
    )
    assert code == 0


def test_read_plane_empty_degraded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "empty"))
    p = build_ui_paper_tracking_latest_payload()
    assert p["latest"] is None
    assert "NO_PAPER_TRACKING_ARTIFACTS" in p["degraded"]
    assert p["replay_evidence_status"] == "UNKNOWN"
    assert p["replay_evidence_blocked"] is False


def test_synthetic_demo_never_promotion_review_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from strategy_validator.research.strategy_batch_runner import run_strategy_batch

    pt_root = tmp_path / "paper_tracking"
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(pt_root))
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "syn-promo")
    spec = StrategyBatchSpec(
        batch_id="syn-promo-batch",
        as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
        mode="paper",
        max_workers=2,
        pit_policy=PitPolicy.DEGRADE_TO_PAPER_ONLY,
        output_root=str(tmp_path / "runs"),
        strategies=[
            StrategyCandidateSpec(
                strategy_id="syn-promo-s",
                strategy_type="momentum",
                universe="U",
                timeframe="1d",
                as_of_utc=datetime(2026, 5, 1, tzinfo=timezone.utc),
                lookback_days=40,
            ),
        ],
    )
    summary = run_strategy_batch(spec, allow_synthetic=True)
    run_dir = Path(summary.output_dir)
    manifests = enroll_strategies_from_batch_run(run_dir, allow_synthetic_demo=True)
    assert len(manifests) == 1
    assert manifests[0].candidate.synthetic_demo is True
    tid = manifests[0].tracking_id
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE", "2026-05-02")
    append_daily_snapshot(tid)
    evaluate_paper_tracking(tid)
    m = PaperTrackingManifest.model_validate(
        json.loads((pt_root / tid / "paper_tracking_manifest.json").read_text(encoding="utf-8"))
    )
    sc = PaperTrackingScorecard.model_validate(
        json.loads((pt_root / tid / "paper_tracking_scorecard.json").read_text(encoding="utf-8"))
    )
    life = derive_candidate_lifecycle_assessment(m, sc)
    assert life.state != CandidateLifecycleState.PROMOTION_REVIEW_READY


def _write_soft_kill_fixtures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    pt_root = tmp_path / "pt"
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(pt_root))
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_PAPER_TRACKING_ID", "lifecycle-soft-kill-test")
    tid = "lifecycle-soft-kill-test"
    tdir = pt_root / tid
    tdir.mkdir(parents=True)
    enrolled = datetime(2026, 5, 1, tzinfo=timezone.utc)
    cand = {
        "strategy_id": "s-soft",
        "strategy_type": "momentum",
        "batch_id": "b",
        "run_id": "r",
        "enrolled_at_utc": enrolled.isoformat(),
        "promotion_eligible_at_enrollment": True,
        "synthetic_demo": False,
        "paper_posture": "RESEARCH_PAPER_TRACKING",
        "data_plane_at_enrollment": "LOCAL_BARS",
        "gauntlet_gate_snapshot": {},
    }
    manifest = PaperTrackingManifest(
        tracking_id=tid,
        batch_run_dir=str(tmp_path / "batch"),
        candidate=PaperTrackingCandidate.model_validate({**cand}),
        portfolio_carry_forward=PortfolioCarryForward(portfolio_gate_status="NOT_APPLICABLE"),
    )
    plain_m = manifest.model_dump(mode="json", exclude={"manifest_sha256"})
    manifest = manifest.model_copy(update={"manifest_sha256": canonical_json_sha256(plain_m)})
    (tdir / "paper_tracking_manifest.json").write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    now = datetime(2026, 5, 3, tzinfo=timezone.utc)
    sc = PaperTrackingScorecard(
        tracking_id=tid,
        strategy_id="s-soft",
        evaluated_at_utc=now,
        days_of_signals=5,
        cumulative_paper_return=0.01,
        drift_score=0.1,
        execution_realism_decay_level=ExecutionRealismDecayLevel.NONE,
        kill_state=KillState.KILLED,
        triggered_rules=[
            TriggeredRule(
                rule_id="paper-signal-drift",
                kind=FalsificationRuleKind.SIGNAL_DRIFT.value,
                detail="drift_score=0.9>threshold=0.75",
            )
        ],
        warnings=[],
    )
    plain_s = sc.model_dump(mode="json", exclude={"scorecard_sha256"})
    sc = sc.model_copy(update={"scorecard_sha256": canonical_json_sha256(plain_s)})
    (tdir / "paper_tracking_scorecard.json").write_text(
        json.dumps(sc.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return tid


def test_duplicative_blocks_promotion_until_governed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from strategy_validator.research.strategy_batch_runner import run_strategy_batch

    pt_root = tmp_path / "paper_tracking"
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(pt_root))
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_STRATEGY_RUN_ID", "dup-promo")
    monkeypatch.chdir(REPO)
    spec = _local_bars_spec(tmp_path)
    summary = run_strategy_batch(spec, allow_synthetic=True)
    run_dir = Path(summary.output_dir)
    manifests = enroll_strategies_from_batch_run(run_dir, allow_synthetic_demo=False)
    tid = manifests[0].tracking_id
    monkeypatch.setenv("STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE", "2026-05-02")
    append_daily_snapshot(tid)
    evaluate_paper_tracking(tid)
    mpath = pt_root / tid / "paper_tracking_manifest.json"
    raw = json.loads(mpath.read_text(encoding="utf-8"))
    raw["portfolio_carry_forward"] = {
        **raw.get("portfolio_carry_forward", {}),
        "portfolio_gate_status": "DUPLICATIVE",
        "duplicate_alpha_warnings": ["TEST_DUPLICATE"],
    }
    raw.pop("manifest_sha256", None)
    m = PaperTrackingManifest.model_validate(raw)
    plain = m.model_dump(mode="json", exclude={"manifest_sha256"})
    m = m.model_copy(update={"manifest_sha256": canonical_json_sha256(plain)})
    mpath.write_text(json.dumps(m.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    m2 = PaperTrackingManifest.model_validate(json.loads(mpath.read_text(encoding="utf-8")))
    sc = PaperTrackingScorecard.model_validate(json.loads((pt_root / tid / "paper_tracking_scorecard.json").read_text()))
    blocked = derive_candidate_lifecycle_assessment(m2, sc)
    assert blocked.state != CandidateLifecycleState.PROMOTION_REVIEW_READY

    assess_paper_tracking(
        tid,
        allow_promotion_despite_duplicative=True,
        duplicative_promotion_rationale="governance approved duplicate cohort review 2026-05-01",
    )
    m3 = PaperTrackingManifest.model_validate(json.loads(mpath.read_text(encoding="utf-8")))
    sc2 = PaperTrackingScorecard.model_validate(json.loads((pt_root / tid / "paper_tracking_scorecard.json").read_text()))
    governed = derive_candidate_lifecycle_assessment(m3, sc2)
    assert governed.state == CandidateLifecycleState.PROMOTION_REVIEW_READY


def test_hard_kill_rule_yields_killed_by_rule(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tid = _write_soft_kill_fixtures(tmp_path, monkeypatch)
    tdir = tmp_path / "pt" / tid
    raw = json.loads((tdir / "paper_tracking_scorecard.json").read_text(encoding="utf-8"))
    raw["triggered_rules"] = [
        {
            "rule_id": "paper-max-cum-loss",
            "kind": FalsificationRuleKind.MAX_CUMULATIVE_LOSS.value,
            "detail": "cumulative_return=-0.20<threshold=-0.15",
        }
    ]
    raw.pop("scorecard_sha256", None)
    sc = PaperTrackingScorecard.model_validate(raw)
    plain_s = sc.model_dump(mode="json", exclude={"scorecard_sha256"})
    sc = sc.model_copy(update={"scorecard_sha256": canonical_json_sha256(plain_s)})
    (tdir / "paper_tracking_scorecard.json").write_text(
        json.dumps(sc.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    m = PaperTrackingManifest.model_validate(json.loads((tdir / "paper_tracking_manifest.json").read_text()))
    sc2 = PaperTrackingScorecard.model_validate(json.loads((tdir / "paper_tracking_scorecard.json").read_text()))
    life = derive_candidate_lifecycle_assessment(m, sc2)
    assert life.state == CandidateLifecycleState.KILLED_BY_RULE


def test_soft_kill_rule_yields_kill_candidate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    tid = _write_soft_kill_fixtures(tmp_path, monkeypatch)
    tdir = tmp_path / "pt" / tid
    m = PaperTrackingManifest.model_validate(json.loads((tdir / "paper_tracking_manifest.json").read_text()))
    sc2 = PaperTrackingScorecard.model_validate(json.loads((tdir / "paper_tracking_scorecard.json").read_text()))
    life = derive_candidate_lifecycle_assessment(m, sc2)
    assert life.state == CandidateLifecycleState.KILL_CANDIDATE


def test_cli_list_json_includes_lifecycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import io
    from contextlib import redirect_stdout

    _write_soft_kill_fixtures(tmp_path, monkeypatch)
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "pt"))
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = paper_track_main(["list", "--json"])
    assert code == 0
    payload = json.loads(buf.getvalue())
    assert payload["schema_version"] == "paper_tracking_list/v1"
    assert len(payload["entries"]) >= 1
    assert "lifecycle_state" in payload["entries"][0]


def test_read_plane_latest_includes_lifecycle_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_soft_kill_fixtures(tmp_path, monkeypatch)
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "pt"))
    p = build_ui_paper_tracking_latest_payload()
    assert p["latest"] is not None
    assert p["latest"]["lifecycle_state"] == CandidateLifecycleState.KILL_CANDIDATE.value


def test_detail_route_safe_traversal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from strategy_validator.application.ui_paper_tracking import build_ui_paper_tracking_detail_payload

    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "pt"))
    p = build_ui_paper_tracking_detail_payload("../etc/passwd")
    assert p["tracking"] is None
    assert "PAPER_TRACKING_NOT_FOUND" in p["degraded"]
