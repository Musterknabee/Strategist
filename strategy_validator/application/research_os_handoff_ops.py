"""Research OS single-tenant handoff pack builder.

This module consumes existing offline/read-plane Research OS artifacts and emits a
machine-readable handoff pack. It does not execute research, call providers, call
brokers, mutate ledgers, approve deployment, or claim profitability.
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
from strategy_validator.contracts.research_os_handoff import (
    ResearchOsHandoffChecklistItem,
    ResearchOsHandoffChecklistStatus,
    ResearchOsHandoffDecision,
    ResearchOsHandoffPack,
    ResearchOsHandoffSourceRef,
    ResearchOsHandoffStatus,
)

_SCHEMA = "ui_research_os_handoff/v1"


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_handoff_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_handoff").resolve()


def research_os_handoff_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_handoff_root(repo_root, artifact_root) / "latest" / "research_os_handoff_pack.json").resolve()


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
        "release_readiness": "research_os_release_readiness/latest/research_os_release_readiness_report.json",
        "policy_gate": "research_os_policy_gate/latest/research_os_policy_gate_report.json",
        "exception": "research_os_exceptions/latest/research_os_exception_record.json",
        "remediation": "research_os_remediation/latest/research_os_remediation_plan.json",
        "export": "research_os_exports/latest/research_os_export_manifest.json",
        "catalog": "research_os_evidence_catalog/latest/research_os_evidence_catalog.json",
        "drift": "research_os_drift/latest/research_os_drift_report.json",
        "operator_run": "research_os_operator_runs/latest/research_os_operator_run_manifest.json",
        "briefing": "research_os_briefings/latest/research_os_briefing_pack.json",
        "closure": "research_os_closure/latest/research_os_closure_manifest.json",
        "attestation": "research_os_attestation/latest/operator_attestation.json",
    }
    return {name: (root / rel, _read_json(root / rel)) for name, rel in rels.items()}


def _source_ref(label: str, path: Path, raw: dict[str, Any] | None) -> ResearchOsHandoffSourceRef:
    return ResearchOsHandoffSourceRef(
        label=label,
        artifact_path=str(path),
        present=raw is not None,
        status_hint=str(raw.get("status")) if isinstance(raw, dict) and raw.get("status") is not None else None,
        decision_hint=str(raw.get("decision")) if isinstance(raw, dict) and raw.get("decision") is not None else None,
        manifest_sha256=str(raw.get("manifest_sha256")) if isinstance(raw, dict) and raw.get("manifest_sha256") is not None else None,
        warnings=_list(raw, "warnings", 20),
        blockers=_list(raw, "blockers", 20),
        metadata={
            "schema_version_observed": raw.get("schema_version") if isinstance(raw, dict) else None,
            "generated_at_utc": str(raw.get("generated_at_utc")) if isinstance(raw, dict) and raw.get("generated_at_utc") is not None else None,
        },
    )


def _check(
    item_id: str,
    title: str,
    status: ResearchOsHandoffChecklistStatus,
    *,
    source: str,
    evidence_refs: list[str] | None = None,
    warnings: list[str] | None = None,
    blockers: list[str] | None = None,
    acceptance: list[str] | None = None,
) -> ResearchOsHandoffChecklistItem:
    return ResearchOsHandoffChecklistItem(
        item_id=item_id,
        title=title,
        status=status,
        source=source,
        evidence_refs=evidence_refs or [],
        warnings=warnings or [],
        blockers=blockers or [],
        acceptance=acceptance or [],
    )


def _with_digests(pack: ResearchOsHandoffPack) -> ResearchOsHandoffPack:
    payload = pack.model_dump(mode="json", exclude={"handoff_spine_sha256", "manifest_sha256"})
    spine = {
        "handoff_id": payload.get("handoff_id"),
        "status": payload.get("status"),
        "decision": payload.get("decision"),
        "source_release_readiness_decision": payload.get("source_release_readiness_decision"),
        "source_policy_gate_decision": payload.get("source_policy_gate_decision"),
        "source_exception_status": payload.get("source_exception_status"),
        "checklist": [
            {
                "item_id": c.get("item_id"),
                "status": c.get("status"),
                "blockers": c.get("blockers", []),
                "warnings": c.get("warnings", []),
            }
            for c in payload.get("checklist", [])
        ],
        "source_refs": [
            {
                "label": r.get("label"),
                "present": r.get("present"),
                "manifest_sha256": r.get("manifest_sha256"),
                "status_hint": r.get("status_hint"),
                "decision_hint": r.get("decision_hint"),
            }
            for r in payload.get("source_refs", [])
        ],
    }
    payload["handoff_spine_sha256"] = _canonical_sha256(spine)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsHandoffPack.model_validate(payload)


def build_research_os_handoff_pack(
    *,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    handoff_id: str = "research-os-handoff",
) -> ResearchOsHandoffPack:
    root = _artifact_root(repo_root, artifact_root)
    inputs = _latest_inputs(root)
    raws = {name: raw for name, (_, raw) in inputs.items()}
    refs = [_source_ref(name, path, raw) for name, (path, raw) in inputs.items()]

    release = raws["release_readiness"]
    policy = raws["policy_gate"]
    exception = raws["exception"]
    remediation = raws["remediation"]
    export = raws["export"]
    catalog = raws["catalog"]
    operator_run = raws["operator_run"]

    warnings: list[str] = []
    blockers: list[str] = []
    followups: list[str] = []
    constraints: list[str] = []
    checklist: list[ResearchOsHandoffChecklistItem] = []

    missing_required = [name for name in ("release_readiness", "policy_gate", "remediation", "export", "catalog", "operator_run") if raws[name] is None]
    if missing_required:
        blockers.extend(f"MISSING_HANDOFF_INPUT:{name}" for name in missing_required)
        checklist.append(_check(
            "required_inputs",
            "Required handoff evidence artifacts are present",
            ResearchOsHandoffChecklistStatus.FAIL,
            source="handoff",
            blockers=[f"MISSING:{name}" for name in missing_required],
            evidence_refs=[str(inputs[name][0]) for name in missing_required],
            acceptance=["Build missing Research OS evidence artifacts before handoff."],
        ))
    else:
        checklist.append(_check(
            "required_inputs",
            "Required handoff evidence artifacts are present",
            ResearchOsHandoffChecklistStatus.PASS,
            source="handoff",
            evidence_refs=[str(inputs[name][0]) for name in ("release_readiness", "policy_gate", "remediation", "export", "catalog", "operator_run")],
        ))

    release_ready = bool(release.get("release_review_ready")) if isinstance(release, dict) else False
    release_decision = str(release.get("decision")) if isinstance(release, dict) and release.get("decision") is not None else None
    release_status = str(release.get("status")) if isinstance(release, dict) and release.get("status") is not None else None
    release_blockers = _list(release, "blockers", 40)
    release_warnings = _list(release, "warnings", 40)
    if release is None:
        checklist.append(_check("release_readiness", "Release-readiness report exists", ResearchOsHandoffChecklistStatus.FAIL, source="release_readiness", blockers=["NO_RELEASE_READINESS_REPORT"]))
    elif release_blockers or not release_ready:
        checklist.append(_check("release_readiness", "Release-readiness report allows handoff", ResearchOsHandoffChecklistStatus.FAIL, source="release_readiness", evidence_refs=[str(inputs["release_readiness"][0])], blockers=release_blockers or [f"RELEASE_READY_FALSE:{release_status or 'UNKNOWN'}"]))
        blockers.extend(release_blockers or ["RELEASE_READINESS_NOT_READY"])
    elif release_decision == "SINGLE_TENANT_REVIEW_READY":
        checklist.append(_check("release_readiness", "Release-readiness report allows handoff", ResearchOsHandoffChecklistStatus.PASS, source="release_readiness", evidence_refs=[str(inputs["release_readiness"][0])]))
    else:
        checklist.append(_check("release_readiness", "Release-readiness report allows restricted handoff", ResearchOsHandoffChecklistStatus.WARN, source="release_readiness", evidence_refs=[str(inputs["release_readiness"][0])], warnings=release_warnings or [f"RELEASE_DECISION:{release_decision or 'UNKNOWN'}"]))
        warnings.extend(release_warnings[:40] or [f"RELEASE_DECISION:{release_decision or 'UNKNOWN'}"])
        constraints.append("Handoff is restricted to release review; resolve remaining warnings before deployment approval.")

    gate_decision = str(policy.get("decision")) if isinstance(policy, dict) and policy.get("decision") is not None else None
    if policy is None:
        checklist.append(_check("policy_gate", "Policy gate is present and not BLOCK", ResearchOsHandoffChecklistStatus.FAIL, source="policy_gate", blockers=["NO_POLICY_GATE"]))
    elif gate_decision == "BLOCK" or _list(policy, "blockers", 20):
        b = _list(policy, "blockers", 20) or ["POLICY_GATE_BLOCK"]
        checklist.append(_check("policy_gate", "Policy gate is present and not BLOCK", ResearchOsHandoffChecklistStatus.FAIL, source="policy_gate", evidence_refs=[str(inputs["policy_gate"][0])], blockers=b))
        blockers.extend(b)
    elif gate_decision == "WARN":
        checklist.append(_check("policy_gate", "Policy gate WARN posture is explicitly constrained", ResearchOsHandoffChecklistStatus.WARN, source="policy_gate", evidence_refs=[str(inputs["policy_gate"][0])], warnings=["POLICY_GATE_WARN_REQUIRES_EXCEPTION_AND_CONSTRAINTS"]))
        warnings.append("POLICY_GATE_WARN_REQUIRES_EXCEPTION_AND_CONSTRAINTS")
        constraints.append("Policy gate is WARN, so this pack is not deployment approval.")
    else:
        checklist.append(_check("policy_gate", "Policy gate is present and not BLOCK", ResearchOsHandoffChecklistStatus.PASS, source="policy_gate", evidence_refs=[str(inputs["policy_gate"][0])]))

    exception_status = str(exception.get("status")) if isinstance(exception, dict) and exception.get("status") is not None else None
    if gate_decision == "WARN":
        if exception_status == "ACTIVE":
            constraints.extend(_list(exception, "constraints", 20))
            checklist.append(_check("governed_exception", "WARN posture has active governed exception constraints", ResearchOsHandoffChecklistStatus.WARN, source="exception", evidence_refs=[str(inputs["exception"][0])], warnings=["ACTIVE_EXCEPTION_LIMITS_HANDOFF_SCOPE"]))
        else:
            checklist.append(_check("governed_exception", "WARN posture has active governed exception constraints", ResearchOsHandoffChecklistStatus.FAIL, source="exception", blockers=["WARN_GATE_WITHOUT_ACTIVE_EXCEPTION"]))
            blockers.append("WARN_GATE_WITHOUT_ACTIVE_EXCEPTION")
    else:
        checklist.append(_check("governed_exception", "Governed exception is only required for WARN posture", ResearchOsHandoffChecklistStatus.NOT_APPLICABLE, source="exception"))

    for name, raw in (("remediation", remediation), ("export", export), ("catalog", catalog), ("operator_run", operator_run)):
        if raw is None:
            checklist.append(_check(name, f"{name} evidence is present", ResearchOsHandoffChecklistStatus.FAIL, source=name, blockers=[f"NO_{name.upper()}"]))
            continue
        raw_blockers = _list(raw, "blockers", 20)
        raw_status = str(raw.get("status") or raw.get("decision") or "UNKNOWN")
        if raw_blockers or raw_status in {"BLOCKED", "FAILED", "NOT_READY"}:
            checklist.append(_check(name, f"{name} evidence has no blockers", ResearchOsHandoffChecklistStatus.FAIL, source=name, evidence_refs=[str(inputs[name][0])], blockers=raw_blockers or [f"{name.upper()}_{raw_status}"]))
            blockers.extend(raw_blockers or [f"{name.upper()}_{raw_status}"])
        elif raw_status in {"RESTRICTED", "RESTRICTED_REVIEW", "WARN", "WARNING"}:
            checklist.append(_check(name, f"{name} evidence is restricted but handoff-visible", ResearchOsHandoffChecklistStatus.WARN, source=name, evidence_refs=[str(inputs[name][0])], warnings=[f"{name.upper()}_{raw_status}"]))
            warnings.append(f"{name.upper()}_{raw_status}")
        else:
            checklist.append(_check(name, f"{name} evidence has no blockers", ResearchOsHandoffChecklistStatus.PASS, source=name, evidence_refs=[str(inputs[name][0])]))

    for name, raw in raws.items():
        if not isinstance(raw, dict):
            continue
        for flag in ("no_live_trading", "no_broker_orders", "no_order_controls", "no_profitability_claim", "deployment_approval_unchanged"):
            if raw.get(flag) is False:
                blockers.append(f"{name}:{flag}=false")
        if raw.get("deployment_approved") is True:
            blockers.append(f"{name}:deployment_approved=true")
        if raw.get("read_plane_only") is False:
            blockers.append(f"{name}:read_plane_only=false")
    safety_blockers = [b for b in blockers if ":no_" in b or "deployment_approved" in b or "read_plane_only" in b]
    checklist.append(_check(
        "safety_flags",
        "Safety flags remain read-plane-only and non-trading",
        ResearchOsHandoffChecklistStatus.FAIL if safety_blockers else ResearchOsHandoffChecklistStatus.PASS,
        source="handoff",
        blockers=safety_blockers,
        warnings=[] if safety_blockers else ["HANDOFF_PACK_DOES_NOT_APPROVE_DEPLOYMENT"],
        acceptance=["no_live_trading/no_broker_orders/no_order_controls stay true", "deployment_approved stays false"],
    ))

    if isinstance(remediation, dict):
        followups.extend(_list(remediation, "recommended_next_actions", 30))
    if isinstance(release, dict):
        followups.extend(_list(release, "required_followups", 30))
    constraints = sorted(set(str(x) for x in constraints if x))[:60]
    followups = sorted(set(str(x) for x in followups + blockers if x))[:80]
    warnings = sorted(set(str(x) for x in warnings if x))[:120]
    blockers = sorted(set(str(x) for x in blockers if x))[:120]

    counts = {"PASS": 0, "WARN": 0, "FAIL": 0, "NOT_APPLICABLE": 0}
    for c in checklist:
        counts[c.status.value] = counts.get(c.status.value, 0) + 1

    if not any(raw is not None for raw in raws.values()):
        status = ResearchOsHandoffStatus.EMPTY
        decision = ResearchOsHandoffDecision.NO_EVIDENCE
        trust = ResearchOsTrustBanner.UNTRUSTED
        handoff_ready = False
        restricted = False
    elif blockers or counts.get("FAIL", 0):
        status = ResearchOsHandoffStatus.BLOCKED if any("false" in b or "BLOCK" in b for b in blockers) else ResearchOsHandoffStatus.NOT_READY
        decision = ResearchOsHandoffDecision.BLOCKED_BY_EVIDENCE if status == ResearchOsHandoffStatus.BLOCKED else ResearchOsHandoffDecision.REMEDIATION_REQUIRED
        trust = ResearchOsTrustBanner.UNTRUSTED if status == ResearchOsHandoffStatus.BLOCKED else ResearchOsTrustBanner.TRUST_RESTRICTED
        handoff_ready = False
        restricted = False
    elif warnings or release_decision == "REVIEW_WITH_RESTRICTIONS" or gate_decision == "WARN":
        status = ResearchOsHandoffStatus.RESTRICTED
        decision = ResearchOsHandoffDecision.HANDOFF_WITH_RESTRICTIONS
        trust = ResearchOsTrustBanner.TRUST_RESTRICTED
        handoff_ready = True
        restricted = True
    else:
        status = ResearchOsHandoffStatus.READY
        decision = ResearchOsHandoffDecision.SINGLE_TENANT_HANDOFF_READY
        trust = ResearchOsTrustBanner.TRUSTED
        handoff_ready = True
        restricted = False

    commands = [
        "python scripts/run_research_os_operator_run_demo.py --artifact-root artifacts --overwrite --json",
        "strategy-validator-research-os-policy-gate build --artifact-root artifacts --overwrite --json",
        "strategy-validator-research-os-remediation build --artifact-root artifacts --overwrite --json",
        "strategy-validator-research-os-release-readiness build --artifact-root artifacts --overwrite --json",
        "strategy-validator-research-os-handoff build --artifact-root artifacts --overwrite --json",
    ]
    if gate_decision == "WARN" and exception_status != "ACTIVE":
        commands.insert(3, "strategy-validator-research-os-exception request --rationale \"Restricted handoff exception\" --ttl-hours 24 --overwrite --json")

    pack = ResearchOsHandoffPack(
        handoff_id=handoff_id,
        generated_at_utc=datetime.now(timezone.utc),
        artifact_root=str(root),
        status=status,
        decision=decision,
        trust_banner=trust,
        deployment_approved=False,
        handoff_ready=handoff_ready,
        restricted_handoff=restricted,
        source_release_readiness_report_id=str(release.get("report_id")) if isinstance(release, dict) and release.get("report_id") is not None else None,
        source_release_readiness_decision=release_decision,
        source_policy_gate_id=str(policy.get("gate_id")) if isinstance(policy, dict) and policy.get("gate_id") is not None else None,
        source_policy_gate_decision=gate_decision,
        source_exception_id=str(exception.get("exception_id")) if isinstance(exception, dict) and exception.get("exception_id") is not None else None,
        source_exception_status=exception_status,
        source_remediation_plan_id=str(remediation.get("plan_id")) if isinstance(remediation, dict) and remediation.get("plan_id") is not None else None,
        source_export_id=str(export.get("export_id")) if isinstance(export, dict) and export.get("export_id") is not None else None,
        source_catalog_id=str(catalog.get("catalog_id")) if isinstance(catalog, dict) and catalog.get("catalog_id") is not None else None,
        source_operator_run_id=str(operator_run.get("run_id")) if isinstance(operator_run, dict) and operator_run.get("run_id") is not None else None,
        source_refs=refs,
        checklist=checklist,
        checklist_counts=counts,
        required_operator_commands=commands,
        handoff_constraints=constraints,
        remaining_followups=followups,
        warnings=warnings,
        blockers=blockers,
    )
    return _with_digests(pack)


def write_research_os_handoff_pack(
    pack: ResearchOsHandoffPack,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_handoff_root(repo_root, artifact_root)
    pack_path = root / "packs" / pack.handoff_id / "research_os_handoff_pack.json"
    if pack_path.exists() and not overwrite:
        raise FileExistsError(f"handoff pack already exists: {pack_path}")
    payload = pack.model_dump(mode="json")
    _write_json(pack_path, payload)
    latest_dir = root / "latest"
    if latest_dir.exists() and overwrite:
        shutil.rmtree(latest_dir)
    latest_dir.mkdir(parents=True, exist_ok=True)
    _write_json(latest_dir / "research_os_handoff_pack.json", payload)
    _write_json(latest_dir / "latest_ref.json", {"handoff_id": pack.handoff_id, "pack_path": str(pack_path), "manifest_sha256": pack.manifest_sha256})
    return pack_path


def build_and_write_research_os_handoff_pack(
    *,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    handoff_id: str = "research-os-handoff",
    overwrite: bool = False,
) -> tuple[ResearchOsHandoffPack, Path]:
    pack = build_research_os_handoff_pack(artifact_root=artifact_root, repo_root=repo_root, handoff_id=handoff_id)
    path = write_research_os_handoff_pack(pack, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return pack, path


def load_latest_research_os_handoff_pack(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsHandoffPack | None:
    raw = _read_json(research_os_handoff_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    try:
        return ResearchOsHandoffPack.model_validate(raw)
    except Exception:
        return None


def build_ui_research_os_handoff_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    p = research_os_handoff_latest_path(repo_root, artifact_root)
    raw = _read_json(p)
    if raw is None:
        return {
            "schema_version": _SCHEMA,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "status": "MISSING",
            "degraded": ["NO_RESEARCH_OS_HANDOFF_PACK"],
            "artifact_path": str(p),
            "latest": None,
            "read_plane_only": True,
            "no_live_trading": True,
            "no_broker_orders": True,
            "no_order_controls": True,
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
    }


__all__ = [
    "build_and_write_research_os_handoff_pack",
    "build_research_os_handoff_pack",
    "build_ui_research_os_handoff_latest_payload",
    "load_latest_research_os_handoff_pack",
    "research_os_handoff_latest_path",
    "research_os_handoff_root",
    "write_research_os_handoff_pack",
]
