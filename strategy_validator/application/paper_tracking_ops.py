"""Paper tracking enroll / snapshot / evaluate (artifacts only; no ledger)."""
from __future__ import annotations

import hashlib
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_tracking_common import (
    _paper_tracking_root,
    _read_json,
    _write_json,
)
from strategy_validator.application.paper_tracking_lifecycle import (
    apply_manifest_governance_updates,
    assess_paper_tracking,
    derive_candidate_lifecycle_assessment,
    list_paper_tracking_entries,
    read_persisted_lifecycle_assessment,
)
from strategy_validator.contracts.paper_tracking import (
    DailySignalSnapshot,
    ExecutionRealismDecayLevel,
    FalsificationRuleKind,
    KillState,
    PaperPosture,
    PaperTrackingCandidate,
    PaperTrackingManifest,
    PaperTrackingScorecard,
    PortfolioCarryForward,
    RealizedOutcomeSnapshot,
    TriggeredRule,
    default_kill_rules,
)
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunResult, StrategyRunStatus
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def make_tracking_id(
    *,
    batch_id: str,
    run_id: str,
    strategy_id: str,
    enrolled_at_utc: datetime,
) -> str:
    override = os.environ.get("STRATEGY_VALIDATOR_TEST_PAPER_TRACKING_ID", "").strip()
    if override:
        return override
    basis = canonical_json_sha256(
        {
            "batch_id": batch_id,
            "run_id": run_id,
            "strategy_id": strategy_id,
            "enrolled_at": enrolled_at_utc.isoformat(),
        }
    )
    return basis[:24]


def _deterministic_exposure(tracking_id: str, observation_date: date) -> float:
    h = hashlib.sha256(f"{tracking_id}|{observation_date.isoformat()}".encode()).digest()
    u = int.from_bytes(h[:8], "big", signed=False) / float(2**64)
    return float(2.0 * u - 1.0)


def _portfolio_carry_from_batch(summary: StrategyBatchRunSummary) -> PortfolioCarryForward:
    raw = summary.portfolio_correlation_summary
    if not raw:
        return PortfolioCarryForward()
    gate = str(raw.get("portfolio_gate_status", "NOT_APPLICABLE"))
    warns = list(raw.get("duplicate_alpha_warnings", []) or [])
    if isinstance(warns, list):
        dup = [str(x) for x in warns]
    else:
        dup = []
    avg = raw.get("average_correlation")
    disc = str(raw.get("disclaimer", PortfolioCarryForward().disclaimer))
    return PortfolioCarryForward(
        portfolio_gate_status=gate,
        duplicate_alpha_warnings=dup,
        average_correlation=float(avg) if isinstance(avg, (int, float)) else None,
        disclaimer=disc,
    )


def _eligible_for_real_enrollment(r: StrategyRunResult) -> bool:
    if r.status != StrategyRunStatus.PASSED:
        return False
    if r.data_plane == "SYNTHETIC":
        return False
    return bool(r.gate_summary.promotion_eligible)


def _eligible_demo_synthetic(r: StrategyRunResult) -> bool:
    return r.status == StrategyRunStatus.PAPER_ONLY and r.data_plane == "SYNTHETIC"


