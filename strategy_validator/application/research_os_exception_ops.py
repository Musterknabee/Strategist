"""Research OS governed exception builder.

This module turns the latest policy-gate posture into a time-bounded exception
record when appropriate. It is intentionally conservative: WARN can be granted
with restrictions; PASS does not need an exception; BLOCK/EMPTY cannot be
bypassed by this artifact.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.application.research_os_policy_gate_ops import research_os_policy_gate_latest_path
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_exception import (
    ResearchOsExceptionDecision,
    ResearchOsExceptionRecord,
    ResearchOsExceptionScope,
    ResearchOsExceptionStatus,
)

_SCHEMA = "ui_research_os_exception/v1"

_DEFAULT_CONSTRAINTS = (
    "No live trading authority is granted.",
    "No broker orders may be submitted.",
    "No browser order controls may be added or used.",
    "No profitability or deployment-readiness claim may be made from this exception.",
    "Operator must review the source policy gate before relying on this exception.",
)


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_exception_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_exceptions").resolve()


def research_os_exception_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_exception_root(repo_root, artifact_root) / "latest" / "research_os_exception_record.json").resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")).hexdigest()


def _parse_expires_at(expires_at_utc: str | None, ttl_hours: int | None) -> datetime:
    if expires_at_utc:
        text = expires_at_utc.strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        value = datetime.fromisoformat(text)
        if value.tzinfo is None:
            raise ValueError("expires_at_utc must include a timezone")
        return value
    hours = ttl_hours if ttl_hours is not None else 24
    if hours <= 0:
        raise ValueError("ttl_hours must be positive")
    if hours > 24 * 30:
        raise ValueError("ttl_hours may not exceed 720 hours / 30 days")
    return datetime.now(timezone.utc) + timedelta(hours=hours)


def _infer_scopes(warnings: list[str], blockers: list[str]) -> list[ResearchOsExceptionScope]:
    joined = "\n".join(warnings + blockers).upper()
    scopes: set[ResearchOsExceptionScope] = {ResearchOsExceptionScope.OPERATOR_ACKNOWLEDGEMENT}
    if "PENDING_KEY" in joined or "PROVIDER" in joined:
        scopes.add(ResearchOsExceptionScope.PENDING_PROVIDER_KEY)
    if "BROKER" in joined:
        scopes.add(ResearchOsExceptionScope.PENDING_BROKER_KEY)
    if "MISSING" in joined or "OPTIONAL" in joined:
        scopes.add(ResearchOsExceptionScope.MISSING_OPTIONAL_EVIDENCE)
    if "DRIFT" in joined or "CHANGED" in joined:
        scopes.add(ResearchOsExceptionScope.EVIDENCE_DRIFT_REVIEW)
    if "RESTRICTED" in joined or "TRUST_RESTRICTED" in joined:
        scopes.add(ResearchOsExceptionScope.RESTRICTED_TRUST)
    if warnings:
        scopes.add(ResearchOsExceptionScope.POLICY_GATE_WARN)
    if not scopes:
        scopes.add(ResearchOsExceptionScope.OTHER)
    return sorted(scopes, key=lambda x: x.value)


def _with_digests(record: ResearchOsExceptionRecord) -> ResearchOsExceptionRecord:
    payload = record.model_dump(mode="json", exclude={"exception_spine_sha256", "manifest_sha256"})
    spine = {
        "exception_id": payload.get("exception_id"),
        "expires_at_utc": payload.get("expires_at_utc"),
        "source_policy_gate_id": payload.get("source_policy_gate_id"),
        "source_policy_gate_sha256": payload.get("source_policy_gate_sha256"),
        "status": payload.get("status"),
        "decision": payload.get("decision"),
        "scopes": payload.get("scopes"),
        "covered_warnings": payload.get("covered_warnings"),
        "covered_blockers": payload.get("covered_blockers"),
        "residual_blockers": payload.get("residual_blockers"),
        "constraints": payload.get("constraints"),
    }
    payload["exception_spine_sha256"] = _canonical_sha256(spine)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsExceptionRecord.model_validate(payload)


def build_research_os_exception_record(
    *,
    exception_id: str,
    operator_id: str,
    rationale: str,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    expires_at_utc: str | None = None,
    ttl_hours: int | None = 24,
    constraints: list[str] | None = None,
    covered_warnings: list[str] | None = None,
) -> ResearchOsExceptionRecord:
    root = _artifact_root(repo_root, artifact_root)
    gate_path = research_os_policy_gate_latest_path(repo_root=repo_root, artifact_root=root)
    gate = _read_json(gate_path)
    expires = _parse_expires_at(expires_at_utc, ttl_hours)
    now = datetime.now(timezone.utc)
    all_constraints = list(_DEFAULT_CONSTRAINTS)
    if constraints:
        all_constraints.extend(c for c in constraints if c)

    if gate is None:
        record = ResearchOsExceptionRecord(
            exception_id=exception_id,
            operator_id=operator_id,
            rationale=rationale,
            expires_at_utc=expires,
            status=ResearchOsExceptionStatus.REJECTED,
            decision=ResearchOsExceptionDecision.REJECTED_EMPTY_GATE,
            trust_banner=ResearchOsTrustBanner.UNTRUSTED,
            residual_blockers=["NO_RESEARCH_OS_POLICY_GATE_REPORT"],
            constraints=all_constraints,
            recommended_followups=["Build a Research OS policy gate before requesting an exception."],
        )
        return _with_digests(record)

    decision = str(gate.get("decision") or "")
    warnings = [str(x) for x in (gate.get("warnings") or []) if x is not None]
    blockers = [str(x) for x in (gate.get("blockers") or []) if x is not None]
    requested_cover = covered_warnings or []
    covered = requested_cover if requested_cover else warnings[:80]
    covered_set = set(covered)
    residual_warnings = [w for w in warnings if w not in covered_set]

    if decision == "PASS":
        status = ResearchOsExceptionStatus.NOT_APPLICABLE
        ex_decision = ResearchOsExceptionDecision.NOT_NEEDED_FOR_PASS
        banner = ResearchOsTrustBanner.TRUSTED
        covered = []
        residual_warnings = warnings
        residual_blockers = []
        followups = ["No exception is needed while the policy gate is PASS."]
    elif decision == "WARN" and expires > now:
        status = ResearchOsExceptionStatus.ACTIVE
        ex_decision = ResearchOsExceptionDecision.GRANTED_WITH_RESTRICTIONS
        banner = ResearchOsTrustBanner.TRUST_RESTRICTED
        residual_blockers = []
        followups = [
            "Resolve or re-run the restricted evidence before this exception expires.",
            "Rebuild the policy gate after missing/provider artifacts are restored.",
        ]
    elif decision == "WARN":
        status = ResearchOsExceptionStatus.EXPIRED
        ex_decision = ResearchOsExceptionDecision.GRANTED_WITH_RESTRICTIONS
        banner = ResearchOsTrustBanner.UNTRUSTED
        residual_blockers = ["EXCEPTION_EXPIRED_AT_CREATION"]
        followups = ["Request a new unexpired exception if restricted evidence still needs review."]
    elif decision == "EMPTY":
        status = ResearchOsExceptionStatus.REJECTED
        ex_decision = ResearchOsExceptionDecision.REJECTED_EMPTY_GATE
        banner = ResearchOsTrustBanner.UNTRUSTED
        residual_blockers = blockers or ["EMPTY_POLICY_GATE_CANNOT_BE_EXCEPTED"]
        followups = ["Run the Research OS operator pipeline before exception review."]
    else:
        status = ResearchOsExceptionStatus.REJECTED
        ex_decision = ResearchOsExceptionDecision.REJECTED_POLICY_BLOCK
        banner = ResearchOsTrustBanner.UNTRUSTED
        residual_blockers = blockers or [f"POLICY_GATE_DECISION_NOT_EXCEPTABLE:{decision}"]
        followups = ["Resolve BLOCK-level evidence before requesting a new exception."]

    record = ResearchOsExceptionRecord(
        exception_id=exception_id,
        operator_id=operator_id,
        rationale=rationale,
        expires_at_utc=expires,
        source_policy_gate_id=str(gate.get("gate_id")) if gate.get("gate_id") else None,
        source_policy_gate_decision=decision or None,
        source_policy_gate_sha256=str(gate.get("manifest_sha256") or _sha256_file(gate_path) or ""),
        status=status,
        decision=ex_decision,
        trust_banner=banner,
        scopes=_infer_scopes(warnings, blockers),
        covered_warnings=covered,
        covered_blockers=[],
        residual_warnings=residual_warnings[:120],
        residual_blockers=residual_blockers[:120],
        constraints=all_constraints,
        recommended_followups=followups,
    )
    return _with_digests(record)


def write_research_os_exception_record(record: ResearchOsExceptionRecord, *, repo_root: Path | None = None, artifact_root: Path | None = None, overwrite: bool = False) -> Path:
    eroot = research_os_exception_root(repo_root=repo_root, artifact_root=artifact_root)
    path = eroot / "exceptions" / record.exception_id / "research_os_exception_record.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"exception record already exists: {path}")
    payload = record.model_dump(mode="json")
    _write_json(path, payload)
    latest = eroot / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, latest / "research_os_exception_record.json")
    _write_json(latest / "latest_ref.json", {"exception_id": record.exception_id, "manifest_path": str(path), "manifest_sha256": record.manifest_sha256})
    return path


def build_and_write_research_os_exception_record(**kwargs: Any) -> tuple[ResearchOsExceptionRecord, Path]:
    overwrite = bool(kwargs.pop("overwrite", False))
    repo_root = kwargs.get("repo_root")
    artifact_root = kwargs.get("artifact_root")
    record = build_research_os_exception_record(**kwargs)
    path = write_research_os_exception_record(record, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return record, path


def load_latest_research_os_exception_record(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsExceptionRecord | None:
    raw = _read_json(research_os_exception_latest_path(repo_root=repo_root, artifact_root=artifact_root))
    if raw is None:
        return None
    record = ResearchOsExceptionRecord.model_validate(raw)
    if record.status == ResearchOsExceptionStatus.ACTIVE and record.expires_at_utc and record.expires_at_utc <= datetime.now(timezone.utc):
        payload = record.model_dump(mode="json")
        payload["status"] = ResearchOsExceptionStatus.EXPIRED.value
        payload["trust_banner"] = ResearchOsTrustBanner.UNTRUSTED.value
        payload["residual_blockers"] = sorted(set(payload.get("residual_blockers") or []) | {"EXCEPTION_EXPIRED"})
        return _with_digests(ResearchOsExceptionRecord.model_validate(payload))
    return record


def build_ui_research_os_exception_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    path = research_os_exception_latest_path(repo_root=repo_root, artifact_root=artifact_root)
    record = load_latest_research_os_exception_record(repo_root=repo_root, artifact_root=artifact_root)
    if record is None:
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
            "degraded": ["NO_RESEARCH_OS_EXCEPTION_RECORD"],
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
        "latest": record.model_dump(mode="json"),
        "degraded": [] if record.status == ResearchOsExceptionStatus.ACTIVE else [f"RESEARCH_OS_EXCEPTION_{record.status.value}"],
    }


__all__ = [
    "build_and_write_research_os_exception_record",
    "build_research_os_exception_record",
    "build_ui_research_os_exception_latest_payload",
    "load_latest_research_os_exception_record",
    "research_os_exception_latest_path",
    "research_os_exception_root",
    "write_research_os_exception_record",
]
