"""Research OS release-readiness review builder.

This module consumes existing offline/read-plane Research OS artifacts and emits a
machine-readable readiness-for-review report. It does not execute research,
call providers, call brokers, mutate ledgers, approve deployment, or claim
profitability.
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
from strategy_validator.contracts.research_os_release_readiness import (
    ResearchOsReleaseReadinessCriterion,
    ResearchOsReleaseReadinessCriterionStatus,
    ResearchOsReleaseReadinessDecision,
    ResearchOsReleaseReadinessReport,
    ResearchOsReleaseReadinessStatus,
)

_SCHEMA = "ui_research_os_release_readiness/v1"


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_release_readiness_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_release_readiness").resolve()


def research_os_release_readiness_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_release_readiness_root(repo_root, artifact_root) / "latest" / "research_os_release_readiness_report.json").resolve()


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


def _list(raw: dict[str, Any] | None, key: str, limit: int = 80) -> list[str]:
    value = raw.get(key) if isinstance(raw, dict) else []
    if not isinstance(value, list):
        return []
    rows = [str(x) for x in value if x is not None]
    if len(rows) > limit:
        return rows[:limit] + [f"{key.upper()}_TRUNCATED:{len(rows)}"]
    return rows


def _latest_inputs(root: Path) -> dict[str, tuple[Path, dict[str, Any] | None]]:
    rels = {
        "policy_gate": "research_os_policy_gate/latest/research_os_policy_gate_report.json",
        "exception": "research_os_exceptions/latest/research_os_exception_record.json",
        "remediation": "research_os_remediation/latest/research_os_remediation_plan.json",
        "operator_run": "research_os_operator_runs/latest/research_os_operator_run_manifest.json",
        "catalog": "research_os_evidence_catalog/latest/research_os_evidence_catalog.json",
        "drift": "research_os_drift/latest/research_os_drift_report.json",
        "closure": "research_os_closure/latest/research_os_closure_manifest.json",
        "attestation": "research_os_attestation/latest/operator_attestation.json",
        "briefing": "research_os_briefings/latest/research_os_briefing_pack.json",
        "export": "research_os_exports/latest/research_os_export_manifest.json",
    }
    return {name: (root / rel, _read_json(root / rel)) for name, rel in rels.items()}


def _criterion(
    criterion_id: str,
    title: str,
    status: ResearchOsReleaseReadinessCriterionStatus,
    *,
    source: str,
    evidence_refs: list[str] | None = None,
    warnings: list[str] | None = None,
    blockers: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ResearchOsReleaseReadinessCriterion:
    return ResearchOsReleaseReadinessCriterion(
        criterion_id=criterion_id,
        title=title,
        status=status,
        source=source,
        evidence_refs=evidence_refs or [],
        warnings=warnings or [],
        blockers=blockers or [],
        metadata=metadata or {},
    )


def _safety_criterion(raws: dict[str, tuple[Path, dict[str, Any] | None]]) -> ResearchOsReleaseReadinessCriterion:
    blockers: list[str] = []
    warnings: list[str] = []
    for name, (path, raw) in raws.items():
        if raw is None:
            continue
        for flag in ("no_live_trading", "no_broker_orders", "no_order_controls", "no_profitability_claim", "deployment_approval_unchanged"):
            if raw.get(flag) is False:
                blockers.append(f"{name}:{flag}=false")
        if raw.get("deployment_approved") is True:
            blockers.append(f"{name}:deployment_approved=true")
        if raw.get("read_plane_only") is False:
            blockers.append(f"{name}:read_plane_only=false")
    status = ResearchOsReleaseReadinessCriterionStatus.FAIL if blockers else ResearchOsReleaseReadinessCriterionStatus.PASS
    if not blockers:
        warnings.append("RELEASE_READINESS_DOES_NOT_APPROVE_DEPLOYMENT")
    refs = [str(path) for path, raw in raws.values() if raw is not None]
    return _criterion(
        "safety_flags",
        "Safety flags remain paper-only/read-plane-only and deployment approval is unchanged",
        status,
        source="release_readiness",
        evidence_refs=refs,
        warnings=warnings,
        blockers=blockers,
    )


def _with_digests(report: ResearchOsReleaseReadinessReport) -> ResearchOsReleaseReadinessReport:
    payload = report.model_dump(mode="json", exclude={"release_readiness_spine_sha256", "manifest_sha256"})
    spine = {
        "report_id": payload.get("report_id"),
        "status": payload.get("status"),
        "decision": payload.get("decision"),
        "source_policy_gate_id": payload.get("source_policy_gate_id"),
        "source_exception_id": payload.get("source_exception_id"),
        "source_remediation_plan_id": payload.get("source_remediation_plan_id"),
        "source_operator_run_id": payload.get("source_operator_run_id"),
        "criteria": [
            {
                "criterion_id": c.get("criterion_id"),
                "status": c.get("status"),
                "source": c.get("source"),
                "blockers": c.get("blockers", []),
                "warnings": c.get("warnings", []),
            }
            for c in payload.get("criteria", [])
        ],
        "p0_open_count": payload.get("p0_open_count"),
        "p1_open_count": payload.get("p1_open_count"),
        "open_remediation_count": payload.get("open_remediation_count"),
    }
    payload["release_readiness_spine_sha256"] = _canonical_sha256(spine)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsReleaseReadinessReport.model_validate(payload)


def build_research_os_release_readiness_report(
    *,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    report_id: str = "research-os-release-readiness",
) -> ResearchOsReleaseReadinessReport:
    root = _artifact_root(repo_root, artifact_root)
    inputs = _latest_inputs(root)
    policy = inputs["policy_gate"][1]
    exception = inputs["exception"][1]
    remediation = inputs["remediation"][1]
    operator_run = inputs["operator_run"][1]
    catalog = inputs["catalog"][1]
    drift = inputs["drift"][1]

    criteria: list[ResearchOsReleaseReadinessCriterion] = []
    warnings: list[str] = []
    blockers: list[str] = []
    followups: list[str] = []

    missing_required = [name for name in ("policy_gate", "remediation", "operator_run", "catalog") if inputs[name][1] is None]
    if missing_required:
        blockers.extend(f"MISSING_RELEASE_REVIEW_INPUT:{name}" for name in missing_required)
        criteria.append(_criterion(
            "required_inputs",
            "Required Research OS review inputs are present",
            ResearchOsReleaseReadinessCriterionStatus.FAIL,
            source="release_readiness",
            evidence_refs=[str(inputs[name][0]) for name in missing_required],
            blockers=[f"MISSING:{name}" for name in missing_required],
        ))
    else:
        criteria.append(_criterion(
            "required_inputs",
            "Required Research OS review inputs are present",
            ResearchOsReleaseReadinessCriterionStatus.PASS,
            source="release_readiness",
            evidence_refs=[str(inputs[name][0]) for name in ("policy_gate", "remediation", "operator_run", "catalog")],
        ))

    gate_decision = str(policy.get("decision")) if isinstance(policy, dict) and policy.get("decision") is not None else None
    gate_blockers = _list(policy, "blockers")
    gate_warnings = _list(policy, "warnings")
    if policy is None:
        criteria.append(_criterion("policy_gate", "Policy gate exists and is not BLOCK", ResearchOsReleaseReadinessCriterionStatus.FAIL, source="policy_gate", blockers=["NO_POLICY_GATE"]))
    elif gate_decision == "BLOCK" or gate_blockers:
        criteria.append(_criterion("policy_gate", "Policy gate exists and is not BLOCK", ResearchOsReleaseReadinessCriterionStatus.FAIL, source="policy_gate", evidence_refs=[str(inputs["policy_gate"][0])], blockers=gate_blockers or ["POLICY_GATE_BLOCK"]))
        blockers.extend(gate_blockers or ["POLICY_GATE_BLOCK"])
    elif gate_decision == "PASS":
        criteria.append(_criterion("policy_gate", "Policy gate exists and is not BLOCK", ResearchOsReleaseReadinessCriterionStatus.PASS, source="policy_gate", evidence_refs=[str(inputs["policy_gate"][0])]))
    else:
        criteria.append(_criterion("policy_gate", "Policy gate exists and is not BLOCK", ResearchOsReleaseReadinessCriterionStatus.WARN, source="policy_gate", evidence_refs=[str(inputs["policy_gate"][0])], warnings=gate_warnings or [f"POLICY_GATE_DECISION:{gate_decision or 'UNKNOWN'}"]))
        warnings.extend(gate_warnings[:20])

    exception_status = str(exception.get("status")) if isinstance(exception, dict) and exception.get("status") is not None else None
    if gate_decision == "WARN":
        if exception_status == "ACTIVE":
            criteria.append(_criterion("governed_exception", "WARN posture has an active governed exception", ResearchOsReleaseReadinessCriterionStatus.WARN, source="exception", evidence_refs=[str(inputs["exception"][0])], warnings=["REVIEW_REQUIRES_ACTIVE_EXCEPTION_CONSTRAINTS"]))
            warnings.append("RELEASE_REVIEW_RESTRICTED_BY_ACTIVE_EXCEPTION")
        else:
            criteria.append(_criterion("governed_exception", "WARN posture has an active governed exception", ResearchOsReleaseReadinessCriterionStatus.FAIL, source="exception", evidence_refs=[str(inputs["exception"][0])], blockers=["WARN_GATE_WITHOUT_ACTIVE_EXCEPTION"]))
            blockers.append("WARN_GATE_WITHOUT_ACTIVE_EXCEPTION")
    elif gate_decision == "PASS":
        criteria.append(_criterion("governed_exception", "PASS posture does not require a governed exception", ResearchOsReleaseReadinessCriterionStatus.NOT_APPLICABLE, source="exception"))
    elif gate_decision in ("BLOCK", "EMPTY"):
        criteria.append(_criterion("governed_exception", "BLOCK/EMPTY posture cannot be bypassed by exception", ResearchOsReleaseReadinessCriterionStatus.FAIL, source="exception", blockers=[f"POLICY_GATE_{gate_decision}"]))

    items = remediation.get("items") if isinstance(remediation, dict) else []
    if not isinstance(items, list):
        items = []
    def _open_priority(priority: str) -> int:
        return sum(1 for item in items if isinstance(item, dict) and item.get("priority") == priority and item.get("status") in {"OPEN", "BLOCKED"})
    p0 = _open_priority("P0")
    p1 = _open_priority("P1")
    p2 = _open_priority("P2")
    p3 = _open_priority("P3")
    open_count = int(remediation.get("open_count") or 0) if isinstance(remediation, dict) else 0
    blocked_count = int(remediation.get("blocked_count") or 0) if isinstance(remediation, dict) else 0
    waived_count = int(remediation.get("waived_count") or 0) if isinstance(remediation, dict) else 0
    if remediation is None:
        criteria.append(_criterion("remediation_plan", "Remediation plan exists and has no open P0/P1 items", ResearchOsReleaseReadinessCriterionStatus.FAIL, source="remediation", blockers=["NO_REMEDIATION_PLAN"]))
    elif p0 or p1 or blocked_count:
        b = []
        if p0: b.append(f"OPEN_P0_REMEDIATION:{p0}")
        if p1: b.append(f"OPEN_P1_REMEDIATION:{p1}")
        if blocked_count: b.append(f"BLOCKED_REMEDIATION:{blocked_count}")
        criteria.append(_criterion("remediation_plan", "Remediation plan exists and has no open P0/P1 items", ResearchOsReleaseReadinessCriterionStatus.FAIL, source="remediation", evidence_refs=[str(inputs["remediation"][0])], blockers=b))
        blockers.extend(b)
        followups.extend(b)
    elif open_count:
        criteria.append(_criterion("remediation_plan", "Remediation plan has only lower-priority open items", ResearchOsReleaseReadinessCriterionStatus.WARN, source="remediation", evidence_refs=[str(inputs["remediation"][0])], warnings=[f"OPEN_LOWER_PRIORITY_REMEDIATION:{open_count}"]))
        warnings.append(f"OPEN_LOWER_PRIORITY_REMEDIATION:{open_count}")
    else:
        criteria.append(_criterion("remediation_plan", "Remediation plan has no open items", ResearchOsReleaseReadinessCriterionStatus.PASS, source="remediation", evidence_refs=[str(inputs["remediation"][0])]))

    for name, raw in (("operator_run", operator_run), ("catalog", catalog), ("drift", drift)):
        if raw is None:
            criteria.append(_criterion(name, f"{name} evidence is present", ResearchOsReleaseReadinessCriterionStatus.FAIL, source=name, blockers=[f"NO_{name.upper()}"]))
            continue
        raw_status = str(raw.get("status") or raw.get("decision") or "UNKNOWN")
        raw_blockers = _list(raw, "blockers", 20)
        if raw_blockers or raw_status in {"BLOCKED", "FAILED"}:
            criteria.append(_criterion(name, f"{name} evidence has no blockers", ResearchOsReleaseReadinessCriterionStatus.FAIL, source=name, evidence_refs=[str(inputs[name][0])], blockers=raw_blockers or [f"{name.upper()}_{raw_status}"]))
            blockers.extend(raw_blockers or [f"{name.upper()}_{raw_status}"])
        elif raw_status in {"RESTRICTED", "WARN", "WARNING"}:
            criteria.append(_criterion(name, f"{name} evidence is restricted but reviewable", ResearchOsReleaseReadinessCriterionStatus.WARN, source=name, evidence_refs=[str(inputs[name][0])], warnings=[f"{name.upper()}_{raw_status}"]))
            warnings.append(f"{name.upper()}_{raw_status}")
        else:
            criteria.append(_criterion(name, f"{name} evidence has no blockers", ResearchOsReleaseReadinessCriterionStatus.PASS, source=name, evidence_refs=[str(inputs[name][0])]))

    safety = _safety_criterion(inputs)
    criteria.append(safety)
    blockers.extend(safety.blockers)
    warnings.extend(safety.warnings)

    criterion_counts: dict[str, int] = {"PASS": 0, "WARN": 0, "FAIL": 0, "NOT_APPLICABLE": 0}
    for c in criteria:
        criterion_counts[c.status.value] = criterion_counts.get(c.status.value, 0) + 1

    if not any(raw is not None for _, raw in inputs.values()):
        status = ResearchOsReleaseReadinessStatus.EMPTY
        decision = ResearchOsReleaseReadinessDecision.NO_EVIDENCE
        trust = ResearchOsTrustBanner.UNTRUSTED
        release_review_ready = False
    elif blockers or criterion_counts.get("FAIL", 0):
        status = ResearchOsReleaseReadinessStatus.BLOCKED if gate_decision == "BLOCK" or safety.blockers else ResearchOsReleaseReadinessStatus.NOT_READY
        decision = ResearchOsReleaseReadinessDecision.BLOCKED_BY_EVIDENCE if status == ResearchOsReleaseReadinessStatus.BLOCKED else ResearchOsReleaseReadinessDecision.REMEDIATION_REQUIRED
        trust = ResearchOsTrustBanner.UNTRUSTED if status == ResearchOsReleaseReadinessStatus.BLOCKED else ResearchOsTrustBanner.TRUST_RESTRICTED
        release_review_ready = False
    elif gate_decision == "PASS" and open_count == 0:
        status = ResearchOsReleaseReadinessStatus.READY_FOR_REVIEW
        decision = ResearchOsReleaseReadinessDecision.SINGLE_TENANT_REVIEW_READY
        trust = ResearchOsTrustBanner.TRUSTED
        release_review_ready = True
    else:
        status = ResearchOsReleaseReadinessStatus.RESTRICTED_REVIEW
        decision = ResearchOsReleaseReadinessDecision.REVIEW_WITH_RESTRICTIONS
        trust = ResearchOsTrustBanner.TRUST_RESTRICTED
        release_review_ready = True

    commands = [
        "strategy-validator-research-os-policy-gate build --artifact-root artifacts --overwrite --json",
        "strategy-validator-research-os-remediation build --artifact-root artifacts --overwrite --json",
        "strategy-validator-research-os-release-readiness build --artifact-root artifacts --overwrite --json",
    ]
    if blockers or p0 or p1:
        commands.insert(0, "python scripts/run_research_os_operator_run_demo.py --artifact-root artifacts --overwrite --json")
    if gate_decision == "WARN" and exception_status != "ACTIVE":
        commands.insert(0, "strategy-validator-research-os-exception request --rationale \"Restricted review exception\" --ttl-hours 24 --overwrite --json")

    report = ResearchOsReleaseReadinessReport(
        report_id=report_id,
        generated_at_utc=datetime.now(timezone.utc),
        artifact_root=str(root),
        status=status,
        decision=decision,
        trust_banner=trust,
        deployment_approved=False,
        release_review_ready=release_review_ready,
        source_policy_gate_id=str(policy.get("gate_id")) if isinstance(policy, dict) and policy.get("gate_id") is not None else None,
        source_policy_gate_decision=gate_decision,
        source_exception_id=str(exception.get("exception_id")) if isinstance(exception, dict) and exception.get("exception_id") is not None else None,
        source_exception_status=exception_status,
        source_remediation_plan_id=str(remediation.get("plan_id")) if isinstance(remediation, dict) and remediation.get("plan_id") is not None else None,
        source_operator_run_id=str(operator_run.get("run_id")) if isinstance(operator_run, dict) and operator_run.get("run_id") is not None else None,
        source_catalog_id=str(catalog.get("catalog_id")) if isinstance(catalog, dict) and catalog.get("catalog_id") is not None else None,
        source_drift_id=str(drift.get("drift_id")) if isinstance(drift, dict) and drift.get("drift_id") is not None else None,
        p0_open_count=p0,
        p1_open_count=p1,
        p2_open_count=p2,
        p3_open_count=p3,
        open_remediation_count=open_count,
        blocked_remediation_count=blocked_count,
        waived_remediation_count=waived_count,
        criterion_counts=criterion_counts,
        criteria=criteria,
        required_followups=sorted(set(followups + blockers))[:80],
        recommended_review_commands=commands,
        warnings=sorted(set(warnings))[:120],
        blockers=sorted(set(blockers))[:120],
    )
    return _with_digests(report)


def write_research_os_release_readiness_report(
    report: ResearchOsReleaseReadinessReport,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_release_readiness_root(repo_root, artifact_root)
    report_path = root / "reports" / report.report_id / "research_os_release_readiness_report.json"
    if report_path.exists() and not overwrite:
        raise FileExistsError(f"release readiness report already exists: {report_path}")
    payload = report.model_dump(mode="json")
    _write_json(report_path, payload)
    latest_dir = root / "latest"
    if latest_dir.exists() and overwrite:
        shutil.rmtree(latest_dir)
    latest_dir.mkdir(parents=True, exist_ok=True)
    _write_json(latest_dir / "research_os_release_readiness_report.json", payload)
    _write_json(latest_dir / "latest_ref.json", {"report_id": report.report_id, "report_path": str(report_path), "manifest_sha256": report.manifest_sha256})
    return report_path


def build_and_write_research_os_release_readiness_report(
    *,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    report_id: str = "research-os-release-readiness",
    overwrite: bool = False,
) -> tuple[ResearchOsReleaseReadinessReport, Path]:
    report = build_research_os_release_readiness_report(artifact_root=artifact_root, repo_root=repo_root, report_id=report_id)
    path = write_research_os_release_readiness_report(report, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return report, path


def load_latest_research_os_release_readiness_report(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsReleaseReadinessReport | None:
    p = research_os_release_readiness_latest_path(repo_root, artifact_root)
    raw = _read_json(p)
    if raw is None:
        return None
    try:
        return ResearchOsReleaseReadinessReport.model_validate(raw)
    except Exception:
        return None


def build_ui_research_os_release_readiness_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    p = research_os_release_readiness_latest_path(repo_root, artifact_root)
    raw = _read_json(p)
    if raw is None:
        return {
            "schema_version": _SCHEMA,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "MISSING",
            "degraded": ["NO_RESEARCH_OS_RELEASE_READINESS_REPORT"],
            "artifact_path": str(p),
            "latest": None,
            "read_plane_only": True,
            "no_live_trading": True,
            "no_broker_orders": True,
            "no_order_controls": True,
            "deployment_approval_unchanged": True,
        }
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PRESENT",
        "degraded": [],
        "artifact_path": str(p),
        "latest": raw,
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "deployment_approval_unchanged": True,
    }


__all__ = [
    "build_and_write_research_os_release_readiness_report",
    "build_research_os_release_readiness_report",
    "build_ui_research_os_release_readiness_latest_payload",
    "load_latest_research_os_release_readiness_report",
    "research_os_release_readiness_latest_path",
    "research_os_release_readiness_root",
    "write_research_os_release_readiness_report",
]