def enroll_strategies_from_batch_run(
    batch_run_dir: Path,
    *,
    strategy_ids: list[str] | None = None,
    allow_synthetic_demo: bool = False,
    repo_root: Path | None = None,
) -> list[PaperTrackingManifest]:
    """Create one manifest per enrolled strategy under paper_tracking_root."""

    run_dir = batch_run_dir.resolve()
    summary_path = run_dir / "batch_summary.json"
    if not summary_path.is_file():
        raise FileNotFoundError(f"BATCH_SUMMARY_MISSING:{summary_path}")
    summary = StrategyBatchRunSummary.model_validate(_read_json(summary_path))
    portfolio_cf = _portfolio_carry_from_batch(summary)
    out_root = _paper_tracking_root(repo_root)
    enrolled: list[PaperTrackingManifest] = []
    now = datetime.now(timezone.utc)
    sid_filter = set(strategy_ids) if strategy_ids else None

    for r in summary.strategies:
        if sid_filter is not None and r.strategy_id not in sid_filter:
            continue
        demo = _eligible_demo_synthetic(r)
        real = _eligible_for_real_enrollment(r)
        if demo:
            if not allow_synthetic_demo:
                continue
            posture = PaperPosture.DEMO_PAPER_ONLY
        elif real:
            posture = PaperPosture.RESEARCH_PAPER_TRACKING
        else:
            continue

        enrolled_at = now
        tid = make_tracking_id(
            batch_id=summary.batch_id,
            run_id=summary.run_id,
            strategy_id=r.strategy_id,
            enrolled_at_utc=enrolled_at,
        )
        strat_dir = run_dir / "strategies" / r.strategy_id
        ev_path = strat_dir / "evidence_manifest.json"
        sc_path = strat_dir / "strategy_scorecard.json"
        eq_path = strat_dir / "equity_curve.json"
        ev_sha = sc_sha = eq_sha = None
        if ev_path.is_file():
            ev_sha = canonical_json_sha256(_read_json(ev_path))
        if sc_path.is_file():
            sc_sha = canonical_json_sha256(_read_json(sc_path))
        if eq_path.is_file():
            eq_sha = canonical_json_sha256(_read_json(eq_path))

        gates = r.gate_summary.model_dump(mode="json")
        notes: list[str] = []
        if portfolio_cf.portfolio_gate_status in ("DUPLICATIVE", "WARNING"):
            notes.append(f"PORTFOLIO_BATCH_GATE:{portfolio_cf.portfolio_gate_status}")
        if portfolio_cf.duplicate_alpha_warnings:
            notes.append("DUPLICATE_ALPHA_WARNINGS_CARRIED_FORWARD")

        candidate = PaperTrackingCandidate(
            strategy_id=r.strategy_id,
            strategy_type="unknown",
            batch_id=summary.batch_id,
            run_id=summary.run_id,
            enrolled_at_utc=enrolled_at,
            promotion_eligible_at_enrollment=bool(r.gate_summary.promotion_eligible),
            synthetic_demo=demo,
            paper_posture=posture,
            data_plane_at_enrollment=r.data_plane,
            gauntlet_gate_snapshot=gates,
            source_evidence_manifest_sha256=ev_sha,
            source_strategy_scorecard_sha256=sc_sha,
            source_equity_curve_sha256=eq_sha,
        )
        # strategy_type from batch - not in StrategyRunResult directly; read input_manifest
        inp = strat_dir / "input_manifest.json"
        if inp.is_file():
            spec = _read_json(inp).get("spec") or {}
            candidate = candidate.model_copy(
                update={"strategy_type": str(spec.get("strategy_type", candidate.strategy_type))}
            )

        rules = default_kill_rules()
        manifest = PaperTrackingManifest(
            tracking_id=tid,
            batch_run_dir=str(run_dir),
            candidate=candidate,
            portfolio_carry_forward=portfolio_cf,
            kill_rules=rules,
            enrollment_notes=notes,
        )
        plain = manifest.model_dump(mode="json")
        manifest = manifest.model_copy(update={"manifest_sha256": canonical_json_sha256(plain)})
        tdir = out_root / tid
        tdir.mkdir(parents=True, exist_ok=False)
        _write_json(tdir / "paper_tracking_manifest.json", {**manifest.model_dump(mode="json")})
        _write_json(
            tdir / "kill_rules.json",
            {"schema_version": "paper_kill_rules/v1", "rules": [x.model_dump(mode="json") for x in rules]},
        )
        enrolled.append(manifest)

    return enrolled


