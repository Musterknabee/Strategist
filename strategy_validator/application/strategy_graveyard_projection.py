"""UI read model for strategy graveyard and resurrection rules."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.strategy_memory_ops import load_graveyard_entries, load_memory_records, strategy_memory_root_directory
from strategy_validator.contracts.strategy_graveyard import (
    StrategyGraveyardEntryView,
    StrategyGraveyardPayload,
    StrategyGraveyardResurrectionRule,
    StrategyGraveyardSummary,
)
from strategy_validator.contracts.strategy_memory import CandidateGraveyardEntry, StrategyMemoryRecord, StrategyMemoryStatus

_SCHEMA = "ui_strategy_graveyard/v1"


def _record_by_strategy(records: list[StrategyMemoryRecord]) -> dict[str, StrategyMemoryRecord]:
    return {r.strategy_id: r for r in records}


def _failure_values(entry: CandidateGraveyardEntry, record: StrategyMemoryRecord | None) -> list[str]:
    reasons = [r.value if hasattr(r, "value") else str(r) for r in entry.failure_reasons]
    if record is not None:
        for r in record.failure_reasons:
            value = r.value if hasattr(r, "value") else str(r)
            if value not in reasons:
                reasons.append(value)
    if not reasons:
        status = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
        if status in {"KILLED", "REJECTED", "DUPLICATE_VARIANT"}:
            reasons.append(status)
    return sorted(reasons)


def _rule(reason: str) -> StrategyGraveyardResurrectionRule:
    catalog: dict[str, tuple[str, list[str], str, str]] = {
        "PIT": ("Prove point-in-time joins and timestamp ordering before any new backtest is trusted.", ["pit_join_verification", "as_of_join_manifest", "lookahead_leakage_report"], "PIT failures invalidate historical performance evidence.", "BLOCKING"),
        "EXECUTION_REALISM": ("Attach liquidity, borrow, slippage, and market-session realism evidence.", ["execution_realism_report", "liquidity_report", "borrow_legality_report", "slippage_model_evidence"], "A strategy that cannot be executed realistically should not consume promotion review budget.", "BLOCKING"),
        "ROBUSTNESS": ("Re-run robustness evidence with CPCV/PBO/DSR or an equivalent predeclared robustness protocol.", ["cpcv_report", "pbo_report", "dsr_report", "robustness_manifest"], "The prior evidence did not prove robustness outside the fitted sample.", "CONDITIONAL"),
        "DATA_QUALITY": ("Provide a fresh, provider-backed dataset with data-quality checks passing.", ["provider_snapshot_manifest", "data_quality_report", "sample_freshness_evidence"], "Original candidate failed because the data substrate was not trustworthy enough.", "CONDITIONAL"),
        "KILL_RULE": ("Satisfy the original kill-rule memo or attach an explicit governed exception.", ["kill_rule_reversal_memo", "governed_exception", "operator_signoff"], "Killed strategies remain blocked until the kill condition is disproven or formally excepted.", "BLOCKING"),
        "DUPLICATE_VARIANT": ("Prove the variant is materially different from the existing family member.", ["variant_fingerprint_diff", "incremental_edge_memo", "family_duplicate_review"], "Duplicate variants should be superseded rather than re-researched.", "BLOCKING"),
        "OPERATOR_REJECTED": ("Require explicit operator review before reopening the idea.", ["operator_reopen_memo", "scope_change_rationale"], "The candidate was rejected by operator judgment.", "REVIEW"),
        "REJECTED": ("Attach a scope-change memo explaining what materially changed since rejection.", ["scope_change_memo", "new_evidence_manifest"], "Rejected candidates need a concrete delta before reopening.", "REVIEW"),
        "KILLED": ("Attach kill-rule reversal evidence before reopening.", ["kill_rule_reversal_memo", "new_evidence_manifest"], "Killed candidates are blocked by default.", "BLOCKING"),
    }
    condition, required, rationale, status = catalog.get(reason, ("Provide new material evidence and operator rationale before re-opening.", ["new_evidence_manifest", "operator_reopen_memo"], "Unknown failure reason; default to conservative review.", "REVIEW"))
    return StrategyGraveyardResurrectionRule(rule_id=f"resurrection:{reason.lower()}", failure_reason=reason, condition=condition, required_evidence=required, rationale=rationale, status=status)  # type: ignore[arg-type]


def _resurrectability(status: str, reasons: list[str]) -> str:
    rs = set(reasons)
    if status == StrategyMemoryStatus.DUPLICATE_VARIANT.value or "DUPLICATE_VARIANT" in rs:
        return "DUPLICATE_SUPERSEDED"
    if "OPERATOR_REJECTED" in rs or status == StrategyMemoryStatus.REJECTED.value:
        return "OPERATOR_REVIEW_REQUIRED"
    if status == StrategyMemoryStatus.KILLED.value or rs & {"KILL_RULE", "PIT", "EXECUTION_REALISM", "KILLED"}:
        return "HARD_BLOCKED_UNTIL_EVIDENCE"
    if rs:
        return "CONDITIONAL_RESEARCH_RETRY"
    return "UNKNOWN"


def _hard_blockers(status: str, reasons: list[str]) -> list[str]:
    blockers: list[str] = []
    if status == StrategyMemoryStatus.DUPLICATE_VARIANT.value or "DUPLICATE_VARIANT" in reasons:
        blockers.append("DUPLICATE_VARIANT_REQUIRES_MATERIAL_DIFFERENCE")
    if status == StrategyMemoryStatus.KILLED.value or "KILL_RULE" in reasons or "KILLED" in reasons:
        blockers.append("KILL_RULE_REOPEN_REQUIRES_EVIDENCE_OR_EXCEPTION")
    if "PIT" in reasons:
        blockers.append("PIT_LEAKAGE_REQUIRES_AS_OF_PROOF")
    if "EXECUTION_REALISM" in reasons:
        blockers.append("EXECUTION_REALISM_REQUIRES_LIQUIDITY_BORROW_SLIPPAGE_PROOF")
    if "OPERATOR_REJECTED" in reasons or status == StrategyMemoryStatus.REJECTED.value:
        blockers.append("OPERATOR_REVIEW_REQUIRED")
    return blockers


def _view(entry: CandidateGraveyardEntry, record: StrategyMemoryRecord | None) -> StrategyGraveyardEntryView:
    status = entry.status.value if hasattr(entry.status, "value") else str(entry.status)
    reasons = _failure_values(entry, record)
    evidence_refs = list(entry.evidence_refs)
    if record is not None:
        for ref in record.evidence_refs:
            if ref not in evidence_refs:
                evidence_refs.append(ref)
    return StrategyGraveyardEntryView(
        strategy_id=entry.strategy_id,
        family_id=entry.family_id,
        status=status,
        kill_reason=entry.kill_reason,
        killed_at_utc=entry.killed_at_utc,
        failure_reasons=reasons,
        resurrectability=_resurrectability(status, reasons),
        resurrection_rules=[_rule(reason) for reason in reasons],
        hard_blockers=_hard_blockers(status, reasons),
        advisory_notes=["Research memory only; no promotion or execution authority is implied."],
        source_record_sha256=record.record_sha256 if record else None,
        entry_sha256=entry.entry_sha256,
        run_id=record.run_id if record else None,
        batch_id=record.batch_id if record else None,
        tracking_id=record.tracking_id if record else None,
        strategy_type=record.strategy_type if record else None,
        universe=record.universe if record else None,
        timeframe=record.timeframe if record else None,
        evidence_refs=evidence_refs,
        raw_entry=entry.model_dump(mode="json"),
    )


def _summary(rows: list[StrategyGraveyardEntryView]) -> StrategyGraveyardSummary:
    reasons: Counter[str] = Counter()
    res: Counter[str] = Counter()
    for row in rows:
        reasons.update(row.failure_reasons)
        res[row.resurrectability] += 1
    return StrategyGraveyardSummary(
        entry_count=len(rows),
        hard_blocked_count=sum(1 for r in rows if r.resurrectability == "HARD_BLOCKED_UNTIL_EVIDENCE"),
        conditional_retry_count=sum(1 for r in rows if r.resurrectability == "CONDITIONAL_RESEARCH_RETRY"),
        duplicate_superseded_count=sum(1 for r in rows if r.resurrectability == "DUPLICATE_SUPERSEDED"),
        operator_review_count=sum(1 for r in rows if r.resurrectability == "OPERATOR_REVIEW_REQUIRED"),
        failure_reason_counts=dict(sorted(reasons.items())),
        resurrectability_counts=dict(sorted(res.items())),
    )


def build_ui_strategy_graveyard_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = strategy_memory_root_directory(repo_root)
    index_path = root / "latest" / "strategy_memory_index.json"
    degraded: list[str] = []
    try:
        records = load_memory_records(repo_root=repo_root)
        entries = load_graveyard_entries(repo_root=repo_root)
    except Exception:
        records = []
        entries = []
        degraded.append("STRATEGY_MEMORY_UNREADABLE")
    if not entries:
        degraded.append("NO_STRATEGY_GRAVEYARD_ENTRIES")
    records_by_strategy = _record_by_strategy(records)
    rows = [_view(e, records_by_strategy.get(e.strategy_id)) for e in entries]
    payload = StrategyGraveyardPayload(scan_root=str(root), index_path=str(index_path), degraded=degraded, summary=_summary(rows), entries=rows)
    return payload.model_dump(mode="json")


__all__ = ["build_ui_strategy_graveyard_latest_payload"]
