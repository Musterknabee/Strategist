"""Consolidated read-plane status for research / paper operating workflows (no secrets; no network)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import (
    artifact_root_directory,
    oracle_cycle_manifest_path,
    paper_broker_status_artifact_path,
    provider_historical_snapshot_run_path,
    provider_paper_loop_manifest_path,
    research_os_runtime_manifest_path,
    strategy_data_directory,
)
from strategy_validator.application.ui_paper_broker import build_ui_paper_broker_status_payload
from strategy_validator.application.ui_paper_tracking import build_ui_paper_tracking_latest_payload
from strategy_validator.application.ui_research_compute import build_ui_research_compute_payload
from strategy_validator.application.strategy_memory_ops import build_ui_strategy_memory_latest_payload
from strategy_validator.application.shadow_book_ops import build_ui_shadow_book_latest_payload
from strategy_validator.application.research_os_closure_ops import build_ui_research_os_closure_latest_payload
from strategy_validator.application.research_os_attestation_ops import build_ui_research_os_attestation_latest_payload
from strategy_validator.application.research_os_briefing_ops import build_ui_research_os_briefing_latest_payload
from strategy_validator.application.research_os_export_ops import build_ui_research_os_export_latest_payload
from strategy_validator.application.research_os_operator_run_ops import build_ui_research_os_operator_run_latest_payload
from strategy_validator.application.research_os_evidence_catalog_ops import build_ui_research_os_evidence_catalog_latest_payload
from strategy_validator.application.research_os_drift_ops import build_ui_research_os_evidence_drift_latest_payload
from strategy_validator.application.research_os_policy_gate_ops import build_ui_research_os_policy_gate_latest_payload
from strategy_validator.application.research_os_exception_ops import build_ui_research_os_exception_latest_payload
from strategy_validator.application.research_os_remediation_ops import build_ui_research_os_remediation_latest_payload
from strategy_validator.application.research_os_release_readiness_ops import build_ui_research_os_release_readiness_latest_payload
from strategy_validator.application.research_os_handoff_ops import build_ui_research_os_handoff_latest_payload
from strategy_validator.application.research_os_handoff_signoff_ops import build_ui_research_os_handoff_signoff_latest_payload
from strategy_validator.application.research_os_review_journal_ops import build_ui_research_os_review_journal_latest_payload
from strategy_validator.research.strategy_thesis_eval import build_ui_strategy_thesis_latest_payload
from strategy_validator.research.strategy_thesis_generator import build_ui_strategy_thesis_generation_latest_payload
from strategy_validator.application.ui_strategy_batch import build_ui_strategy_batch_latest_payload

_SCHEMA = "ui_research_os_status/v1"


def _safe_read(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _newest_glob(root: Path, pattern: str, limit: int = 1) -> list[Path]:
    if not root.is_dir():
        return []
    paths = sorted(root.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return paths[:limit]


def _provider_ingestion_hint(*, repo_root: Path | None = None) -> dict[str, Any]:
    data_root = strategy_data_directory(repo_root)
    manifests = _newest_glob(data_root, "*_manifest.json", 3)
    if not manifests:
        return {
            "status": "NO_ARTIFACTS",
            "artifact_path": None,
            "provider_status": None,
            "pit_status": None,
        }
    p = manifests[0]
    raw = _safe_read(p)
    if raw is None:
        return {"status": "UNREADABLE", "artifact_path": str(p)}
    return {
        "status": "ARTIFACT_PRESENT",
        "artifact_path": str(p),
        "provider_status": raw.get("provider_status"),
        "pit_status": str(raw.get("pit_status", "")),
        "row_count": raw.get("row_count"),
        "manifest_sha256": raw.get("manifest_sha256"),
    }


def _demo_manifest_hint(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or Path.cwd()
    raw_path = os.environ.get("STRATEGY_VALIDATOR_RESEARCH_OS_DEMO_MANIFEST", "").strip()
    if raw_path:
        p = Path(raw_path)
        if not p.is_absolute():
            p = (root / p).resolve()
    else:
        p = (root / "artifacts" / "research_os_demo" / "latest" / "demo_manifest.json").resolve()
    if not p.is_file():
        return {"status": "NOT_PRESENT", "artifact_path": str(p)}
    raw = _safe_read(p)
    if raw is None:
        return {"status": "UNREADABLE", "artifact_path": str(p)}
    return {
        "status": "PRESENT",
        "artifact_path": str(p),
        "run_id": raw.get("run_id"),
        "demo_completed_at_utc": raw.get("demo_completed_at_utc"),
        "ok": raw.get("ok"),
    }


def _provider_historical_snapshot_run_hint(*, repo_root: Path | None = None) -> dict[str, Any]:
    p = provider_historical_snapshot_run_path(repo_root)
    if not p.is_file():
        return {"status": "NOT_PRESENT", "artifact_path": str(p)}
    raw = _safe_read(p)
    if raw is None:
        return {"status": "UNREADABLE", "artifact_path": str(p)}
    return {
        "status": "PRESENT",
        "artifact_path": str(p),
        "ok": raw.get("ok"),
        "network_used": raw.get("network_used"),
        "fixture_path": raw.get("fixture_path"),
        "snapshot_count": len(raw.get("snapshots") or []) if isinstance(raw.get("snapshots"), list) else None,
        "manifest_sha256": raw.get("manifest_sha256"),
    }


def _provider_paper_loop_manifest_hint(*, repo_root: Path | None = None) -> dict[str, Any]:
    p = provider_paper_loop_manifest_path(repo_root)
    if not p.is_file():
        return {"status": "NOT_PRESENT", "artifact_path": str(p)}
    raw = _safe_read(p)
    if raw is None:
        return {"status": "UNREADABLE", "artifact_path": str(p)}
    return {
        "status": "PRESENT",
        "artifact_path": str(p),
        "ok": raw.get("ok"),
        "run_id": raw.get("run_id"),
        "generated_at_utc": str(raw.get("generated_at_utc", "")),
        "warnings": raw.get("warnings"),
        "blockers": raw.get("blockers"),
        "digests": raw.get("digests"),
    }


def _paper_broker_artifact_hint(*, repo_root: Path | None = None) -> dict[str, Any]:
    p = paper_broker_status_artifact_path(repo_root)
    if not p.is_file():
        return {"status": "NOT_PRESENT", "artifact_path": str(p)}
    raw = _safe_read(p)
    if raw is None:
        return {"status": "UNREADABLE", "artifact_path": str(p)}
    return {
        "status": "PRESENT",
        "artifact_path": str(p),
        "policy_status": raw.get("policy_status"),
        "key_configured": raw.get("key_configured"),
        "endpoint_classification": raw.get("endpoint_classification"),
        "manifest_sha256": raw.get("manifest_sha256"),
    }


def _oracle_cycle_manifest_hint(*, repo_root: Path | None = None) -> dict[str, Any]:
    p = oracle_cycle_manifest_path(repo_root)
    if not p.is_file():
        return {"status": "NOT_PRESENT", "artifact_path": str(p)}
    raw = _safe_read(p)
    if raw is None:
        return {"status": "UNREADABLE", "artifact_path": str(p)}
    return {
        "status": "PRESENT",
        "artifact_path": str(p),
        "batch_id": raw.get("batch_id"),
        "run_id": raw.get("run_id"),
        "fusion_posture": raw.get("fusion_posture"),
        "dominant_regime": raw.get("dominant_regime"),
        "news_semantic_source": raw.get("news_semantic_source"),
        "strategy_snapshots": raw.get("strategy_snapshots"),
    }


def _runtime_demo_manifest_hint(*, repo_root: Path | None = None) -> dict[str, Any]:
    p = research_os_runtime_manifest_path(repo_root)
    if not p.is_file():
        return {"status": "NOT_PRESENT", "artifact_path": str(p)}
    raw = _safe_read(p)
    if raw is None:
        return {"status": "UNREADABLE", "artifact_path": str(p)}
    dig = raw.get("manifest_sha256") or raw.get("digests", {}).get("full_manifest_sha256")
    return {
        "status": "PRESENT",
        "artifact_path": str(p),
        "run_id": raw.get("run_id"),
        "generated_at_utc": raw.get("generated_at_utc"),
        "ok": raw.get("ok"),
        "artifact_root": raw.get("artifact_root"),
        "manifest_sha256": dig,
        "blockers": raw.get("blockers"),
        "warnings": raw.get("warnings"),
    }


def _cpcv_from_batch(latest_batch: dict[str, Any] | None) -> dict[str, Any]:
    if not latest_batch:
        return {"status": "NO_BATCH", "summary": None}
    strategies = latest_batch.get("strategies")
    if not isinstance(strategies, list):
        return {"status": "NO_STRATEGIES", "summary": None}
    rows: list[dict[str, Any]] = []
    for s in strategies:
        if not isinstance(s, dict):
            continue
        sid = s.get("strategy_id")
        gate = s.get("cpcv_robustness_gate_status")
        path = s.get("cpcv_artifact_path")
        digest = s.get("cpcv_evidence_sha256")
        if gate or path or digest:
            rows.append(
                {
                    "strategy_id": sid,
                    "cpcv_robustness_gate_status": gate,
                    "cpcv_artifact_path": path,
                    "cpcv_evidence_sha256": digest,
                }
            )
    if not rows:
        return {"status": "NO_CPCV_FIELDS", "summary": None}
    return {"status": "PARTIAL", "strategies": rows[:16]}


def build_ui_research_os_status_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    """Aggregate subsystem hints for operator cockpit; never raises for missing artifacts."""
    root = repo_root or Path.cwd()
    warnings: list[str] = []
    degraded: list[str] = []
    art_base = artifact_root_directory(repo_root)

    batch_payload = build_ui_strategy_batch_latest_payload(repo_root=root)
    batch_latest = batch_payload.get("latest")
    batch_rec = batch_latest if isinstance(batch_latest, dict) else None

    paper_payload = build_ui_paper_tracking_latest_payload(repo_root=root)
    if paper_payload.get("degraded"):
        degraded.extend(str(x) for x in paper_payload["degraded"])

    broker_payload = build_ui_paper_broker_status_payload()
    compute_payload = build_ui_research_compute_payload()
    strategy_memory_payload = build_ui_strategy_memory_latest_payload(repo_root=root)
    strategy_thesis_payload = build_ui_strategy_thesis_latest_payload(repo_root=root)
    strategy_thesis_generation_payload = build_ui_strategy_thesis_generation_latest_payload(repo_root=root)
    shadow_book_payload = build_ui_shadow_book_latest_payload(repo_root=root)
    research_os_closure_payload = build_ui_research_os_closure_latest_payload(repo_root=root)
    research_os_attestation_payload = build_ui_research_os_attestation_latest_payload(repo_root=root)
    research_os_briefing_payload = build_ui_research_os_briefing_latest_payload(repo_root=root)
    research_os_export_payload = build_ui_research_os_export_latest_payload(repo_root=root)
    research_os_operator_run_payload = build_ui_research_os_operator_run_latest_payload(repo_root=root)
    research_os_evidence_catalog_payload = build_ui_research_os_evidence_catalog_latest_payload(repo_root=root)
    research_os_evidence_drift_payload = build_ui_research_os_evidence_drift_latest_payload(repo_root=root)
    research_os_policy_gate_payload = build_ui_research_os_policy_gate_latest_payload(repo_root=root)
    research_os_exception_payload = build_ui_research_os_exception_latest_payload(repo_root=root)
    research_os_remediation_payload = build_ui_research_os_remediation_latest_payload(repo_root=root)
    research_os_release_readiness_payload = build_ui_research_os_release_readiness_latest_payload(repo_root=root)
    research_os_handoff_payload = build_ui_research_os_handoff_latest_payload(repo_root=root)
    research_os_handoff_signoff_payload = build_ui_research_os_handoff_signoff_latest_payload(repo_root=root)
    research_os_review_journal_payload = build_ui_research_os_review_journal_latest_payload(repo_root=root)
    if strategy_memory_payload.get("degraded"):
        degraded.extend(str(x) for x in strategy_memory_payload["degraded"])
    if strategy_thesis_payload.get("degraded"):
        degraded.extend(str(x) for x in strategy_thesis_payload["degraded"])
    if strategy_thesis_generation_payload.get("degraded"):
        degraded.extend(str(x) for x in strategy_thesis_generation_payload["degraded"])
    if shadow_book_payload.get("degraded"):
        degraded.extend(str(x) for x in shadow_book_payload["degraded"])
    if research_os_closure_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_closure_payload["degraded"])
    if research_os_attestation_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_attestation_payload["degraded"])
    if research_os_briefing_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_briefing_payload["degraded"])
    if research_os_export_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_export_payload["degraded"])
    if research_os_operator_run_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_operator_run_payload["degraded"])
    if research_os_evidence_catalog_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_evidence_catalog_payload["degraded"])
    if research_os_evidence_drift_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_evidence_drift_payload["degraded"])
    if research_os_policy_gate_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_policy_gate_payload["degraded"])
    if research_os_exception_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_exception_payload["degraded"])
    if research_os_remediation_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_remediation_payload["degraded"])
    if research_os_release_readiness_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_release_readiness_payload["degraded"])
    if research_os_handoff_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_handoff_payload["degraded"])
    if research_os_handoff_signoff_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_handoff_signoff_payload["degraded"])
    if research_os_review_journal_payload.get("degraded"):
        degraded.extend(str(x) for x in research_os_review_journal_payload["degraded"])

    provider = _provider_ingestion_hint(repo_root=root)
    if provider.get("status") == "NO_ARTIFACTS":
        degraded.append("NO_PROVIDER_INGESTION_ARTIFACTS")

    demo = _demo_manifest_hint(repo_root=root)
    runtime_demo = _runtime_demo_manifest_hint(repo_root=root)
    oracle_cycle = _oracle_cycle_manifest_hint(repo_root=root)
    if demo.get("status") != "PRESENT" and runtime_demo.get("status") != "PRESENT":
        degraded.append("RESEARCH_OS_OPERATOR_MANIFEST_ABSENT")

    provider_hist_run = _provider_historical_snapshot_run_hint(repo_root=root)
    if provider_hist_run.get("status") == "NOT_PRESENT":
        degraded.append("NO_PROVIDER_HISTORICAL_SNAPSHOT_RUN_ARTIFACT")

    provider_paper_loop = _provider_paper_loop_manifest_hint(repo_root=root)
    if provider_paper_loop.get("status") == "NOT_PRESENT":
        degraded.append("NO_PROVIDER_PAPER_LOOP_ARTIFACT")

    paper_broker_art = _paper_broker_artifact_hint(repo_root=root)
    if paper_broker_art.get("status") == "NOT_PRESENT":
        degraded.append("NO_PAPER_BROKER_STATUS_ARTIFACT")

    cpcv = _cpcv_from_batch(batch_rec)
    if cpcv.get("status") in ("NO_BATCH", "NO_STRATEGIES", "NO_CPCV_FIELDS"):
        warnings.append(f"CPCV_HINT:{cpcv.get('status')}")

    alloc = batch_payload.get("portfolio_allocation")
    if alloc is None:
        degraded.append("NO_PORTFOLIO_ALLOCATION_ARTIFACT")
    elif isinstance(alloc, dict):
        gate = alloc.get("allocation_gate_status")
        if gate == "BLOCKED":
            warnings.append("PORTFOLIO_ALLOCATION_GATE_BLOCKED")

    if batch_payload.get("degraded"):
        degraded.extend(str(x) for x in batch_payload["degraded"])

    portfolio_corr = batch_rec.get("portfolio_correlation_summary") if batch_rec else None

    prov_loop_warns: list[str] = []
    if isinstance(provider_paper_loop.get("warnings"), list):
        prov_loop_warns.extend(str(x) for x in provider_paper_loop["warnings"] if x is not None)
    if isinstance(provider_paper_loop.get("blockers"), list):
        prov_loop_warns.extend(f"BLOCKER:{x}" for x in provider_paper_loop["blockers"] if x is not None)

    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "artifact_root_summary": {
            "artifact_root": str(art_base),
            "strategy_batch_scan_root": batch_payload.get("scan_root"),
            "paper_tracking_scan_root": paper_payload.get("scan_root"),
            "strategy_data_root": str(strategy_data_directory(repo_root)),
        },
        "runtime_demo_manifest": runtime_demo,
        "oracle_cycle_latest": oracle_cycle,
        "provider_historical_snapshot_latest": provider_hist_run,
        "provider_paper_loop_latest": provider_paper_loop,
        "paper_broker_status_latest": paper_broker_art,
        "provider_backed_gauntlet_latest": batch_payload.get("provider_backed_gauntlet"),
        "provider_loop_warnings": prov_loop_warns,
        "strategy_memory_latest": strategy_memory_payload,
        "strategy_thesis_latest": strategy_thesis_payload,
        "strategy_thesis_generation_latest": strategy_thesis_generation_payload,
        "shadow_book_latest": shadow_book_payload,
        "research_os_closure_latest": research_os_closure_payload,
        "research_os_attestation_latest": research_os_attestation_payload,
        "research_os_briefing_latest": research_os_briefing_payload,
        "research_os_export_latest": research_os_export_payload,
        "research_os_operator_run_latest": research_os_operator_run_payload,
        "research_os_evidence_catalog_latest": research_os_evidence_catalog_payload,
        "research_os_evidence_drift_latest": research_os_evidence_drift_payload,
        "research_os_policy_gate_latest": research_os_policy_gate_payload,
        "research_os_exception_latest": research_os_exception_payload,
        "research_os_remediation_latest": research_os_remediation_payload,
        "research_os_release_readiness_latest": research_os_release_readiness_payload,
        "research_os_handoff_latest": research_os_handoff_payload,
        "research_os_handoff_signoff_latest": research_os_handoff_signoff_payload,
        "research_os_review_journal_latest": research_os_review_journal_payload,
        "provider_loop_blockers": list(provider_paper_loop.get("blockers") or [])
        if isinstance(provider_paper_loop.get("blockers"), list)
        else [],
        "gauntlet_latest": {
            "degraded": list(batch_payload.get("degraded") or []),
            "summary_path": batch_payload.get("summary_path"),
            "batch_id": batch_rec.get("batch_id") if batch_rec else None,
            "run_id": batch_rec.get("run_id") if batch_rec else None,
            "strategy_count": batch_rec.get("strategy_count") if batch_rec else None,
            "passed_count": batch_rec.get("passed_count") if batch_rec else None,
            "paper_only_count": batch_rec.get("paper_only_count") if batch_rec else None,
            "blocked_count": batch_rec.get("blocked_count") if batch_rec else None,
            "failed_count": batch_rec.get("failed_count") if batch_rec else None,
            "ok": batch_rec.get("ok") if batch_rec else None,
            "top_candidate": batch_rec.get("top_candidate") if batch_rec else None,
            "portfolio_correlation_summary": portfolio_corr,
            "batch_warnings": batch_rec.get("warnings") if batch_rec else None,
        },
        "paper_tracking_latest": {
            "degraded": list(paper_payload.get("degraded") or []),
            "scan_root": paper_payload.get("scan_root"),
            "manifest_path": paper_payload.get("manifest_path"),
            "latest": paper_payload.get("latest"),
            "latest_daily_run": paper_payload.get("latest_daily_run"),
        },
        "lifecycle_latest": (
            {
                "state": (paper_payload.get("latest") or {}).get("lifecycle_state")
                if isinstance(paper_payload.get("latest"), dict)
                else None,
                "promotion_review_ready": (paper_payload.get("latest") or {}).get("promotion_review_ready")
                if isinstance(paper_payload.get("latest"), dict)
                else None,
                "assessment_artifact": (paper_payload.get("latest") or {}).get("lifecycle_assessment_artifact")
                if isinstance(paper_payload.get("latest"), dict)
                else None,
                "kill_rule_posture": (paper_payload.get("latest") or {}).get("lifecycle_kill_rule_posture")
                if isinstance(paper_payload.get("latest"), dict)
                else None,
                "lifecycle_blockers": (paper_payload.get("latest") or {}).get("lifecycle_blockers")
                if isinstance(paper_payload.get("latest"), dict)
                else None,
            }
        ),
        "promotion_packet_latest": (
            (paper_payload.get("latest") or {}).get("promotion_review_packet_summary")
            if isinstance(paper_payload.get("latest"), dict)
            else None
        ),
        "provider_ingestion_latest": provider,
        "paper_broker_status": broker_payload,
        "daily_tracking_latest": paper_payload.get("latest_daily_run"),
        "compute_status": compute_payload,
        "cpcv_latest": cpcv,
        "portfolio_allocation_latest": alloc if isinstance(alloc, dict) else None,
        "demo_manifest": demo,
        "warnings": warnings,
        "degraded": sorted(set(degraded)),
    }


__all__ = ["build_ui_research_os_status_payload", "_demo_manifest_hint", "_runtime_demo_manifest_hint"]
