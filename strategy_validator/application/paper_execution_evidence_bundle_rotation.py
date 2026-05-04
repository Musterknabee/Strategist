"""Paper execution evidence-bundle rotation recommendation artifacts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_evidence_bundle import _paper_broker_root, _safe_timestamp
from strategy_validator.contracts.paper_execution import (
    PaperExecutionEvidenceBundleDriftView,
    PaperExecutionEvidenceBundleRotationArtifact,
    PaperExecutionEvidenceBundleRotationView,
    PaperExecutionEvidenceBundleVerificationView,
    PaperExecutionEvidenceBundleView,
    PaperExecutionTimelineSummary,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _tracking_id(*values: Any) -> str | None:
    for value in values:
        if value is None:
            continue
        raw = getattr(value, "tracking_id", None)
        if raw:
            return str(raw)
    return None


def build_paper_execution_evidence_bundle_rotation_artifact(
    *,
    timeline_summary: PaperExecutionTimelineSummary,
    latest_evidence_bundle: PaperExecutionEvidenceBundleView | None = None,
    latest_evidence_bundle_verification: PaperExecutionEvidenceBundleVerificationView | None = None,
    latest_evidence_bundle_drift: PaperExecutionEvidenceBundleDriftView | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionEvidenceBundleRotationArtifact:
    """Build an operator recovery recommendation for bundle rotation."""

    now = generated_at_utc or datetime.now(timezone.utc)
    blockers: list[str] = []
    warnings: list[str] = []
    reasons: list[str] = []
    sequence: list[str] = []

    timeline_status = str(timeline_summary.sequence_status or "EMPTY")
    if timeline_status != "COMPLETE":
        blockers.append("PAPER_EXECUTION_TIMELINE_NOT_COMPLETE_FOR_ROTATION")
        reasons.append("TIMELINE_NOT_COMPLETE")
        status = "BLOCKED"
        trust = "UNTRUSTED"
        sequence.append("Complete missing/blocked paper execution timeline stages before sealing a bundle.")
    elif latest_evidence_bundle is None:
        reasons.append("NO_SEALED_BUNDLE")
        status = "REQUIRED"
        trust = "TRUST_RESTRICTED"
        sequence.extend([
            "strategy-validator-paper-broker seal-evidence-bundle",
            "strategy-validator-paper-broker verify-evidence-bundle",
            "strategy-validator-paper-broker check-evidence-bundle-drift",
        ])
    else:
        verification_status = str(getattr(latest_evidence_bundle_verification, "verification_status", "NO_VERIFICATION") or "NO_VERIFICATION")
        drift_status = str(getattr(latest_evidence_bundle_drift, "drift_status", "NO_DRIFT_CHECK") or "NO_DRIFT_CHECK")
        bundle_status = str(getattr(latest_evidence_bundle, "bundle_status", "UNKNOWN") or "UNKNOWN")
        bundle_trust = str(getattr(latest_evidence_bundle, "trust_banner", "TRUST_RESTRICTED") or "TRUST_RESTRICTED")

        if drift_status == "DRIFTED":
            reasons.append("BUNDLE_DRIFTED")
            status = "REQUIRED"
            trust = "UNTRUSTED"
            sequence.extend([
                "strategy-validator-paper-broker seal-evidence-bundle",
                "strategy-validator-paper-broker verify-evidence-bundle",
                "strategy-validator-paper-broker check-evidence-bundle-drift",
            ])
        elif verification_status not in {"PASS"}:
            reasons.append("BUNDLE_NOT_VERIFIED")
            status = "RECOMMENDED"
            trust = "TRUST_RESTRICTED"
            sequence.extend([
                "strategy-validator-paper-broker verify-evidence-bundle",
                "strategy-validator-paper-broker check-evidence-bundle-drift",
            ])
        elif drift_status in {"NO_DRIFT_CHECK", "UNKNOWN", "NO_BUNDLE", "NO_TIMELINE"}:
            reasons.append("DRIFT_CHECK_MISSING_OR_INCONCLUSIVE")
            status = "RECOMMENDED"
            trust = "TRUST_RESTRICTED"
            sequence.append("strategy-validator-paper-broker check-evidence-bundle-drift")
        elif bundle_status == "SEALED_BLOCKED" or bundle_trust == "UNTRUSTED":
            reasons.append("BUNDLE_BLOCKED_OR_UNTRUSTED")
            status = "REQUIRED"
            trust = "UNTRUSTED"
            sequence.extend([
                "Repair bundle blockers or source artifacts.",
                "strategy-validator-paper-broker seal-evidence-bundle",
                "strategy-validator-paper-broker verify-evidence-bundle",
                "strategy-validator-paper-broker check-evidence-bundle-drift",
            ])
        else:
            reasons.append("CURRENT_BUNDLE_VERIFIED_AND_IN_SYNC")
            status = "NOT_NEEDED"
            trust = "TRUSTED"
            sequence.append("No rotation needed; keep monitoring for new paper execution artifacts.")

    if status == "REQUIRED":
        warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ROTATION_REQUIRED")
    elif status == "RECOMMENDED":
        warnings.append("PAPER_EXECUTION_EVIDENCE_BUNDLE_ROTATION_RECOMMENDED")

    one_hint = " && ".join([cmd for cmd in sequence if cmd.startswith("strategy-validator-paper-broker")]) or None
    artifact = PaperExecutionEvidenceBundleRotationArtifact(
        generated_at_utc=now,
        tracking_id=_tracking_id(latest_evidence_bundle, latest_evidence_bundle_verification, latest_evidence_bundle_drift),
        rotation_status=status,  # type: ignore[arg-type]
        trust_banner=trust,  # type: ignore[arg-type]
        source_bundle_sha256=getattr(latest_evidence_bundle, "bundle_sha256", None) if latest_evidence_bundle else None,
        source_bundle_status=getattr(latest_evidence_bundle, "bundle_status", None) if latest_evidence_bundle else None,
        source_bundle_trust_banner=getattr(latest_evidence_bundle, "trust_banner", None) if latest_evidence_bundle else None,
        source_verification_status=getattr(latest_evidence_bundle_verification, "verification_status", None) if latest_evidence_bundle_verification else None,
        source_verification_trust_banner=getattr(latest_evidence_bundle_verification, "trust_banner", None) if latest_evidence_bundle_verification else None,
        source_drift_status=getattr(latest_evidence_bundle_drift, "drift_status", None) if latest_evidence_bundle_drift else None,
        source_drift_trust_banner=getattr(latest_evidence_bundle_drift, "trust_banner", None) if latest_evidence_bundle_drift else None,
        timeline_sequence_status=timeline_status,
        timeline_event_count=int(timeline_summary.event_count or 0),
        rotation_reason_codes=sorted(set(reasons)),
        recommended_operator_sequence=list(dict.fromkeys(sequence)),
        one_command_sequence_hint=one_hint,
        blockers=sorted(set(blockers)),
        warnings=sorted(set(warnings)),
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_execution_evidence_bundle_rotation_artifact(
    *,
    timeline_summary: PaperExecutionTimelineSummary,
    latest_evidence_bundle: PaperExecutionEvidenceBundleView | None = None,
    latest_evidence_bundle_verification: PaperExecutionEvidenceBundleVerificationView | None = None,
    latest_evidence_bundle_drift: PaperExecutionEvidenceBundleDriftView | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionEvidenceBundleRotationArtifact]:
    artifact = build_paper_execution_evidence_bundle_rotation_artifact(
        timeline_summary=timeline_summary,
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        generated_at_utc=generated_at_utc,
    )
    tracking_id = artifact.tracking_id or "untracked"
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "evidence_bundle_rotations"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_execution_evidence_bundle_rotation.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def _view_from_raw(path: Path, raw: dict[str, Any]) -> PaperExecutionEvidenceBundleRotationView:
    digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
    return PaperExecutionEvidenceBundleRotationView(
        tracking_id=str(raw.get("tracking_id") or "") or None,
        artifact_path=str(path),
        artifact_sha256=digest,
        generated_at_utc=str(raw.get("generated_at_utc") or "") or None,
        rotation_status=str(raw.get("rotation_status") or "UNKNOWN"),  # type: ignore[arg-type]
        trust_banner=str(raw.get("trust_banner") or "TRUST_RESTRICTED"),  # type: ignore[arg-type]
        source_bundle_sha256=str(raw.get("source_bundle_sha256") or "") or None,
        source_bundle_status=str(raw.get("source_bundle_status") or "") or None,
        source_verification_status=str(raw.get("source_verification_status") or "") or None,
        source_drift_status=str(raw.get("source_drift_status") or "") or None,
        timeline_sequence_status=str(raw.get("timeline_sequence_status") or "") or None,
        timeline_event_count=int(raw.get("timeline_event_count") or 0),
        rotation_reason_codes=[str(x) for x in raw.get("rotation_reason_codes", []) if x not in (None, "")] if isinstance(raw.get("rotation_reason_codes"), list) else [],
        recommended_operator_sequence=[str(x) for x in raw.get("recommended_operator_sequence", []) if x not in (None, "")] if isinstance(raw.get("recommended_operator_sequence"), list) else [],
        one_command_sequence_hint=str(raw.get("one_command_sequence_hint") or "") or None,
        blockers=[str(x) for x in raw.get("blockers", []) if x not in (None, "")] if isinstance(raw.get("blockers"), list) else [],
        warnings=[str(x) for x in raw.get("warnings", []) if x not in (None, "")] if isinstance(raw.get("warnings"), list) else [],
    )


def read_paper_execution_evidence_bundle_rotation_views(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
    limit: int = 100,
) -> list[PaperExecutionEvidenceBundleRotationView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/evidence_bundle_rotations/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_execution_evidence_bundle_rotation.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionEvidenceBundleRotationView] = []
    for path in sorted(set(candidates), key=_mtime, reverse=True)[:limit]:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        try:
            rows.append(_view_from_raw(path, raw))
        except ValueError:
            continue
    return sorted(rows, key=lambda row: row.generated_at_utc or "", reverse=True)[:limit]


__all__ = [
    "build_paper_execution_evidence_bundle_rotation_artifact",
    "read_paper_execution_evidence_bundle_rotation_views",
    "write_paper_execution_evidence_bundle_rotation_artifact",
]
