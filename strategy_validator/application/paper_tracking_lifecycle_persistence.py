"""Paper-tracking lifecycle persistence and governance mutation helpers."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_tracking_common import (
    _paper_tracking_root,
    _read_json,
    _write_json,
)
from strategy_validator.application.paper_tracking_lifecycle_assessment import (
    derive_candidate_lifecycle_assessment,
)
from strategy_validator.contracts.candidate_lifecycle import (
    CandidateLifecycleAssessment,
    CandidateLifecycleTransitionReason,
)
from strategy_validator.contracts.paper_tracking import (
    PaperTrackingGovernance,
    PaperTrackingManifest,
    PaperTrackingScorecard,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _read_scorecard_optional(tdir: Path) -> PaperTrackingScorecard | None:
    p = tdir / "paper_tracking_scorecard.json"
    if not p.is_file():
        return None
    try:
        return PaperTrackingScorecard.model_validate(_read_json(p))
    except ValueError:
        return None


def _migrate_legacy_lifecycle_dict(raw: dict[str, Any]) -> dict[str, Any]:
    """Map pre-v1 candidate_lifecycle_assessment.json into lifecycle_assessment/v1 shape."""
    st = raw.get("current_state") or raw.get("state")
    if not st:
        raise ValueError("legacy lifecycle missing state")
    kp = raw.get("kill_rule_status") or raw.get("kill_rule_posture", "NONE")
    if hasattr(kp, "value"):
        kp = kp.value
    return {
        "schema_version": "lifecycle_assessment/v1",
        "tracking_id": raw["tracking_id"],
        "strategy_id": raw["strategy_id"],
        "batch_id": raw.get("batch_id", ""),
        "run_id": raw.get("run_id", ""),
        "current_state": st,
        "recommended_state": st,
        "previous_state": None,
        "transition_reason": CandidateLifecycleTransitionReason.SCORECARD_UPDATED.value,
        "assessed_at_utc": raw["assessed_at_utc"],
        "gauntlet_status_summary": raw.get("gauntlet_status_summary") or {},
        "paper_tracking_scorecard_digest": raw.get("paper_tracking_scorecard_digest")
        or raw.get("scorecard_sha256"),
        "kill_rule_status": str(kp),
        "duplicative_portfolio_warning": bool(raw.get("duplicative_portfolio_warning", False)),
        "synthetic_demo": bool(raw.get("synthetic_demo", False)),
        "promotion_review_ready": bool(raw.get("promotion_review_ready", st == "PROMOTION_REVIEW_READY")),
        "blockers": list(raw.get("blockers") or []),
        "warnings": list(raw.get("warnings") or []),
        "evidence_refs": raw.get("evidence_refs") or [],
        "basis_summary": raw.get("basis_summary", ""),
        "manifest_sha256": raw.get("manifest_sha256", ""),
        "promotion_review_disclaimer": raw.get(
            "promotion_review_disclaimer",
            "PROMOTION_REVIEW_READY is an evidence gate only — not live trading approval or deployment promotion.",
        ),
        "lifecycle_assessment_sha256": raw.get("lifecycle_assessment_sha256", ""),
    }


def _read_lifecycle_assessment_optional(tdir: Path) -> CandidateLifecycleAssessment | None:
    for name in ("lifecycle_assessment.json", "candidate_lifecycle_assessment.json"):
        p = tdir / name
        if not p.is_file():
            continue
        try:
            raw = _read_json(p)
        except (OSError, json.JSONDecodeError):
            continue
        if raw.get("schema_version") == "candidate_lifecycle_assessment/v1":
            try:
                raw = _migrate_legacy_lifecycle_dict(raw)
            except (KeyError, ValueError, TypeError):
                continue
        try:
            return CandidateLifecycleAssessment.model_validate(raw)
        except ValueError:
            continue
    return None


def apply_manifest_governance_updates(
    tracking_id: str,
    *,
    allow_promotion_despite_duplicative: bool | None = None,
    duplicative_promotion_rationale: str | None = None,
    lifecycle_rejected: bool | None = None,
    repo_root: Path | None = None,
) -> PaperTrackingManifest:
    """Merge governance fields, rewrite manifest + digest on disk."""

    root = _paper_tracking_root(repo_root)
    tdir = root / tracking_id
    mpath = tdir / "paper_tracking_manifest.json"
    if not mpath.is_file():
        raise FileNotFoundError(f"MANIFEST_MISSING:{mpath}")
    manifest = PaperTrackingManifest.model_validate(_read_json(mpath))
    gov = manifest.governance.model_dump()
    if allow_promotion_despite_duplicative is not None:
        gov["allow_promotion_despite_duplicative"] = allow_promotion_despite_duplicative
    if duplicative_promotion_rationale is not None:
        gov["duplicative_promotion_rationale"] = duplicative_promotion_rationale
    if lifecycle_rejected is not None:
        gov["lifecycle_rejected"] = lifecycle_rejected
    manifest = manifest.model_copy(update={"governance": PaperTrackingGovernance.model_validate(gov)})
    plain = manifest.model_dump(mode="json", exclude={"manifest_sha256"})
    manifest = manifest.model_copy(update={"manifest_sha256": canonical_json_sha256(plain)})
    _write_json(mpath, {**manifest.model_dump(mode="json")})
    return manifest


def assess_paper_tracking(
    tracking_id: str,
    *,
    repo_root: Path | None = None,
    allow_promotion_despite_duplicative: bool | None = None,
    duplicative_promotion_rationale: str | None = None,
    lifecycle_rejected: bool | None = None,
) -> CandidateLifecycleAssessment:
    """Write candidate_lifecycle_assessment.json from current manifest/scorecard."""

    tdir = _paper_tracking_root(repo_root) / tracking_id
    if (
        allow_promotion_despite_duplicative is not None
        or duplicative_promotion_rationale is not None
        or lifecycle_rejected is not None
    ):
        manifest = apply_manifest_governance_updates(
            tracking_id,
            allow_promotion_despite_duplicative=allow_promotion_despite_duplicative,
            duplicative_promotion_rationale=duplicative_promotion_rationale,
            lifecycle_rejected=lifecycle_rejected,
            repo_root=repo_root,
        )
    else:
        mpath = tdir / "paper_tracking_manifest.json"
        if not mpath.is_file():
            raise FileNotFoundError(f"MANIFEST_MISSING:{mpath}")
        manifest = PaperTrackingManifest.model_validate(_read_json(mpath))

    score = _read_scorecard_optional(tdir)
    previous = _read_lifecycle_assessment_optional(tdir)
    assessment = derive_candidate_lifecycle_assessment(
        manifest, score, tracking_dir=tdir, previous=previous
    )
    assessment = assessment.model_copy(update={"manifest_sha256": manifest.manifest_sha256})
    plain = assessment.model_dump(mode="json", exclude={"lifecycle_assessment_sha256"})
    assessment = assessment.model_copy(
        update={"lifecycle_assessment_sha256": canonical_json_sha256(plain)}
    )
    _write_json(tdir / "lifecycle_assessment.json", {**assessment.model_dump(mode="json")})
    return assessment


read_persisted_lifecycle_assessment = _read_lifecycle_assessment_optional


__all__ = [
    "apply_manifest_governance_updates",
    "assess_paper_tracking",
    "read_persisted_lifecycle_assessment",
]
