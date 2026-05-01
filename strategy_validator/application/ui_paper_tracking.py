"""Read-plane payloads for paper tracking artifacts (no execution)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_tracking_ops import (
    derive_candidate_lifecycle_assessment,
    read_persisted_lifecycle_assessment,
)
from strategy_validator.contracts.candidate_lifecycle import CandidateLifecycleAssessment
from strategy_validator.contracts.paper_tracking import (
    PaperTrackingManifest,
    PaperTrackingScorecard,
)

_SCHEMA = "ui_paper_tracking/v2"


def _root(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    root = repo_root or Path.cwd()
    return (root / "artifacts" / "paper_tracking").resolve()


def _find_manifests(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.glob("*/paper_tracking_manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def _safe_read(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def discover_latest_paper_tracking(*, repo_root: Path | None = None) -> tuple[Path | None, dict[str, Any] | None]:
    root = _root(repo_root)
    for mp in _find_manifests(root):
        data = _safe_read(mp)
        if data is not None:
            tid = mp.parent.name
            bundle = _build_tracking_bundle(mp.parent, tid, data)
            return mp, bundle
    return None, None


def discover_paper_tracking(tracking_id: str, *, repo_root: Path | None = None) -> tuple[Path | None, dict[str, Any] | None]:
    root = _root(repo_root)
    tid = tracking_id.strip()
    if not tid or ".." in tid or "/" in tid or "\\" in tid:
        return None, None
    tdir = (root / tid).resolve()
    try:
        tdir.relative_to(root.resolve())
    except ValueError:
        return None, None
    mp = tdir / "paper_tracking_manifest.json"
    if not mp.is_file():
        return None, None
    data = _safe_read(mp)
    if data is None:
        return None, None
    return mp, _build_tracking_bundle(tdir, tid, data)


def _lifecycle_payload(tdir: Path, manifest: dict[str, Any], score: dict[str, Any] | None) -> dict[str, Any]:
    try:
        m = PaperTrackingManifest.model_validate(manifest)
    except ValueError:
        return {
            "lifecycle_state": None,
            "lifecycle_kill_rule_posture": None,
            "lifecycle_basis_summary": None,
            "lifecycle_blockers": [],
            "lifecycle_promotion_disclaimer": None,
            "lifecycle_assessment_artifact": None,
            "promotion_review_ready": False,
        }
    sc_obj: PaperTrackingScorecard | None = None
    if score is not None:
        try:
            sc_obj = PaperTrackingScorecard.model_validate(score)
        except ValueError:
            sc_obj = None
    derived = derive_candidate_lifecycle_assessment(m, sc_obj, tracking_dir=tdir)
    persisted_model = read_persisted_lifecycle_assessment(tdir)
    persisted = persisted_model.model_dump(mode="json") if persisted_model is not None else None
    return {
        "lifecycle_state": derived.current_state.value,
        "lifecycle_kill_rule_posture": derived.kill_rule_status,
        "lifecycle_basis_summary": derived.basis_summary,
        "lifecycle_blockers": list(derived.blockers),
        "lifecycle_promotion_disclaimer": derived.promotion_review_disclaimer,
        "lifecycle_assessment_artifact": persisted,
        "promotion_review_ready": derived.promotion_review_ready,
    }


def _promotion_packet_summary(tdir: Path) -> dict[str, Any] | None:
    p = tdir / "promotion_review_packet.json"
    raw = _safe_read(p)
    if raw is None:
        return None
    rec = raw.get("recommendation") if isinstance(raw.get("recommendation"), dict) else {}
    return {
        "packet_id": raw.get("packet_id"),
        "recommendation": rec.get("recommendation") if isinstance(rec, dict) else None,
        "rationale": rec.get("rationale") if isinstance(rec, dict) else None,
        "packet_sha256": raw.get("packet_sha256"),
        "artifact_path": str(p),
    }


def _build_tracking_bundle(tdir: Path, tracking_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    score_path = tdir / "paper_tracking_scorecard.json"
    score = _safe_read(score_path)
    sig_dir = tdir / "snapshots" / "signals"
    out_dir = tdir / "snapshots" / "outcomes"
    signals: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []
    if sig_dir.is_dir():
        for p in sorted(sig_dir.glob("*.json"), reverse=True)[:64]:
            row = _safe_read(p)
            if row:
                signals.append({"path": str(p), "summary": row})
    if out_dir.is_dir():
        for p in sorted(out_dir.glob("*.json"), reverse=True)[:64]:
            row = _safe_read(p)
            if row:
                outcomes.append({"path": str(p), "summary": row})
    life = _lifecycle_payload(tdir, manifest, score)
    return {
        "tracking_id": tracking_id,
        "manifest": manifest,
        "scorecard": score,
        **life,
        "promotion_review_packet_summary": _promotion_packet_summary(tdir),
        "signal_history_recent": list(reversed(signals)),
        "outcome_history_recent": list(reversed(outcomes)),
        "tracking_dir": str(tdir),
    }


def _latest_daily_run_manifest(root: Path) -> dict[str, Any] | None:
    paths = sorted(root.glob("daily_runs/*/daily_run_manifest.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    if not paths:
        return None
    data = _safe_read(paths[0])
    if data is None:
        return None
    return {"manifest_path": str(paths[0]), **data}


def build_ui_paper_tracking_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    path, bundle = discover_latest_paper_tracking(repo_root=repo_root)
    degraded: list[str] = []
    if path is None:
        degraded.append("NO_PAPER_TRACKING_ARTIFACTS")
    scan = _root(repo_root)
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scan_root": str(scan),
        "manifest_path": str(path) if path else None,
        "degraded": degraded,
        "latest": bundle,
        "latest_daily_run": _latest_daily_run_manifest(scan),
    }


def build_ui_paper_tracking_detail_payload(tracking_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    path, bundle = discover_paper_tracking(tracking_id, repo_root=repo_root)
    degraded: list[str] = []
    if bundle is None:
        degraded.append("PAPER_TRACKING_NOT_FOUND")
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tracking_id": tracking_id,
        "manifest_path": str(path) if path else None,
        "degraded": degraded,
        "tracking": bundle,
    }


__all__ = [
    "build_ui_paper_tracking_detail_payload",
    "build_ui_paper_tracking_latest_payload",
    "discover_latest_paper_tracking",
    "discover_paper_tracking",
]
