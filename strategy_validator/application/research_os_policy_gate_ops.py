"""Research OS policy gate builder.

The policy gate evaluates already-written Research OS evidence artifacts and
emits a digest-linked PASS/WARN/BLOCK/EMPTY report. It never calls providers or
brokers, never mutates the ledger, and never grants deployment/live-trading
authority.
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
from strategy_validator.contracts.research_os_policy_gate import (
    ResearchOsPolicyGateDecision,
    ResearchOsPolicyGateInputRef,
    ResearchOsPolicyGateReport,
    ResearchOsPolicyGateRuleResult,
    ResearchOsPolicyGateRuleStatus,
    ResearchOsPolicyGateSeverity,
)

_SCHEMA = "ui_research_os_policy_gate/v1"

_REQUIRED_INPUTS: tuple[tuple[str, str, str], ...] = (
    ("operator_run", "OPERATOR_RUN", "research_os_operator_runs/latest/research_os_operator_run_manifest.json"),
    ("evidence_catalog", "CATALOG", "research_os_evidence_catalog/latest/research_os_evidence_catalog.json"),
    ("closure_manifest", "CLOSURE", "research_os_closure/latest/research_os_closure_manifest.json"),
    ("closure_verification", "ATTESTATION", "research_os_attestation/latest/closure_verification_result.json"),
    ("operator_attestation", "ATTESTATION", "research_os_attestation/latest/operator_attestation.json"),
    ("briefing_pack", "BRIEFING", "research_os_briefings/latest/research_os_briefing_pack.json"),
    ("export_manifest", "EXPORT", "research_os_exports/latest/research_os_export_manifest.json"),
    ("evidence_drift", "DRIFT", "research_os_drift/latest/research_os_drift_report.json"),
)

_OPTIONAL_INPUTS: tuple[tuple[str, str, str], ...] = (
    ("export_verification", "EXPORT", "research_os_exports/latest/research_os_export_verification.json"),
    ("provider_paper_loop", "PROVIDER_LOOP", "provider_paper_loop/latest/provider_paper_loop_manifest.json"),
    ("provider_historical_snapshot", "PROVIDER_SNAPSHOT", "provider_historical_snapshots/latest/provider_historical_snapshot_run.json"),
    ("paper_broker_status", "PAPER_BROKER", "paper_broker/latest/paper_broker_status.json"),
    ("strategy_memory", "STRATEGY_MEMORY", "strategy_memory/latest/memory_index.json"),
    ("strategy_thesis", "STRATEGY_THESIS", "strategy_theses/latest/thesis_evaluation.json"),
    ("shadow_book", "SHADOW_BOOK", "shadow_books/latest/shadow_book_manifest.json"),
    ("shadow_book_risk", "SHADOW_BOOK", "shadow_books/latest/latest_risk_summary.json"),
)

_SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_SECRET_KEY",
    "ALPACA_API_SECRET",
    "BROKER_SECRET",
    "PRIVATE KEY",
    "BEGIN OPENSSH PRIVATE KEY",
    "BEGIN RSA PRIVATE KEY",
    "Bearer ",
)

_SAFETY_FLAGS = (
    "read_plane_only",
    "no_live_trading",
    "no_broker_orders",
    "no_order_controls",
    "no_profitability_claim",
    "deployment_approval_unchanged",
)

_BAD_STATUS_HINTS = {"BLOCKED", "FAILED", "TAMPERED", "MISSING", "REJECTED"}
_WARN_STATUS_HINTS = {
    "RESTRICTED",
    "DEGRADED",
    "WARNING",
    "WARN",
    "PENDING_KEY",
    "TRUST_RESTRICTED",
    "ACCEPTED_WITH_RESTRICTIONS",
    "STALE",
}


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_policy_gate_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_policy_gate").resolve()


def research_os_policy_gate_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_policy_gate_root(repo_root, artifact_root) / "latest" / "research_os_policy_gate_report.json").resolve()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _contains_secret_marker(path: Path) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:1_000_000]
    except OSError:
        return []
    return [f"SECRET_MARKER_PRESENT:{marker.strip()}" for marker in _SECRET_MARKERS if marker in text]


def _status_hint(raw: dict[str, Any]) -> str | None:
    for key in ("status", "policy_status", "decision", "verification_status"):
        value = raw.get(key)
        if value:
            return str(value)
    return None


def _count_list(raw: dict[str, Any], key: str) -> int:
    value = raw.get(key)
    return len(value) if isinstance(value, list) else 0


def _limited_list(raw: dict[str, Any], key: str, limit: int = 16) -> list[str]:
    value = raw.get(key)
    if not isinstance(value, list):
        return []
    rows = [str(x) for x in value[:limit] if x is not None]
    if len(value) > limit:
        rows.append(f"{key.upper()}_TRUNCATED:{len(value)}")
    return rows


def _input_ref(root: Path, input_id: str, category: str, rel_path: str, *, required: bool) -> ResearchOsPolicyGateInputRef:
    path = (root / rel_path).resolve()
    warnings: list[str] = []
    blockers: list[str] = []
    if not path.is_file():
        if required:
            blockers.append(f"MISSING_REQUIRED_INPUT:{input_id}")
        return ResearchOsPolicyGateInputRef(input_id=input_id, category=category, artifact_path=str(path), exists=False, readable=False, warnings=warnings, blockers=blockers)
    raw = _read_json(path)
    if raw is None:
        blockers.append(f"UNREADABLE_INPUT:{input_id}")
        return ResearchOsPolicyGateInputRef(input_id=input_id, category=category, artifact_path=str(path), exists=True, readable=False, file_sha256=_sha256_file(path), warnings=warnings, blockers=blockers)

    status = _status_hint(raw)
    trust = raw.get("trust_banner")
    decision = raw.get("decision")
    verification = raw.get("verification_status") or raw.get("status") if input_id == "closure_verification" else raw.get("verification_status")
    safety = {flag: raw.get(flag) if isinstance(raw.get(flag), bool) else None for flag in _SAFETY_FLAGS}
    warnings.extend(_limited_list(raw, "warnings"))
    blockers.extend(_limited_list(raw, "blockers"))
    warnings.extend(_contains_secret_marker(path))
    if any(w.startswith("SECRET_MARKER_PRESENT") for w in warnings):
        blockers.extend(w for w in warnings if w.startswith("SECRET_MARKER_PRESENT"))
    for flag, value in safety.items():
        if value is False:
            blockers.append(f"SAFETY_FLAG_FALSE:{input_id}:{flag}")
    if status in _BAD_STATUS_HINTS or decision in {"BLOCKED", "REJECTED"} or verification in {"TAMPERED", "MISSING", "BLOCKED"}:
        blockers.append(f"BLOCKING_STATUS:{input_id}:{status or decision or verification}")
    elif status in _WARN_STATUS_HINTS or str(trust or "") == "TRUST_RESTRICTED" or decision == "ACCEPTED_WITH_RESTRICTIONS":
        warnings.append(f"RESTRICTED_STATUS:{input_id}:{status or decision or trust}")

    return ResearchOsPolicyGateInputRef(
        input_id=input_id,
        category=category,
        artifact_path=str(path),
        exists=True,
        readable=True,
        file_sha256=_sha256_file(path),
        schema_version_observed=str(raw.get("schema_version")) if raw.get("schema_version") else None,
        status_hint=str(status) if status else None,
        trust_banner_hint=str(trust) if trust else None,
        decision_hint=str(decision) if decision else None,
        verification_status_hint=str(verification) if verification else None,
        ok_hint=raw.get("ok") if isinstance(raw.get("ok"), bool) else None,
        warnings_count=_count_list(raw, "warnings"),
        blockers_count=_count_list(raw, "blockers"),
        safety_flags=safety,
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
    )


def _rule(rule_id: str, title: str, status: ResearchOsPolicyGateRuleStatus, severity: ResearchOsPolicyGateSeverity, message: str, refs: list[str] | None = None, metadata: dict[str, Any] | None = None) -> ResearchOsPolicyGateRuleResult:
    return ResearchOsPolicyGateRuleResult(rule_id=rule_id, title=title, status=status, severity=severity, message=message, evidence_refs=refs or [], metadata=metadata or {})


def _build_rules(inputs: list[ResearchOsPolicyGateInputRef]) -> list[ResearchOsPolicyGateRuleResult]:
    by_id = {i.input_id: i for i in inputs}
    rules: list[ResearchOsPolicyGateRuleResult] = []
    required_missing = [i.input_id for i in inputs if i.input_id in {x[0] for x in _REQUIRED_INPUTS} and not i.exists]
    rules.append(_rule(
        "required_evidence_present",
        "Required evidence artifacts are present",
        ResearchOsPolicyGateRuleStatus.BLOCK if required_missing else ResearchOsPolicyGateRuleStatus.PASS,
        ResearchOsPolicyGateSeverity.BLOCKER if required_missing else ResearchOsPolicyGateSeverity.INFO,
        "Required Research OS evidence inputs must exist before operator review can pass.",
        required_missing,
        {"missing_required": required_missing},
    ))
    false_flags: list[str] = []
    for i in inputs:
        for flag, value in i.safety_flags.items():
            if value is False:
                false_flags.append(f"{i.input_id}:{flag}")
    rules.append(_rule(
        "safety_flags_preserved",
        "Safety flags preserve paper-only/read-plane posture",
        ResearchOsPolicyGateRuleStatus.BLOCK if false_flags else ResearchOsPolicyGateRuleStatus.PASS,
        ResearchOsPolicyGateSeverity.BLOCKER if false_flags else ResearchOsPolicyGateSeverity.INFO,
        "Live trading, broker orders, browser order controls, profitability claims, and deployment approval changes must remain disabled.",
        false_flags,
    ))
    input_blockers = [f"{i.input_id}:{b}" for i in inputs for b in i.blockers]
    rules.append(_rule(
        "no_input_blockers",
        "No evidence input carries blockers",
        ResearchOsPolicyGateRuleStatus.BLOCK if input_blockers else ResearchOsPolicyGateRuleStatus.PASS,
        ResearchOsPolicyGateSeverity.BLOCKER if input_blockers else ResearchOsPolicyGateSeverity.INFO,
        "Any evidence blocker forces the policy gate to BLOCK.",
        input_blockers[:32],
        {"blocker_count": len(input_blockers)},
    ))
    restricted = [i.input_id for i in inputs if i.status_hint in _WARN_STATUS_HINTS or i.trust_banner_hint == "TRUST_RESTRICTED" or i.decision_hint == "ACCEPTED_WITH_RESTRICTIONS" or i.warnings]
    rules.append(_rule(
        "restricted_evidence_review",
        "Restricted evidence requires operator caution",
        ResearchOsPolicyGateRuleStatus.WARN if restricted else ResearchOsPolicyGateRuleStatus.PASS,
        ResearchOsPolicyGateSeverity.WARNING if restricted else ResearchOsPolicyGateSeverity.INFO,
        "Restricted, degraded, or warning-bearing evidence can be reviewed, but cannot be treated as deployment approval.",
        restricted,
        {"restricted_input_count": len(restricted)},
    ))
    att = by_id.get("operator_attestation")
    att_ok = att is not None and att.exists and att.readable and att.decision_hint in {"ACKNOWLEDGED", "ACCEPTED_WITH_RESTRICTIONS"}
    rules.append(_rule(
        "operator_attestation_present",
        "Operator attestation is present and non-rejected",
        ResearchOsPolicyGateRuleStatus.PASS if att_ok else ResearchOsPolicyGateRuleStatus.BLOCK,
        ResearchOsPolicyGateSeverity.INFO if att_ok else ResearchOsPolicyGateSeverity.BLOCKER,
        "Operator attestation must exist and must not be BLOCKED or REJECTED.",
        [] if att_ok else ["operator_attestation"],
        {"decision": att.decision_hint if att else None},
    ))
    drift = by_id.get("evidence_drift")
    drift_changed = False
    if drift and drift.exists and drift.readable:
        raw = _read_json(Path(drift.artifact_path)) or {}
        drift_changed = any(int(raw.get(k) or 0) > 0 for k in ("added_count", "removed_count", "changed_count"))
    rules.append(_rule(
        "drift_reviewed",
        "Evidence drift is visible to operator",
        ResearchOsPolicyGateRuleStatus.WARN if drift_changed else ResearchOsPolicyGateRuleStatus.PASS,
        ResearchOsPolicyGateSeverity.WARNING if drift_changed else ResearchOsPolicyGateSeverity.INFO,
        "Catalog drift is not automatically bad, but changed evidence should be reviewed before relying on the briefing/export.",
        ["evidence_drift"] if drift_changed else [],
    ))
    return rules


def _with_digest(report: ResearchOsPolicyGateReport) -> ResearchOsPolicyGateReport:
    payload = report.model_dump(mode="json", exclude={"manifest_sha256", "gate_spine_sha256"})
    spine_rows = [
        {
            "input_id": i["input_id"],
            "file_sha256": i.get("file_sha256"),
            "status_hint": i.get("status_hint"),
            "decision_hint": i.get("decision_hint"),
            "verification_status_hint": i.get("verification_status_hint"),
        }
        for i in payload.get("inputs", [])
    ] + [
        {"rule_id": r["rule_id"], "status": r["status"], "severity": r["severity"]}
        for r in payload.get("rules", [])
    ]
    payload["gate_spine_sha256"] = _canonical_sha256(spine_rows)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsPolicyGateReport.model_validate(payload)


def build_research_os_policy_gate_report(*, gate_id: str, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsPolicyGateReport:
    root = _artifact_root(repo_root, artifact_root)
    inputs = [_input_ref(root, input_id, category, rel, required=True) for input_id, category, rel in _REQUIRED_INPUTS]
    inputs.extend(_input_ref(root, input_id, category, rel, required=False) for input_id, category, rel in _OPTIONAL_INPUTS)
    rules = _build_rules(inputs)
    warnings = sorted(set(f"{i.input_id}:{w}" for i in inputs for w in i.warnings))
    blockers = sorted(set(f"{i.input_id}:{b}" for i in inputs for b in i.blockers))
    for r in rules:
        if r.status == ResearchOsPolicyGateRuleStatus.WARN:
            warnings.append(f"RULE_WARN:{r.rule_id}")
        elif r.status == ResearchOsPolicyGateRuleStatus.BLOCK:
            blockers.append(f"RULE_BLOCK:{r.rule_id}")
    present_required = sum(1 for i in inputs if i.input_id in {x[0] for x in _REQUIRED_INPUTS} and i.exists and i.readable)
    if present_required == 0:
        decision = ResearchOsPolicyGateDecision.EMPTY
        banner = ResearchOsTrustBanner.UNTRUSTED
    elif blockers:
        decision = ResearchOsPolicyGateDecision.BLOCK
        banner = ResearchOsTrustBanner.UNTRUSTED
    elif warnings:
        decision = ResearchOsPolicyGateDecision.WARN
        banner = ResearchOsTrustBanner.TRUST_RESTRICTED
    else:
        decision = ResearchOsPolicyGateDecision.PASS
        banner = ResearchOsTrustBanner.TRUSTED
    actions: list[str] = []
    if decision == ResearchOsPolicyGateDecision.EMPTY:
        actions.append("Run strategy-validator-research-os-run run --overwrite --json before policy review.")
    if any("MISSING_REQUIRED_INPUT" in b for b in blockers):
        actions.append("Produce missing required Research OS evidence artifacts, then rebuild the policy gate.")
    if any("SAFETY_FLAG_FALSE" in b for b in blockers):
        actions.append("Investigate unsafe evidence flags before relying on this run.")
    if decision == ResearchOsPolicyGateDecision.WARN:
        actions.append("Review restricted/degraded evidence and document operator rationale; do not treat WARN as deployment approval.")
    if not actions and decision == ResearchOsPolicyGateDecision.PASS:
        actions.append("Evidence posture is internally consistent for paper-only operator review; deployment approval still requires separate evidence.")

    report = ResearchOsPolicyGateReport(
        gate_id=gate_id,
        artifact_root=str(root),
        decision=decision,
        trust_banner=banner,
        required_input_count=len(_REQUIRED_INPUTS),
        present_input_count=present_required,
        warning_count=len(set(warnings)),
        blocker_count=len(set(blockers)),
        inputs=inputs,
        rules=rules,
        warnings=sorted(set(warnings))[:240] + ([f"POLICY_GATE_WARNINGS_TRUNCATED:{len(set(warnings))}"] if len(set(warnings)) > 240 else []),
        blockers=sorted(set(blockers))[:240] + ([f"POLICY_GATE_BLOCKERS_TRUNCATED:{len(set(blockers))}"] if len(set(blockers)) > 240 else []),
        recommended_operator_actions=actions,
    )
    return _with_digest(report)


def write_research_os_policy_gate_report(report: ResearchOsPolicyGateReport, *, repo_root: Path | None = None, artifact_root: Path | None = None, overwrite: bool = False) -> Path:
    root = research_os_policy_gate_root(repo_root, artifact_root)
    gdir = root / "gates" / report.gate_id
    path = gdir / "research_os_policy_gate_report.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"policy gate report already exists: {path}")
    payload = report.model_dump(mode="json")
    _write_json(path, payload)
    latest = root / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, latest / "research_os_policy_gate_report.json")
    _write_json(latest / "latest_ref.json", {"gate_id": report.gate_id, "manifest_path": str(path), "manifest_sha256": report.manifest_sha256})
    return path


def build_and_write_research_os_policy_gate_report(*, gate_id: str, repo_root: Path | None = None, artifact_root: Path | None = None, overwrite: bool = False) -> tuple[ResearchOsPolicyGateReport, Path]:
    report = build_research_os_policy_gate_report(gate_id=gate_id, repo_root=repo_root, artifact_root=artifact_root)
    path = write_research_os_policy_gate_report(report, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return report, path


def load_latest_research_os_policy_gate_report(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsPolicyGateReport | None:
    raw = _read_json(research_os_policy_gate_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    return ResearchOsPolicyGateReport.model_validate(raw)


def build_ui_research_os_policy_gate_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    path = research_os_policy_gate_latest_path(repo_root, artifact_root)
    report = load_latest_research_os_policy_gate_report(repo_root=repo_root, artifact_root=artifact_root)
    if report is None:
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
            "degraded": ["NO_RESEARCH_OS_POLICY_GATE_REPORT"],
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
        "latest": report.model_dump(mode="json"),
        "degraded": [] if report.decision == ResearchOsPolicyGateDecision.PASS else [f"POLICY_GATE_{report.decision.value}"],
    }


__all__ = [
    "build_and_write_research_os_policy_gate_report",
    "build_research_os_policy_gate_report",
    "build_ui_research_os_policy_gate_latest_payload",
    "load_latest_research_os_policy_gate_report",
    "research_os_policy_gate_latest_path",
    "research_os_policy_gate_root",
    "write_research_os_policy_gate_report",
]
