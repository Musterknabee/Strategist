"""Research OS review journal operations.

Builds a durable local journal over already-produced Research OS review artifacts.
This module is offline/read-plane-only: no broker calls, no live trading, no
canonical ledger mutation, no deployment approval, and no profitability claims.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_review_journal import (
    ResearchOsReviewJournal,
    ResearchOsReviewJournalEntry,
    ResearchOsReviewJournalEntryType,
    ResearchOsReviewJournalStatus,
)

_SCHEMA = "ui_research_os_review_journal/v1"

_SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_API_SECRET",
    "ALPACA_SECRET_KEY",
    "POLYGON_API_KEY",
    "TIINGO_API_KEY",
    "TWELVE_DATA_API_KEY",
    "SECRET_KEY",
    "PRIVATE_KEY",
    "BEARER ",
)

_SOURCE_SPECS: tuple[tuple[str, ResearchOsReviewJournalEntryType, str], ...] = (
    ("research_os_handoff_signoff/latest/research_os_handoff_reviewer_signoff.json", ResearchOsReviewJournalEntryType.HANDOFF_SIGNOFF, "reviewer signoff"),
    ("research_os_handoff_signoff/latest/research_os_handoff_verification_result.json", ResearchOsReviewJournalEntryType.HANDOFF_SIGNOFF, "handoff verification"),
    ("research_os_handoff/latest/research_os_handoff_pack.json", ResearchOsReviewJournalEntryType.HANDOFF, "single-tenant handoff"),
    ("research_os_release_readiness/latest/research_os_release_readiness_report.json", ResearchOsReviewJournalEntryType.RELEASE_READINESS, "release-readiness review"),
    ("research_os_policy_gate/latest/research_os_policy_gate_report.json", ResearchOsReviewJournalEntryType.POLICY_GATE, "policy gate"),
    ("research_os_exceptions/latest/research_os_exception_record.json", ResearchOsReviewJournalEntryType.EXCEPTION, "governed exception"),
    ("research_os_remediation/latest/research_os_remediation_plan.json", ResearchOsReviewJournalEntryType.REMEDIATION, "remediation plan"),
    ("research_os_evidence_catalog/latest/research_os_evidence_catalog.json", ResearchOsReviewJournalEntryType.EVIDENCE_CATALOG, "evidence catalog"),
    ("research_os_drift/latest/research_os_drift_report.json", ResearchOsReviewJournalEntryType.EVIDENCE_DRIFT, "evidence drift"),
    ("research_os_operator_runs/latest/research_os_operator_run_manifest.json", ResearchOsReviewJournalEntryType.OPERATOR_RUN, "operator run"),
    ("research_os_exports/latest/research_os_export_manifest.json", ResearchOsReviewJournalEntryType.EXPORT, "export manifest"),
    ("research_os_briefings/latest/research_os_briefing_pack.json", ResearchOsReviewJournalEntryType.BRIEFING, "briefing pack"),
    ("research_os_closure/latest/research_os_closure_manifest.json", ResearchOsReviewJournalEntryType.CLOSURE, "closure manifest"),
    ("research_os_attestation/latest/operator_attestation.json", ResearchOsReviewJournalEntryType.ATTESTATION, "operator attestation"),
    ("research_os_attestation/latest/closure_verification_result.json", ResearchOsReviewJournalEntryType.ATTESTATION, "closure verification"),
)

_REQUIRED_LATEST = {
    "research_os_handoff_signoff/latest/research_os_handoff_reviewer_signoff.json": "NO_HANDOFF_REVIEWER_SIGNOFF",
    "research_os_handoff/latest/research_os_handoff_pack.json": "NO_HANDOFF_PACK",
    "research_os_release_readiness/latest/research_os_release_readiness_report.json": "NO_RELEASE_READINESS_REPORT",
    "research_os_policy_gate/latest/research_os_policy_gate_report.json": "NO_POLICY_GATE_REPORT",
    "research_os_remediation/latest/research_os_remediation_plan.json": "NO_REMEDIATION_PLAN",
}


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_review_journal_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_review_journal").resolve()


def research_os_review_journal_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_review_journal_root(repo_root, artifact_root) / "latest" / "research_os_review_journal.json").resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _contains_secret_marker(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size > 5_000_000:
            return False
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    upper = text.upper()
    return any(marker.upper() in upper for marker in _SECRET_MARKERS)


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _str(raw: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = raw.get(key)
        if value is not None:
            return str(value)
    return None


def _list(raw: dict[str, Any], key: str, limit: int = 40) -> list[str]:
    value = raw.get(key)
    if not isinstance(value, list):
        return []
    rows = [str(x) for x in value if x is not None]
    if len(rows) > limit:
        return rows[:limit] + [f"{key.upper()}_TRUNCATED:{len(rows)}"]
    return rows


def _entry_summary(label: str, raw: dict[str, Any]) -> str:
    status = _str(raw, "status", "verification_status", "policy_status") or "UNKNOWN"
    decision = _str(raw, "decision", "source_policy_gate_decision", "source_handoff_decision")
    if decision:
        return f"{label}: status={status}, decision={decision}"
    return f"{label}: status={status}"


def _entry_for_source(root: Path, rel: str, entry_type: ResearchOsReviewJournalEntryType, label: str) -> ResearchOsReviewJournalEntry | None:
    path = (root / rel).resolve()
    if not path.exists():
        return None
    raw = _read_json(path)
    warnings: list[str] = []
    blockers: list[str] = []
    if raw is None:
        blockers.append("UNREADABLE_JSON")
        raw = {}
    if _contains_secret_marker(path):
        blockers.append("SECRET_MARKER_PRESENT")
    warnings.extend(_list(raw, "warnings"))
    blockers.extend(_list(raw, "blockers"))
    for flag in ("read_plane_only", "no_live_trading", "no_broker_orders", "no_order_controls", "no_profitability_claim", "deployment_approval_unchanged"):
        if raw.get(flag) is False:
            blockers.append(f"{flag}=false")
    if raw.get("deployment_approved") is True:
        blockers.append("deployment_approved=true")
    sid = _str(
        raw,
        "signoff_id",
        "verification_id",
        "handoff_id",
        "report_id",
        "gate_id",
        "exception_id",
        "plan_id",
        "catalog_id",
        "drift_id",
        "run_id",
        "export_id",
        "briefing_id",
        "closure_id",
        "attestation_id",
    )
    return ResearchOsReviewJournalEntry(
        entry_id=f"{entry_type.value.lower()}:{sid or path.stem}",
        entry_type=entry_type,
        source_artifact_path=str(path),
        source_file_sha256=_sha256_file(path),
        source_manifest_sha256=_str(raw, "manifest_sha256", "result_sha256", "catalog_spine_sha256"),
        source_schema_version=_str(raw, "schema_version"),
        source_status=_str(raw, "status", "verification_status", "policy_status"),
        source_decision=_str(raw, "decision", "source_policy_gate_decision", "source_handoff_decision"),
        source_trust_banner=_str(raw, "trust_banner"),
        source_id_hint=sid,
        summary=_entry_summary(label, raw),
        warnings=sorted(set(warnings))[:60],
        blockers=sorted(set(blockers))[:60],
        metadata={
            "relative_path": _safe_rel(path, root),
            "label": label,
            "ok": raw.get("ok") if isinstance(raw.get("ok"), bool) else None,
            "release_review_ready": raw.get("release_review_ready"),
            "handoff_ready": raw.get("handoff_ready"),
            "deployment_approved": raw.get("deployment_approved"),
        },
    )


def _with_digest(journal: ResearchOsReviewJournal) -> ResearchOsReviewJournal:
    payload = journal.model_dump(mode="json", exclude={"journal_spine_sha256", "manifest_sha256"})
    spine = [
        {
            "entry_id": e.get("entry_id"),
            "entry_type": e.get("entry_type"),
            "source_manifest_sha256": e.get("source_manifest_sha256"),
            "source_file_sha256": e.get("source_file_sha256"),
            "source_status": e.get("source_status"),
            "source_decision": e.get("source_decision"),
        }
        for e in payload.get("entries", [])
    ]
    payload["journal_spine_sha256"] = _canonical_sha256(spine)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsReviewJournal.model_validate(payload)


def build_research_os_review_journal(
    *,
    journal_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> ResearchOsReviewJournal:
    root = _artifact_root(repo_root, artifact_root)
    entries: list[ResearchOsReviewJournalEntry] = []
    warnings: list[str] = []
    blockers: list[str] = []
    for rel, entry_type, label in _SOURCE_SPECS:
        entry = _entry_for_source(root, rel, entry_type, label)
        if entry is None:
            if rel in _REQUIRED_LATEST:
                warnings.append(_REQUIRED_LATEST[rel])
            continue
        entries.append(entry)
        warnings.extend(f"{entry.entry_type.value}:{w}" for w in entry.warnings)
        blockers.extend(f"{entry.entry_type.value}:{b}" for b in entry.blockers)
        if entry.source_status in {"BLOCKED", "FAILED", "TAMPERED", "MISSING"}:
            warnings.append(f"{entry.entry_type.value}:STATUS_{entry.source_status}")
        elif entry.source_status in {"RESTRICTED", "RESTRICTED_REVIEW", "STALE", "WARN", "WARNING", "DEGRADED"}:
            warnings.append(f"{entry.entry_type.value}:STATUS_{entry.source_status}")
        if entry.source_decision in {"BLOCKED", "REJECTED", "BLOCKED_BY_EVIDENCE", "REMEDIATION_REQUIRED"}:
            warnings.append(f"{entry.entry_type.value}:DECISION_{entry.source_decision}")
    entries.sort(key=lambda e: (e.recorded_at_utc, e.entry_type.value, e.entry_id))
    source_counts: dict[str, int] = {}
    latest_decision_summary: dict[str, Any] = {}
    for entry in entries:
        source_counts[entry.entry_type.value] = source_counts.get(entry.entry_type.value, 0) + 1
        if entry.source_decision or entry.source_status:
            latest_decision_summary[entry.entry_type.value] = {
                "status": entry.source_status,
                "decision": entry.source_decision,
                "trust_banner": entry.source_trust_banner,
                "source_id": entry.source_id_hint,
            }
    if not entries:
        status = ResearchOsReviewJournalStatus.EMPTY
        trust = ResearchOsTrustBanner.UNTRUSTED
        warnings.append("NO_REVIEW_JOURNAL_SOURCE_ARTIFACTS")
    elif blockers:
        status = ResearchOsReviewJournalStatus.BLOCKED
        trust = ResearchOsTrustBanner.UNTRUSTED
    elif warnings:
        status = ResearchOsReviewJournalStatus.RESTRICTED
        trust = ResearchOsTrustBanner.TRUST_RESTRICTED
    else:
        status = ResearchOsReviewJournalStatus.READY
        trust = ResearchOsTrustBanner.TRUSTED
    journal = ResearchOsReviewJournal(
        journal_id=journal_id,
        artifact_root=str(root),
        status=status,
        trust_banner=trust,
        entry_count=len(entries),
        source_counts=source_counts,
        latest_decision_summary=latest_decision_summary,
        entries=entries,
        warnings=sorted(set(warnings))[:200],
        blockers=sorted(set(blockers))[:200],
    )
    return _with_digest(journal)


def write_research_os_review_journal(
    journal: ResearchOsReviewJournal,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_review_journal_root(repo_root, artifact_root)
    jdir = root / "journals" / journal.journal_id
    path = jdir / "research_os_review_journal.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"review journal already exists: {path}")
    payload = journal.model_dump(mode="json")
    _write_json(path, payload)
    latest = root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, latest / "research_os_review_journal.json")
    _write_json(latest / "latest_ref.json", {"journal_id": journal.journal_id, "manifest_path": str(path), "manifest_sha256": journal.manifest_sha256})
    return path


def build_and_write_research_os_review_journal(
    *,
    journal_id: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> tuple[ResearchOsReviewJournal, Path]:
    journal = build_research_os_review_journal(journal_id=journal_id, repo_root=repo_root, artifact_root=artifact_root)
    path = write_research_os_review_journal(journal, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return journal, path


def load_latest_research_os_review_journal(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsReviewJournal | None:
    raw = _read_json(research_os_review_journal_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    try:
        return ResearchOsReviewJournal.model_validate(raw)
    except Exception:
        return None


def build_ui_research_os_review_journal_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    path = research_os_review_journal_latest_path(repo_root, artifact_root)
    journal = load_latest_research_os_review_journal(repo_root=repo_root, artifact_root=artifact_root)
    if journal is None:
        return {
            "schema_version": _SCHEMA,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "read_plane_only": True,
            "no_live_trading": True,
            "no_broker_orders": True,
            "no_order_controls": True,
            "status": "NOT_PRESENT",
            "manifest_path": str(path),
            "latest": None,
            "degraded": ["NO_RESEARCH_OS_REVIEW_JOURNAL"],
        }
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "status": "PRESENT",
        "manifest_path": str(path),
        "latest": journal.model_dump(mode="json"),
        "degraded": [] if journal.status == ResearchOsReviewJournalStatus.READY else [f"REVIEW_JOURNAL_{journal.status.value}"],
    }


__all__ = [
    "build_and_write_research_os_review_journal",
    "build_research_os_review_journal",
    "build_ui_research_os_review_journal_latest_payload",
    "load_latest_research_os_review_journal",
    "research_os_review_journal_latest_path",
    "research_os_review_journal_root",
    "write_research_os_review_journal",
]
