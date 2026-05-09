"""Pure paper-tracking lifecycle assessment projection."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.candidate_lifecycle import (
    CandidateLifecycleAssessment,
    CandidateLifecycleEvidenceRef,
    CandidateLifecycleState,
    CandidateLifecycleTransitionReason,
)
from strategy_validator.contracts.paper_tracking import (
    ExecutionRealismDecayLevel,
    FalsificationRuleKind,
    KillRulePosture,
    KillState,
    PaperTrackingManifest,
    PaperTrackingScorecard,
    TriggeredRule,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


_HARD_KILL_KINDS: frozenset[FalsificationRuleKind] = frozenset(
    {
        FalsificationRuleKind.MAX_CUMULATIVE_LOSS,
        FalsificationRuleKind.MAX_DRAWDOWN,
        FalsificationRuleKind.MANUAL_OPERATOR_HALT,
    }
)
_SOFT_KILL_KINDS: frozenset[FalsificationRuleKind] = frozenset(
    {
        FalsificationRuleKind.SIGNAL_DRIFT,
        FalsificationRuleKind.EXECUTION_ASSUMPTION_STALE,
    }
)


def _kill_rule_posture(triggered: list[TriggeredRule]) -> KillRulePosture:
    hard = False
    soft = False
    for t in triggered:
        try:
            kind = FalsificationRuleKind(t.kind)
        except ValueError:
            continue
        if kind in _HARD_KILL_KINDS:
            hard = True
        elif kind in _SOFT_KILL_KINDS:
            soft = True
    if hard:
        return KillRulePosture.HARD_TRIGGERED
    if soft:
        return KillRulePosture.SOFT_TRIGGERED
    return KillRulePosture.NONE


def _duplicative_blocks_promotion(manifest: PaperTrackingManifest) -> bool:
    gate = manifest.portfolio_carry_forward.portfolio_gate_status
    if gate != "DUPLICATIVE":
        return False
    g = manifest.governance
    if g.allow_promotion_despite_duplicative and g.duplicative_promotion_rationale.strip():
        return False
    return True


def _gauntlet_summary_from_manifest(manifest: PaperTrackingManifest) -> dict[str, Any]:
    g = manifest.candidate.gauntlet_gate_snapshot or {}
    return {
        "promotion_eligible_at_enrollment": g.get("promotion_eligible"),
        "paper_posture": manifest.candidate.paper_posture.value,
        "data_plane_at_enrollment": manifest.candidate.data_plane_at_enrollment,
    }


def _finalize_lifecycle_assessment(
    base: CandidateLifecycleAssessment,
) -> CandidateLifecycleAssessment:
    plain = base.model_dump(mode="json", exclude={"lifecycle_assessment_sha256"})
    digest = canonical_json_sha256(plain)
    return base.model_copy(update={"lifecycle_assessment_sha256": digest})


def _assessment_shell(
    *,
    manifest: PaperTrackingManifest,
    scorecard: PaperTrackingScorecard | None,
    state: CandidateLifecycleState,
    basis_summary: str,
    blockers: list[str],
    warnings: list[str],
    kill_posture: KillRulePosture,
    promotion_ready: bool,
    previous: CandidateLifecycleAssessment | None,
    assessed_at_utc: datetime,
    tracking_dir: Path | None,
    transition_reason: CandidateLifecycleTransitionReason = CandidateLifecycleTransitionReason.SCORECARD_UPDATED,
) -> CandidateLifecycleAssessment:
    tid = manifest.tracking_id
    sid = manifest.candidate.strategy_id
    m_sha = manifest.manifest_sha256 or canonical_json_sha256(
        manifest.model_dump(mode="json", exclude={"manifest_sha256"})
    )
    sc_digest = scorecard.scorecard_sha256 if scorecard else None
    refs: list[CandidateLifecycleEvidenceRef] = []
    if tracking_dir is not None:
        mp = tracking_dir / "paper_tracking_manifest.json"
        refs.append(
            CandidateLifecycleEvidenceRef(
                ref_kind="paper_tracking_manifest",
                artifact_path=str(mp),
                sha256=m_sha or None,
            )
        )
        if scorecard is not None:
            sp = tracking_dir / "paper_tracking_scorecard.json"
            refs.append(
                CandidateLifecycleEvidenceRef(
                    ref_kind="paper_tracking_scorecard",
                    artifact_path=str(sp),
                    sha256=sc_digest,
                )
            )
    dup_warn = manifest.portfolio_carry_forward.portfolio_gate_status == "DUPLICATIVE"
    base = CandidateLifecycleAssessment(
        tracking_id=tid,
        strategy_id=sid,
        batch_id=manifest.candidate.batch_id,
        run_id=manifest.candidate.run_id,
        current_state=state,
        recommended_state=state,
        previous_state=previous.current_state if previous else None,
        transition_reason=transition_reason,
        assessed_at_utc=assessed_at_utc,
        gauntlet_status_summary=_gauntlet_summary_from_manifest(manifest),
        paper_tracking_scorecard_digest=sc_digest,
        kill_rule_status=kill_posture.value,
        duplicative_portfolio_warning=dup_warn,
        synthetic_demo=manifest.candidate.synthetic_demo,
        promotion_review_ready=promotion_ready,
        blockers=blockers,
        warnings=warnings,
        evidence_refs=refs,
        basis_summary=basis_summary,
        manifest_sha256=m_sha,
    )
    return _finalize_lifecycle_assessment(base)


def derive_candidate_lifecycle_assessment(
    manifest: PaperTrackingManifest,
    scorecard: PaperTrackingScorecard | None,
    *,
    assessed_at_utc: datetime | None = None,
    tracking_dir: Path | None = None,
    previous: CandidateLifecycleAssessment | None = None,
) -> CandidateLifecycleAssessment:
    """Project lifecycle state from manifest + optional scorecard (no I/O)."""

    when = assessed_at_utc or datetime.now(timezone.utc)

    if scorecard is None:
        return _assessment_shell(
            manifest=manifest,
            scorecard=None,
            state=CandidateLifecycleState.RESEARCH_CANDIDATE,
            basis_summary="Manifest present; scorecard not produced yet — run evaluate then assess.",
            blockers=["SCORECARD_MISSING"],
            warnings=[],
            kill_posture=KillRulePosture.NONE,
            promotion_ready=False,
            previous=previous,
            assessed_at_utc=when,
            tracking_dir=tracking_dir,
            transition_reason=CandidateLifecycleTransitionReason.INITIAL,
        )

    trig = list(scorecard.triggered_rules)
    posture = _kill_rule_posture(trig)

    if manifest.governance.lifecycle_rejected:
        return _assessment_shell(
            manifest=manifest,
            scorecard=scorecard,
            state=CandidateLifecycleState.REJECTED,
            basis_summary="Governance marked lifecycle_rejected on manifest.",
            blockers=["LIFECYCLE_REJECTED_GOVERNANCE"],
            warnings=list(scorecard.warnings),
            kill_posture=posture,
            promotion_ready=False,
            previous=previous,
            assessed_at_utc=when,
            tracking_dir=tracking_dir,
            transition_reason=CandidateLifecycleTransitionReason.MANUAL_REJECT,
        )

    if posture == KillRulePosture.HARD_TRIGGERED:
        return _assessment_shell(
            manifest=manifest,
            scorecard=scorecard,
            state=CandidateLifecycleState.KILLED_BY_RULE,
            basis_summary="Hard falsification rule triggered (loss, drawdown, or operator halt).",
            blockers=[t.detail for t in trig],
            warnings=list(scorecard.warnings),
            kill_posture=posture,
            promotion_ready=False,
            previous=previous,
            assessed_at_utc=when,
            tracking_dir=tracking_dir,
            transition_reason=CandidateLifecycleTransitionReason.KILL_RULE_TRIGGERED,
        )

    if posture == KillRulePosture.SOFT_TRIGGERED:
        return _assessment_shell(
            manifest=manifest,
            scorecard=scorecard,
            state=CandidateLifecycleState.KILL_CANDIDATE,
            basis_summary="Soft falsification rule triggered (drift or execution staleness) — review before hard kill.",
            blockers=[t.detail for t in trig],
            warnings=list(scorecard.warnings),
            kill_posture=posture,
            promotion_ready=False,
            previous=previous,
            assessed_at_utc=when,
            tracking_dir=tracking_dir,
            transition_reason=CandidateLifecycleTransitionReason.KILL_RULE_TRIGGERED,
        )

    if scorecard.execution_realism_decay_level == ExecutionRealismDecayLevel.SEVERE:
        return _assessment_shell(
            manifest=manifest,
            scorecard=scorecard,
            state=CandidateLifecycleState.DEGRADED,
            basis_summary="Execution realism decay severe — revalidate assumptions.",
            blockers=["EXECUTION_REALISM_DECAY_SEVERE"],
            warnings=list(scorecard.warnings),
            kill_posture=KillRulePosture.NONE,
            promotion_ready=False,
            previous=previous,
            assessed_at_utc=when,
            tracking_dir=tracking_dir,
        )

    blockers: list[str] = []
    if manifest.candidate.synthetic_demo:
        blockers.append("SYNTHETIC_DEMO_EXCLUDES_PROMOTION_REVIEW")
    if _duplicative_blocks_promotion(manifest):
        blockers.append("PORTFOLIO_DUPLICATIVE_REQUIRES_GOVERNANCE_OVERRIDE")

    promotion_ready = (
        not manifest.candidate.synthetic_demo
        and not _duplicative_blocks_promotion(manifest)
        and scorecard.kill_state == KillState.ACTIVE
        and not trig
        and scorecard.days_of_signals >= 1
        and scorecard.drift_score < 0.75
        and scorecard.execution_realism_decay_level != ExecutionRealismDecayLevel.SEVERE
        and scorecard.cumulative_paper_return >= -0.08
    )

    if promotion_ready:
        return _assessment_shell(
            manifest=manifest,
            scorecard=scorecard,
            state=CandidateLifecycleState.PROMOTION_REVIEW_READY,
            basis_summary="Paper evidence meets promotion-review gate (not approval).",
            blockers=[],
            warnings=list(scorecard.warnings),
            kill_posture=KillRulePosture.NONE,
            promotion_ready=True,
            previous=previous,
            assessed_at_utc=when,
            tracking_dir=tracking_dir,
            transition_reason=CandidateLifecycleTransitionReason.PROMOTION_GATE,
        )

    if scorecard.kill_state == KillState.WARNED or bool(scorecard.warnings):
        return _assessment_shell(
            manifest=manifest,
            scorecard=scorecard,
            state=CandidateLifecycleState.WATCHLIST,
            basis_summary="Warnings or warned kill posture — elevated monitoring.",
            blockers=list(blockers) + list(scorecard.warnings),
            warnings=list(scorecard.warnings),
            kill_posture=KillRulePosture.NONE,
            promotion_ready=False,
            previous=previous,
            assessed_at_utc=when,
            tracking_dir=tracking_dir,
        )

    return _assessment_shell(
        manifest=manifest,
        scorecard=scorecard,
        state=CandidateLifecycleState.PAPER_TRACKING,
        basis_summary="Active paper tracking without promotion-review gate satisfied.",
        blockers=blockers,
        warnings=list(scorecard.warnings),
        kill_posture=KillRulePosture.NONE,
        promotion_ready=False,
        previous=previous,
        assessed_at_utc=when,
        tracking_dir=tracking_dir,
    )


__all__ = ["derive_candidate_lifecycle_assessment"]
