"""Build promotion review packets from paper tracking artifacts (read-plane / CLI only)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_tracking_ops import (
    _paper_tracking_root,
    _read_json,
    derive_candidate_lifecycle_assessment,
    read_persisted_lifecycle_assessment,
)
from strategy_validator.contracts.candidate_lifecycle import CandidateLifecycleState
from strategy_validator.contracts.paper_tracking import PaperTrackingManifest, PaperTrackingScorecard
from strategy_validator.contracts.promotion_review_packet import (
    PromotionReviewChecklist,
    PromotionReviewDecisionRecommendation,
    PromotionReviewEvidenceRef,
    PromotionReviewPacket,
    PromotionReviewRecommendation,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def build_promotion_review_packet(
    tracking_id: str,
    *,
    repo_root: Path | None = None,
) -> PromotionReviewPacket:
    root = _paper_tracking_root(repo_root)
    tdir = root / tracking_id
    mpath = tdir / "paper_tracking_manifest.json"
    if not mpath.is_file():
        raise FileNotFoundError(f"MANIFEST_MISSING:{mpath}")
    manifest = PaperTrackingManifest.model_validate(_read_json(mpath))
    sc_path = tdir / "paper_tracking_scorecard.json"
    scorecard: PaperTrackingScorecard | None = None
    if sc_path.is_file():
        try:
            scorecard = PaperTrackingScorecard.model_validate(_read_json(sc_path))
        except ValueError:
            scorecard = None
    life_path = tdir / "lifecycle_assessment.json"
    persisted = read_persisted_lifecycle_assessment(tdir)
    derived = derive_candidate_lifecycle_assessment(
        manifest, scorecard, tracking_dir=tdir, previous=persisted
    )
    refs: list[PromotionReviewEvidenceRef] = [
        PromotionReviewEvidenceRef(
            ref_kind="paper_tracking_manifest",
            artifact_path=str(mpath),
            sha256=manifest.manifest_sha256 or None,
        )
    ]
    if scorecard is not None:
        refs.append(
            PromotionReviewEvidenceRef(
                ref_kind="paper_tracking_scorecard",
                artifact_path=str(sc_path),
                sha256=scorecard.scorecard_sha256 or None,
            )
        )
    if life_path.is_file():
        refs.append(
            PromotionReviewEvidenceRef(
                ref_kind="lifecycle_assessment",
                artifact_path=str(life_path),
                sha256=derived.lifecycle_assessment_sha256 or None,
            )
        )
    checklist = PromotionReviewChecklist(
        has_manifest=True,
        has_scorecard=scorecard is not None,
        has_lifecycle_assessment=life_path.is_file(),
        has_gauntlet_scorecard_ref=bool(manifest.candidate.source_strategy_scorecard_sha256),
        has_evidence_manifest_ref=bool(manifest.candidate.source_evidence_manifest_sha256),
    )

    blockers: list[str] = []
    warnings: list[str] = []
    risks: list[str] = ["Paper research evidence only; no profitability or live readiness claim."]
    if manifest.candidate.synthetic_demo:
        blockers.append("SYNTHETIC_DEMO_DO_NOT_PROMOTE")
    if manifest.portfolio_carry_forward.portfolio_gate_status == "DUPLICATIVE":
        warnings.append("PORTFOLIO_DUPLICATIVE_CARRY_FORWARD")
        if not (
            manifest.governance.allow_promotion_despite_duplicative
            and manifest.governance.duplicative_promotion_rationale.strip()
        ):
            blockers.append("DUPLICATIVE_REQUIRES_GOVERNANCE_OR_REVIEW")
    if scorecard:
        warnings.extend(scorecard.warnings)
    if not checklist.has_scorecard:
        blockers.append("MISSING_SCORECARD")
    if not checklist.has_evidence_manifest_ref:
        warnings.append("MISSING_SOURCE_EVIDENCE_MANIFEST_SHA256")

    rec: PromotionReviewRecommendation
    rationale: str
    if manifest.candidate.synthetic_demo:
        rec = PromotionReviewRecommendation.DO_NOT_PROMOTE
        rationale = "Synthetic / demo candidate cannot advance to human promotion review for production."
    elif derived.current_state != CandidateLifecycleState.PROMOTION_REVIEW_READY:
        if derived.current_state in (
            CandidateLifecycleState.WATCHLIST,
            CandidateLifecycleState.PAPER_TRACKING,
            CandidateLifecycleState.RESEARCH_CANDIDATE,
        ):
            rec = PromotionReviewRecommendation.REVIEW_FOR_PAPER_EXTENSION
            rationale = "Lifecycle state is not PROMOTION_REVIEW_READY; extend paper evidence or resolve blockers."
        else:
            rec = PromotionReviewRecommendation.DO_NOT_PROMOTE
            rationale = f"Lifecycle state {derived.current_state.value} is not eligible for promotion review packet as READY_FOR_HUMAN_REVIEW."
    elif blockers:
        rec = PromotionReviewRecommendation.DO_NOT_PROMOTE
        rationale = "Missing evidence or governance blockers present."
    else:
        rec = PromotionReviewRecommendation.READY_FOR_HUMAN_REVIEW
        rationale = "Lifecycle PROMOTION_REVIEW_READY with required evidence refs; queue for human review only."

    now = datetime.now(timezone.utc)
    packet_id = f"prp-{uuid.uuid4().hex[:16]}"
    pkt = PromotionReviewPacket(
        packet_id=packet_id,
        tracking_id=manifest.tracking_id,
        strategy_id=manifest.candidate.strategy_id,
        batch_id=manifest.candidate.batch_id,
        run_id=manifest.candidate.run_id,
        generated_at_utc=now,
        candidate_lifecycle_state=derived.current_state.value,
        gauntlet_summary=dict(manifest.candidate.gauntlet_gate_snapshot or {}),
        paper_tracking_summary={
            "days_of_signals": scorecard.days_of_signals if scorecard else 0,
            "cumulative_paper_return": scorecard.cumulative_paper_return if scorecard else None,
            "kill_state": scorecard.kill_state.value if scorecard else None,
        },
        kill_rule_summary={
            "triggered": [t.model_dump(mode="json") for t in scorecard.triggered_rules] if scorecard else [],
            "posture": derived.kill_rule_status,
        },
        execution_realism_summary={"decay_level": scorecard.execution_realism_decay_level.value if scorecard else None},
        robustness_summary={},
        portfolio_correlation_summary={
            "gate": manifest.portfolio_carry_forward.portfolio_gate_status,
            "warnings": manifest.portfolio_carry_forward.duplicate_alpha_warnings,
        },
        provider_data_summary={"status": "NOT_APPLICABLE", "note": "Provider ingestion summary not wired in this packet revision."},
        known_risks=risks,
        blockers=blockers,
        warnings=warnings,
        evidence_refs=refs,
        checklist=checklist,
        recommendation=PromotionReviewDecisionRecommendation(recommendation=rec, rationale=rationale),
    )
    plain = pkt.model_dump(mode="json", exclude={"packet_sha256"})
    pkt = pkt.model_copy(update={"packet_sha256": canonical_json_sha256(plain)})
    _write_json(tdir / "promotion_review_packet.json", {**pkt.model_dump(mode="json")})
    return pkt


__all__ = ["build_promotion_review_packet"]