def append_daily_snapshot(
    tracking_id: str,
    *,
    observation_date: date | None = None,
    repo_root: Path | None = None,
) -> tuple[DailySignalSnapshot, RealizedOutcomeSnapshot]:
    root = _paper_tracking_root(repo_root)
    tdir = root / tracking_id
    mpath = tdir / "paper_tracking_manifest.json"
    if not mpath.is_file():
        raise FileNotFoundError(f"MANIFEST_MISSING:{mpath}")
    manifest = PaperTrackingManifest.model_validate(_read_json(mpath))
    obs = observation_date or date.today()
    test_clock = os.environ.get("STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE", "").strip()
    if test_clock:
        obs = date.fromisoformat(test_clock)

    exposure = _deterministic_exposure(manifest.tracking_id, obs)
    sig = DailySignalSnapshot(
        tracking_id=manifest.tracking_id,
        strategy_id=manifest.candidate.strategy_id,
        observation_date_utc=obs,
        signal_exposure=exposure,
        signal_metadata={"deterministic_seed": f"{manifest.tracking_id}|{obs.isoformat()}"},
    )
    plain_sig = sig.model_dump(mode="json")
    sig = sig.model_copy(update={"evidence_sha256": canonical_json_sha256(plain_sig)})

    sig_dir = tdir / "snapshots" / "signals"
    _write_json(sig_dir / f"{obs.isoformat()}.json", {**sig.model_dump(mode="json")})

    # 1d return from deterministic stream; cumulative from previous outcome
    h2 = hashlib.sha256(f"out|{manifest.tracking_id}|{obs.isoformat()}".encode()).digest()
    u2 = int.from_bytes(h2[:8], "big", signed=False) / float(2**64)
    r1d = float((u2 - 0.5) * 0.02)
    prev_cum = 1.0
    out_dir = tdir / "snapshots" / "outcomes"
    prev_files = sorted(out_dir.glob("*.json")) if out_dir.is_dir() else []
    if prev_files:
        try:
            last_o = RealizedOutcomeSnapshot.model_validate(_read_json(prev_files[-1]))
            prev_cum = last_o.cumulative_paper_equity_factor
        except (ValueError, KeyError, OSError):
            prev_cum = 1.0
    cum = prev_cum * (1.0 + r1d)

    out = RealizedOutcomeSnapshot(
        tracking_id=manifest.tracking_id,
        strategy_id=manifest.candidate.strategy_id,
        observation_date_utc=obs,
        paper_return_1d=r1d,
        cumulative_paper_equity_factor=cum,
    )
    plain_out = out.model_dump(mode="json")
    out = out.model_copy(update={"evidence_sha256": canonical_json_sha256(plain_out)})
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / f"{obs.isoformat()}.json", {**out.model_dump(mode="json")})

    return sig, out


def evaluate_paper_tracking(
    tracking_id: str,
    *,
    repo_root: Path | None = None,
) -> PaperTrackingScorecard:
    root = _paper_tracking_root(repo_root)
    tdir = root / tracking_id
    mpath = tdir / "paper_tracking_manifest.json"
    if not mpath.is_file():
        raise FileNotFoundError(f"MANIFEST_MISSING:{mpath}")
    manifest = PaperTrackingManifest.model_validate(_read_json(mpath))
    sig_dir = tdir / "snapshots" / "signals"
    out_dir = tdir / "snapshots" / "outcomes"
    signals: list[DailySignalSnapshot] = []
    if sig_dir.is_dir():
        for p in sorted(sig_dir.glob("*.json")):
            try:
                signals.append(DailySignalSnapshot.model_validate(_read_json(p)))
            except ValueError:
                continue
    outcomes: list[RealizedOutcomeSnapshot] = []
    if out_dir.is_dir():
        for p in sorted(out_dir.glob("*.json")):
            try:
                outcomes.append(RealizedOutcomeSnapshot.model_validate(_read_json(p)))
            except ValueError:
                continue

    baseline = signals[0].signal_exposure if signals else 0.0
    drift = 0.0
    if len(signals) >= 2:
        drift = float(
            sum(abs(s.signal_exposure - baseline) for s in signals[-10:]) / max(1, min(10, len(signals)))
        )

    cum_ret = outcomes[-1].cumulative_paper_equity_factor - 1.0 if outcomes else 0.0
    equity = [1.0]
    for o in outcomes:
        equity.append(o.cumulative_paper_equity_factor)
    peak = equity[0]
    max_dd = 0.0
    for x in equity:
        peak = max(peak, x)
        max_dd = max(max_dd, 1.0 - x / peak if peak > 0 else 0.0)

    enrolled = manifest.candidate.enrolled_at_utc
    now = datetime.now(timezone.utc)
    days_since = (now - enrolled).days
    decay = ExecutionRealismDecayLevel.NONE
    if days_since > 180:
        decay = ExecutionRealismDecayLevel.SEVERE
    elif days_since > 90:
        decay = ExecutionRealismDecayLevel.WARN

    triggered: list[TriggeredRule] = []
    warnings: list[str] = []
    for rule in manifest.kill_rules:
        if rule.kind == FalsificationRuleKind.MAX_CUMULATIVE_LOSS and rule.threshold is not None:
            if cum_ret < float(rule.threshold):
                triggered.append(
                    TriggeredRule(
                        rule_id=rule.rule_id,
                        kind=rule.kind.value,
                        detail=f"cumulative_return={cum_ret:.4f}<threshold={rule.threshold}",
                    )
                )
        elif rule.kind == FalsificationRuleKind.MAX_DRAWDOWN and rule.threshold is not None:
            if max_dd > float(rule.threshold):
                triggered.append(
                    TriggeredRule(
                        rule_id=rule.rule_id,
                        kind=rule.kind.value,
                        detail=f"max_drawdown={max_dd:.4f}>threshold={rule.threshold}",
                    )
                )
        elif rule.kind == FalsificationRuleKind.SIGNAL_DRIFT and rule.threshold is not None:
            if drift > float(rule.threshold):
                triggered.append(
                    TriggeredRule(
                        rule_id=rule.rule_id,
                        kind=rule.kind.value,
                        detail=f"drift_score={drift:.4f}>threshold={rule.threshold}",
                    )
                )
        elif rule.kind == FalsificationRuleKind.EXECUTION_ASSUMPTION_STALE and rule.threshold is not None:
            if float(days_since) > float(rule.threshold):
                triggered.append(
                    TriggeredRule(
                        rule_id=rule.rule_id,
                        kind=rule.kind.value,
                        detail=f"days_since_enroll={days_since}>threshold={rule.threshold}",
                    )
                )

    if decay == ExecutionRealismDecayLevel.WARN:
        warnings.append("EXECUTION_REALISM_REVALIDATION_RECOMMENDED")
    elif decay == ExecutionRealismDecayLevel.SEVERE:
        warnings.append("EXECUTION_REALISM_DECAY_SEVERE")

    p_warns = list(manifest.portfolio_carry_forward.duplicate_alpha_warnings)
    if manifest.portfolio_carry_forward.portfolio_gate_status == "DUPLICATIVE":
        warnings.append("PORTFOLIO_DUPLICATIVE_AT_ENROLLMENT")

    kill = KillState.ACTIVE
    if triggered:
        kill = KillState.KILLED
    elif warnings:
        kill = KillState.WARNED

    sc = PaperTrackingScorecard(
        tracking_id=manifest.tracking_id,
        strategy_id=manifest.candidate.strategy_id,
        evaluated_at_utc=now,
        days_of_signals=len(signals),
        cumulative_paper_return=cum_ret,
        drift_score=drift,
        execution_realism_decay_level=decay,
        kill_state=kill,
        triggered_rules=triggered,
        warnings=warnings,
        portfolio_carry_forward_warnings=p_warns,
    )
    plain = sc.model_dump(mode="json")
    sc = sc.model_copy(update={"scorecard_sha256": canonical_json_sha256(plain)})
    _write_json(tdir / "paper_tracking_scorecard.json", {**sc.model_dump(mode="json")})
    return sc


