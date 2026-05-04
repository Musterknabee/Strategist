"""Research OS remediation plan builder.

Builds a read-plane action queue from the latest Research OS policy gate,
exception, catalog, and drift artifacts. This module does not execute research,
call providers, call brokers, mutate ledgers, approve deployment, or make
profitability claims.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.contracts.research_os_remediation import (
    ResearchOsRemediationCategory,
    ResearchOsRemediationItem,
    ResearchOsRemediationItemStatus,
    ResearchOsRemediationPlan,
    ResearchOsRemediationPriority,
    ResearchOsRemediationStatus,
)

_SCHEMA = "ui_research_os_remediation/v1"


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_remediation_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_remediation").resolve()


def research_os_remediation_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_remediation_root(repo_root, artifact_root) / "latest" / "research_os_remediation_plan.json").resolve()


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


def _slug(text: str, limit: int = 64) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.:-]+", "_", text.strip())[:limit].strip("_")
    return cleaned or "item"


def _list(raw: dict[str, Any] | None, key: str, limit: int = 120) -> list[str]:
    value = raw.get(key) if isinstance(raw, dict) else []
    if not isinstance(value, list):
        return []
    rows = [str(x) for x in value if x is not None]
    if len(rows) > limit:
        return rows[:limit] + [f"{key.upper()}_TRUNCATED:{len(rows)}"]
    return rows


def _category_for_signal(signal: str) -> ResearchOsRemediationCategory:
    u = signal.upper()
    if "PROVIDER_PAPER_LOOP" in u or "PROVIDER PAPER" in u:
        return ResearchOsRemediationCategory.PROVIDER_LOOP
    if "PROVIDER" in u:
        return ResearchOsRemediationCategory.PROVIDER_LOOP
    if "BROKER" in u:
        return ResearchOsRemediationCategory.PAPER_BROKER
    if "STRATEGY_MEMORY" in u or "MEMORY" in u:
        return ResearchOsRemediationCategory.STRATEGY_MEMORY
    if "THESIS" in u:
        return ResearchOsRemediationCategory.THESIS
    if "SHADOW" in u:
        return ResearchOsRemediationCategory.SHADOW_BOOK
    if "DRIFT" in u:
        return ResearchOsRemediationCategory.DRIFT
    if "CATALOG" in u:
        return ResearchOsRemediationCategory.CATALOG
    if "SECRET" in u or "TOKEN" in u or "KEY" in u and "PENDING" not in u:
        return ResearchOsRemediationCategory.SECURITY
    if "MISSING_REQUIRED" in u or "REQUIRED" in u:
        return ResearchOsRemediationCategory.REQUIRED_EVIDENCE
    if "MISSING" in u or "NO_" in u or "OPTIONAL" in u:
        return ResearchOsRemediationCategory.OPTIONAL_EVIDENCE
    if "EXCEPTION" in u:
        return ResearchOsRemediationCategory.EXCEPTION
    return ResearchOsRemediationCategory.POLICY_GATE


def _priority_for_signal(signal: str, *, blocker: bool = False) -> ResearchOsRemediationPriority:
    u = signal.upper()
    if blocker or "SECRET" in u or "TAMPER" in u or "SAFETY_FLAG_FALSE" in u:
        return ResearchOsRemediationPriority.P0
    if "MISSING_REQUIRED" in u or "NO_CLOSURE" in u or "NO_OPERATOR" in u or "NO_POLICY" in u:
        return ResearchOsRemediationPriority.P1
    if "PROVIDER" in u or "BROKER" in u or "DRIFT" in u or "RESTRICTED" in u:
        return ResearchOsRemediationPriority.P2
    return ResearchOsRemediationPriority.P3


def _command_for_category(category: ResearchOsRemediationCategory) -> str | None:
    commands = {
        ResearchOsRemediationCategory.PROVIDER_LOOP: "python scripts/run_provider_paper_loop.py --artifact-root artifacts/provider_paper_loop --run-id provider-paper-demo --overwrite --no-network --json",
        ResearchOsRemediationCategory.PAPER_BROKER: "strategy-validator-paper-broker status --env-file deployment.env --output-root artifacts/paper_broker --json",
        ResearchOsRemediationCategory.STRATEGY_MEMORY: "strategy-validator-strategy-memory build-index --json",
        ResearchOsRemediationCategory.THESIS: "strategy-validator-thesis list --json",
        ResearchOsRemediationCategory.SHADOW_BOOK: "python scripts/run_shadow_book_demo.py --artifact-root artifacts/shadow_books --overwrite --json",
        ResearchOsRemediationCategory.DRIFT: "strategy-validator-research-os-drift build --artifact-root artifacts --overwrite --json",
        ResearchOsRemediationCategory.CATALOG: "strategy-validator-research-os-catalog build --artifact-root artifacts --overwrite --json",
        ResearchOsRemediationCategory.REQUIRED_EVIDENCE: "python scripts/run_research_os_operator_run_demo.py --artifact-root artifacts --overwrite --json",
        ResearchOsRemediationCategory.POLICY_GATE: "strategy-validator-research-os-policy-gate build --artifact-root artifacts --overwrite --json",
        ResearchOsRemediationCategory.EXCEPTION: "strategy-validator-research-os-exception request --rationale \"Paper-only restricted evidence acknowledged\" --ttl-hours 24 --overwrite --json",
    }
    return commands.get(category)


def _make_item(
    signal: str,
    *,
    source: str,
    blocker: bool = False,
    evidence_refs: list[str] | None = None,
    status: ResearchOsRemediationItemStatus | None = None,
) -> ResearchOsRemediationItem:
    category = _category_for_signal(signal)
    priority = _priority_for_signal(signal, blocker=blocker)
    item_status = status or (ResearchOsRemediationItemStatus.BLOCKED if blocker else ResearchOsRemediationItemStatus.OPEN)
    sid = hashlib.sha256(f"{source}:{signal}".encode("utf-8")).hexdigest()[:12]
    title = signal.replace("_", " ").replace(":", " · ")[:120]
    acceptance = [
        "Regenerate the referenced evidence artifact.",
        "Rebuild the Research OS evidence catalog and policy gate.",
        "Confirm the item no longer appears in the latest remediation plan.",
    ]
    if category == ResearchOsRemediationCategory.SECURITY:
        acceptance = [
            "Remove the secret marker from generated artifacts/source.",
            "Rotate any real exposed credential outside this repository if applicable.",
            "Rebuild catalog/policy gate and confirm no SECRET_MARKER blockers remain.",
        ]
    return ResearchOsRemediationItem(
        item_id=f"{priority.value}-{_slug(category.value.lower())}-{sid}",
        category=category,
        priority=priority,
        status=item_status,
        title=title,
        description=f"Remediate Research OS evidence signal from {source}: {signal}",
        source=source,
        evidence_refs=evidence_refs or [],
        recommended_command=_command_for_category(category),
        acceptance=acceptance,
        blockers=[signal] if blocker else [],
        warnings=[] if blocker else [signal],
    )


def _dedupe(items: list[ResearchOsRemediationItem]) -> list[ResearchOsRemediationItem]:
    by_key: dict[tuple[str, str], ResearchOsRemediationItem] = {}
    order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    for item in items:
        key = (item.category.value, item.title)
        prev = by_key.get(key)
        if prev is None or order[item.priority.value] < order[prev.priority.value]:
            by_key[key] = item
    return sorted(by_key.values(), key=lambda i: (order[i.priority.value], i.category.value, i.item_id))[:200]


def _with_digests(plan: ResearchOsRemediationPlan) -> ResearchOsRemediationPlan:
    payload = plan.model_dump(mode="json", exclude={"remediation_spine_sha256", "manifest_sha256"})
    spine = {
        "plan_id": payload.get("plan_id"),
        "source_policy_gate_id": payload.get("source_policy_gate_id"),
        "source_policy_gate_decision": payload.get("source_policy_gate_decision"),
        "source_exception_id": payload.get("source_exception_id"),
        "source_exception_status": payload.get("source_exception_status"),
        "source_catalog_id": payload.get("source_catalog_id"),
        "source_drift_id": payload.get("source_drift_id"),
        "items": [
            {
                "item_id": item.get("item_id"),
                "category": item.get("category"),
                "priority": item.get("priority"),
                "status": item.get("status"),
                "title": item.get("title"),
                "source": item.get("source"),
            }
            for item in payload.get("items", [])
        ],
    }
    payload["remediation_spine_sha256"] = _canonical_sha256(spine)
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return ResearchOsRemediationPlan.model_validate(payload)


def build_research_os_remediation_plan(*, plan_id: str, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsRemediationPlan:
    root = _artifact_root(repo_root, artifact_root)
    gate_path = root / "research_os_policy_gate" / "latest" / "research_os_policy_gate_report.json"
    exception_path = root / "research_os_exceptions" / "latest" / "research_os_exception_record.json"
    catalog_path = root / "research_os_evidence_catalog" / "latest" / "research_os_evidence_catalog.json"
    drift_path = root / "research_os_drift" / "latest" / "research_os_drift_report.json"
    gate = _read_json(gate_path)
    exception = _read_json(exception_path)
    catalog = _read_json(catalog_path)
    drift = _read_json(drift_path)

    warnings: list[str] = []
    blockers: list[str] = []
    items: list[ResearchOsRemediationItem] = []

    if gate is None:
        blockers.append("NO_RESEARCH_OS_POLICY_GATE_REPORT")
        items.append(_make_item("NO_RESEARCH_OS_POLICY_GATE_REPORT", source="policy_gate", blocker=True, evidence_refs=[str(gate_path)]))
    else:
        for b in _list(gate, "blockers"):
            items.append(_make_item(b, source="policy_gate.blockers", blocker=True, evidence_refs=[str(gate_path)]))
        for w in _list(gate, "warnings"):
            items.append(_make_item(w, source="policy_gate.warnings", evidence_refs=[str(gate_path)]))
        for action in _list(gate, "recommended_operator_actions", limit=40):
            items.append(_make_item(action, source="policy_gate.recommended_operator_actions", evidence_refs=[str(gate_path)]))
        for rule in gate.get("rules") or []:
            if not isinstance(rule, dict):
                continue
            status = str(rule.get("status") or "")
            if status in {"WARN", "BLOCK"}:
                msg = str(rule.get("message") or rule.get("rule_id") or "POLICY_RULE_NEEDS_REVIEW")
                items.append(_make_item(msg, source=f"policy_gate.rule:{rule.get('rule_id')}", blocker=status == "BLOCK", evidence_refs=[str(gate_path)]))

    if exception is None:
        warnings.append("NO_RESEARCH_OS_EXCEPTION_RECORD")
        items.append(_make_item("NO_RESEARCH_OS_EXCEPTION_RECORD", source="exception", evidence_refs=[str(exception_path)]))
    else:
        ex_status = str(exception.get("status") or "")
        if ex_status in {"ACTIVE", "NOT_APPLICABLE"}:
            for fw in _list(exception, "recommended_followups", limit=40):
                items.append(_make_item(fw, source="exception.recommended_followups", status=ResearchOsRemediationItemStatus.WAIVED_BY_EXCEPTION if ex_status == "ACTIVE" else None, evidence_refs=[str(exception_path)]))
            for rw in _list(exception, "residual_warnings", limit=80):
                items.append(_make_item(rw, source="exception.residual_warnings", evidence_refs=[str(exception_path)]))
        else:
            items.append(_make_item(f"RESEARCH_OS_EXCEPTION_{ex_status or 'NOT_ACTIVE'}", source="exception", blocker=ex_status in {"REJECTED", "EXPIRED"}, evidence_refs=[str(exception_path)]))

    if catalog is None:
        warnings.append("NO_RESEARCH_OS_EVIDENCE_CATALOG")
        items.append(_make_item("NO_RESEARCH_OS_EVIDENCE_CATALOG", source="catalog", evidence_refs=[str(catalog_path)]))
    else:
        for b in _list(catalog, "blockers", limit=80):
            items.append(_make_item(b, source="catalog.blockers", blocker=True, evidence_refs=[str(catalog_path)]))
        # Missing high-value optional evidence should be visible even when it is not a policy blocker.
        latest_by_category = catalog.get("latest_by_category") if isinstance(catalog.get("latest_by_category"), dict) else {}
        for cat, signal in {
            "PROVIDER_LOOP": "MISSING_PROVIDER_PAPER_LOOP_LATEST_ARTIFACT",
            "PAPER_BROKER": "MISSING_PAPER_BROKER_STATUS_LATEST_ARTIFACT",
            "STRATEGY_MEMORY": "MISSING_STRATEGY_MEMORY_INDEX",
            "STRATEGY_THESIS": "MISSING_STRATEGY_THESIS_EVALUATION",
            "SHADOW_BOOK": "MISSING_SHADOW_BOOK_LATEST_ARTIFACT",
        }.items():
            if cat not in latest_by_category:
                items.append(_make_item(signal, source="catalog.latest_by_category", evidence_refs=[str(catalog_path)]))

    if drift is None:
        warnings.append("NO_RESEARCH_OS_EVIDENCE_DRIFT_REPORT")
        items.append(_make_item("NO_RESEARCH_OS_EVIDENCE_DRIFT_REPORT", source="drift", evidence_refs=[str(drift_path)]))
    else:
        changed = int(drift.get("changed_count") or 0)
        added = int(drift.get("added_count") or 0)
        removed = int(drift.get("removed_count") or 0)
        if changed or removed:
            items.append(_make_item(f"EVIDENCE_DRIFT_REVIEW_REQUIRED:changed={changed}:removed={removed}", source="drift", evidence_refs=[str(drift_path)]))
        elif added:
            items.append(_make_item(f"EVIDENCE_DRIFT_NEW_ARTIFACTS_ADDED:{added}", source="drift", evidence_refs=[str(drift_path)]))
        for b in _list(drift, "blockers", limit=40):
            items.append(_make_item(b, source="drift.blockers", blocker=True, evidence_refs=[str(drift_path)]))

    items = _dedupe(items)
    open_count = sum(1 for i in items if i.status == ResearchOsRemediationItemStatus.OPEN)
    blocked_count = sum(1 for i in items if i.status == ResearchOsRemediationItemStatus.BLOCKED)
    waived_count = sum(1 for i in items if i.status == ResearchOsRemediationItemStatus.WAIVED_BY_EXCEPTION)
    priority_counts: dict[str, int] = {}
    category_counts: dict[str, int] = {}
    for item in items:
        priority_counts[item.priority.value] = priority_counts.get(item.priority.value, 0) + 1
        category_counts[item.category.value] = category_counts.get(item.category.value, 0) + 1

    if gate is None and not items:
        status = ResearchOsRemediationStatus.EMPTY
        banner = ResearchOsTrustBanner.UNTRUSTED
    elif blocked_count or blockers:
        status = ResearchOsRemediationStatus.BLOCKED
        banner = ResearchOsTrustBanner.UNTRUSTED
    elif open_count or waived_count or warnings:
        status = ResearchOsRemediationStatus.RESTRICTED
        banner = ResearchOsTrustBanner.TRUST_RESTRICTED
    else:
        status = ResearchOsRemediationStatus.READY
        banner = ResearchOsTrustBanner.TRUSTED

    next_actions = [item.recommended_command for item in items if item.recommended_command][:8]
    if not next_actions and status == ResearchOsRemediationStatus.READY:
        next_actions = ["Re-run the Research OS operator pipeline on the next scheduled cadence."]

    plan = ResearchOsRemediationPlan(
        plan_id=plan_id,
        artifact_root=str(root),
        status=status,
        trust_banner=banner,
        source_policy_gate_id=str(gate.get("gate_id")) if isinstance(gate, dict) and gate.get("gate_id") else None,
        source_policy_gate_decision=str(gate.get("decision")) if isinstance(gate, dict) and gate.get("decision") else None,
        source_exception_id=str(exception.get("exception_id")) if isinstance(exception, dict) and exception.get("exception_id") else None,
        source_exception_status=str(exception.get("status")) if isinstance(exception, dict) and exception.get("status") else None,
        source_catalog_id=str(catalog.get("catalog_id")) if isinstance(catalog, dict) and catalog.get("catalog_id") else None,
        source_drift_id=str(drift.get("drift_id")) if isinstance(drift, dict) and drift.get("drift_id") else None,
        open_count=open_count,
        blocked_count=blocked_count,
        waived_count=waived_count,
        item_count=len(items),
        priority_counts=priority_counts,
        category_counts=category_counts,
        items=items,
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
        recommended_next_actions=next_actions,
    )
    return _with_digests(plan)


def write_research_os_remediation_plan(plan: ResearchOsRemediationPlan, *, repo_root: Path | None = None, artifact_root: Path | None = None, overwrite: bool = False) -> Path:
    rroot = research_os_remediation_root(repo_root=repo_root, artifact_root=artifact_root)
    path = rroot / "plans" / plan.plan_id / "research_os_remediation_plan.json"
    if path.exists() and not overwrite:
        raise FileExistsError(f"remediation plan already exists: {path}")
    payload = plan.model_dump(mode="json")
    _write_json(path, payload)
    latest = rroot / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, latest / "research_os_remediation_plan.json")
    _write_json(latest / "latest_ref.json", {"plan_id": plan.plan_id, "manifest_path": str(path), "manifest_sha256": plan.manifest_sha256})
    return path


def build_and_write_research_os_remediation_plan(*, plan_id: str, repo_root: Path | None = None, artifact_root: Path | None = None, overwrite: bool = False) -> tuple[ResearchOsRemediationPlan, Path]:
    plan = build_research_os_remediation_plan(plan_id=plan_id, repo_root=repo_root, artifact_root=artifact_root)
    path = write_research_os_remediation_plan(plan, repo_root=repo_root, artifact_root=artifact_root, overwrite=overwrite)
    return plan, path


def load_latest_research_os_remediation_plan(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsRemediationPlan | None:
    raw = _read_json(research_os_remediation_latest_path(repo_root=repo_root, artifact_root=artifact_root))
    if raw is None:
        return None
    return ResearchOsRemediationPlan.model_validate(raw)


def build_ui_research_os_remediation_latest_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    path = research_os_remediation_latest_path(repo_root=repo_root, artifact_root=artifact_root)
    plan = load_latest_research_os_remediation_plan(repo_root=repo_root, artifact_root=artifact_root)
    if plan is None:
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
            "degraded": ["NO_RESEARCH_OS_REMEDIATION_PLAN"],
        }
    degraded = [] if plan.status == ResearchOsRemediationStatus.READY else [f"RESEARCH_OS_REMEDIATION_{plan.status.value}"]
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "status": "PRESENT",
        "manifest_path": str(path),
        "latest": plan.model_dump(mode="json"),
        "degraded": degraded,
    }


__all__ = [
    "build_and_write_research_os_remediation_plan",
    "build_research_os_remediation_plan",
    "build_ui_research_os_remediation_latest_payload",
    "load_latest_research_os_remediation_plan",
    "research_os_remediation_latest_path",
    "research_os_remediation_root",
    "write_research_os_remediation_plan",
]