def run_paper_tracking_daily(
    run_date: date,
    *,
    repo_root: Path | None = None,
    tracking_root: Path | None = None,
) -> dict[str, Any]:
    """Snapshot, evaluate, and assess each enrolled tracking directory; continue on errors."""

    prev_pt = os.environ.get("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT")
    if tracking_root is not None:
        os.environ["STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT"] = str(Path(tracking_root).resolve())
    try:
        root = _paper_tracking_root(repo_root)
        processed: list[str] = []
        failures: list[dict[str, str]] = []
        for mpath in sorted(root.glob("*/paper_tracking_manifest.json")):
            tid = mpath.parent.name
            try:
                append_daily_snapshot(tid, observation_date=run_date, repo_root=repo_root)
                evaluate_paper_tracking(tid, repo_root=repo_root)
                assess_paper_tracking(tid, repo_root=repo_root)
                processed.append(tid)
            except Exception as exc:  # pragma: no cover - broad collect for operator manifest
                failures.append({"tracking_id": tid, "error": f"{type(exc).__name__}:{exc}"})
        out_dir = root / "daily_runs" / run_date.isoformat()
        payload = {
            "schema_version": "paper_tracking_daily_run/v1",
            "run_date_utc": run_date.isoformat(),
            "tracking_root": str(root),
            "processed_tracking_ids": processed,
            "failure_count": len(failures),
            "failures": failures,
        }
        _write_json(out_dir / "daily_run_manifest.json", payload)
        return payload
    finally:
        if tracking_root is not None:
            if prev_pt is None:
                os.environ.pop("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", None)
            else:
                os.environ["STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT"] = prev_pt



__all__ = [
    "append_daily_snapshot",
    "apply_manifest_governance_updates",
    "assess_paper_tracking",
    "derive_candidate_lifecycle_assessment",
    "enroll_strategies_from_batch_run",
    "evaluate_paper_tracking",
    "list_paper_tracking_entries",
    "make_tracking_id",
    "read_persisted_lifecycle_assessment",
    "run_paper_tracking_daily",
    "_paper_tracking_root",
]
