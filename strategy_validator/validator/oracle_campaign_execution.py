from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle_strategic_memory import (
    OracleDoctrineAdaptationReport,
    OracleResearchExecutionMemoryReport,
    OracleStrategicMemoryHorizonReport,
)
from strategy_validator.contracts.oracle_strategic_programs import (
    OracleStrategicCampaignExecutionInput,
    OracleStrategicCampaignExecutionItem,
    OracleStrategicCampaignExecutionReport,
    OracleStrategicCampaignExecutionUpdateItem,
    OracleStrategicCampaignReport,
)
from strategy_validator.validator.oracle_campaign_planner import build_oracle_strategic_campaign_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_cadence_feedback import summarize_exact_cadence_feedback, classify_exact_cadence_signal, cadence_operator_action, cadence_recommendation_suffix
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_history_integrity import (
    campaign_friction,
    history_integrity_status,
    integrity_fact,
    integrity_operator_action,
    sealed_history_observation_count,
    unsealed_history_excluded_count,
    preferred_strategic_backing_source,
    preferred_strategic_backing_classification,
)
from strategy_validator.validator.oracle_strategic_artifact_evidence import discover_preferred_strategic_artifact_evidence, strategic_artifact_evidence_support_score, preferred_artifact_evidence_fact


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _sort_items(items: list[OracleStrategicCampaignExecutionItem]) -> list[OracleStrategicCampaignExecutionItem]:
    return sorted(
        items,
        key=lambda item: (
            item.execution_state not in {"ACTIVE", "DRIFTING", "BLOCKED"},
            -item.priority_score,
            -item.progress_score,
            item.campaign_id,
        ),
    )


def _override_map(execution_input: OracleStrategicCampaignExecutionInput | None) -> dict[str, OracleStrategicCampaignExecutionUpdateItem]:
    if execution_input is None:
        return {}
    return {item.campaign_id: item for item in execution_input.items}


def _completed_priority_ids(report: OracleResearchExecutionMemoryReport | None) -> set[str]:
    return set(report.completed_priority_ids) if report is not None else set()


def _deferred_priority_ids(report: OracleResearchExecutionMemoryReport | None) -> set[str]:
    return set(report.deferred_priority_ids) if report is not None else set()


def _execution_items_by_priority(report: OracleResearchExecutionMemoryReport | None) -> dict[str, list]:
    output: dict[str, list] = {}
    if report is None:
        return output
    for item in report.items:
        output.setdefault(item.priority_id, []).append(item)
    return output


def build_oracle_strategic_campaign_execution_report(
    campaign_report: OracleStrategicCampaignReport,
    *,
    execution_input: OracleStrategicCampaignExecutionInput | None = None,
    research_execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    strategic_memory_horizon_report: OracleStrategicMemoryHorizonReport | None = None,
    campaign_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleStrategicCampaignExecutionReport:
    issued_at = now_utc or _utc_now()
    oracle_run_id, input_timestamp_utc, universe_label = assert_matching_strategic_epoch(campaign_report, doctrine_adaptation_report, strategic_memory_horizon_report)
    overrides = _override_map(execution_input)
    completed_priority_ids = _completed_priority_ids(research_execution_memory_report)
    deferred_priority_ids = _deferred_priority_ids(research_execution_memory_report)
    execution_by_priority = _execution_items_by_priority(research_execution_memory_report)

    freeze_recommended = bool(getattr(doctrine_adaptation_report, "freeze_recommended", False))
    drift_state = getattr(strategic_memory_horizon_report, "drift_state", "FIRST_OBSERVATION") if strategic_memory_horizon_report is not None else "FIRST_OBSERVATION"
    integrity_status = history_integrity_status(strategic_memory_horizon_report)
    integrity_friction = campaign_friction(strategic_memory_horizon_report)
    preferred_backing_source = preferred_strategic_backing_source(strategic_memory_horizon_report) or getattr(campaign_report, "preferred_strategic_backing_source", None)
    preferred_backing_classification = preferred_strategic_backing_classification(strategic_memory_horizon_report) or getattr(campaign_report, "preferred_strategic_backing_classification", None)
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()
    campaign_artifact_evidence = discover_preferred_strategic_artifact_evidence(report_path=Path(campaign_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root) if campaign_report_path is not None and Path(campaign_report_path).exists() else None
    campaign_exact_evidence_support_score = strategic_artifact_evidence_support_score(campaign_artifact_evidence)
    execution_memory_exact_support_score = round(float(getattr(research_execution_memory_report, "exact_evidence_support_score", 0.0) or 0.0), 6)
    exact_evidence_support_score = max(campaign_exact_evidence_support_score, execution_memory_exact_support_score)
    cadence = summarize_exact_cadence_feedback(repo_root=resolved_repo_root, search_root=resolved_search_root, window_size=6)
    exact_cadence_signal_classification = classify_exact_cadence_signal(
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
    )
    drift_pressure = {
        "REVERSING": 0.75,
        "VOLATILE": 0.65,
        "SOFTENING": 0.40,
        "STRENGTHENING": 0.10,
        "STABLE": 0.15,
        "FIRST_OBSERVATION": 0.20,
    }.get(drift_state, 0.20)

    items: list[OracleStrategicCampaignExecutionItem] = []
    for index, campaign in enumerate(campaign_report.items):
        override = overrides.get(campaign.campaign_id)
        completed_steps = _unique(list(override.completed_step_ids) if override is not None else [])
        blocked_steps = _unique(list(override.blocked_step_ids) if override is not None else [])
        source_execution_ids: list[str] = []
        auto_completed_steps: list[str] = []
        local_execution_support = execution_memory_exact_support_score
        if research_execution_memory_report is not None:
            if campaign.source_priority_ids:
                for priority_id in campaign.source_priority_ids:
                    matched = execution_by_priority.get(priority_id, [])
                    source_execution_ids.extend(item.execution_id for item in matched)
                    local_execution_support = max(local_execution_support, max((float(getattr(item, "exact_evidence_support_score", 0.0) or 0.0) for item in matched), default=0.0))
                    if priority_id in completed_priority_ids:
                        for step in campaign.steps:
                            if step.step_kind in {"INVESTIGATION", "VALIDATION"} and step.step_id not in completed_steps:
                                auto_completed_steps.append(step.step_id)
            if not campaign.source_priority_ids and campaign.steps and index == 0:
                auto_completed_steps.append(campaign.steps[0].step_id)
        completed_steps = _unique(completed_steps + auto_completed_steps)
        item_exact_support_score = max(campaign_exact_evidence_support_score, local_execution_support)
        pending_steps = [step.step_id for step in campaign.steps if step.step_id not in completed_steps and step.step_id not in blocked_steps]

        completion_ratio = (len(completed_steps) / len(campaign.steps)) if campaign.steps else 0.0
        completed_ratio = (len([priority_id for priority_id in campaign.source_priority_ids if priority_id in completed_priority_ids]) / len(campaign.source_priority_ids)) if campaign.source_priority_ids else completion_ratio
        progress_score = _clamp(0.45 * completion_ratio + 0.25 * completed_ratio + 0.20 * campaign.priority_score + (0.10 if index == 0 else 0.0))
        blocker_score = _clamp(
            (0.60 if blocked_steps else 0.0)
            + (0.35 if any(priority_id in deferred_priority_ids for priority_id in campaign.source_priority_ids) else 0.0)
            + (0.40 if freeze_recommended and campaign.objective_kind in {"OPPORTUNITY_EXPANSION", "COHORT_RECOVERY"} else 0.0)
            + (0.35 * integrity_friction if integrity_status != "SEALED_HISTORY" and campaign.objective_kind in {"OPPORTUNITY_EXPANSION", "THESIS_VALIDATION", "COHORT_RECOVERY"} else 0.0)
        )
        invalidation_score = _clamp(
            (0.85 if freeze_recommended and campaign.objective_kind == "OPPORTUNITY_EXPANSION" else 0.0)
            + (0.75 if campaign_report.baseline_conviction_state == "BROKEN_CONVICTION" and campaign.objective_kind == "OPPORTUNITY_EXPANSION" else 0.0)
            + (0.25 if override is not None and override.execution_state == "INVALIDATED" else 0.0)
            + (0.45 * integrity_friction if integrity_status == "CURRENT_ONLY" and campaign.objective_kind in {"OPPORTUNITY_EXPANSION", "THESIS_VALIDATION"} else 0.0)
            + (0.25 * integrity_friction if integrity_status == "MIXED_HISTORY" and campaign.objective_kind == "OPPORTUNITY_EXPANSION" else 0.0)
            - (0.12 * item_exact_support_score if campaign.objective_kind in {"DOCTRINE_STABILIZATION", "THESIS_VALIDATION", "OPPORTUNITY_EXPANSION"} else 0.0)
        )
        blocker_score = _clamp(max(0.0, blocker_score - (0.10 * item_exact_support_score if campaign.objective_kind in {"DOCTRINE_STABILIZATION", "THESIS_VALIDATION", "OPPORTUNITY_EXPANSION"} else 0.0)))
        drift_score = _clamp(
            drift_pressure
            + (0.20 if campaign_report.baseline_fragility_score >= 0.60 else 0.0)
            + (0.15 if campaign.objective_kind in {"CONVICTION_REPAIR", "DOCTRINE_STABILIZATION"} and drift_state in {"REVERSING", "VOLATILE"} else 0.0)
            + (0.18 * integrity_friction if integrity_status != "SEALED_HISTORY" else 0.0)
        )

        if override is not None:
            execution_state = override.execution_state
        elif invalidation_score >= 0.75:
            execution_state = "INVALIDATED"
        elif blocker_score >= 0.70:
            execution_state = "BLOCKED"
        elif progress_score >= 0.95 and not pending_steps:
            execution_state = "COMPLETED"
        elif drift_score >= 0.70 and progress_score >= 0.20:
            execution_state = "DRIFTING"
        elif index == 0 or progress_score >= 0.20 or completed_steps:
            execution_state = "ACTIVE"
        else:
            execution_state = "QUEUED"

        if execution_state == "COMPLETED":
            completed_steps = _unique(completed_steps + [step.step_id for step in campaign.steps])
            pending_steps = []
            progress_score = max(progress_score, 1.0)
        evidence = _unique(
            campaign.evidence
            + ([override.note] if override is not None and override.note else [])
            + list(override.evidence if override is not None else [])
            + [
                f"campaign_priority:{campaign.priority_score:.2f}",
                f"campaign_baseline_conviction:{campaign_report.baseline_conviction_state}:{campaign_report.baseline_conviction_score:.2f}",
                f"campaign_baseline_fragility:{campaign_report.baseline_fragility_score:.2f}",
                f"campaign_drift:{drift_state}:{drift_score:.2f}",
                integrity_fact(strategic_memory_horizon_report),
                f"integrity_friction={integrity_friction:.2f}",
                f"execution_memory_exact_evidence_support={local_execution_support:.2f}",
                *preferred_artifact_evidence_fact("campaign", campaign_artifact_evidence),
            ]
            + ([f"freeze_recommended:{freeze_recommended}"] if doctrine_adaptation_report is not None else [])
            + [f"execution:{execution_id}" for execution_id in source_execution_ids]
            + [
                f"exact_cadence_signal_classification={exact_cadence_signal_classification}",
                f"exact_feedback_confirmation_count={cadence.exact_feedback_confirmation_count}",
                f"exact_feedback_relief_count={cadence.exact_feedback_relief_count}",
            ]
        )[:10]
        if override is not None and override.recommended_next_step:
            recommended_next_step = override.recommended_next_step
        elif blocked_steps:
            recommended_next_step = f"Unblock {blocked_steps[0]} before advancing {campaign.campaign_id}."
        elif integrity_status != "SEALED_HISTORY" and campaign.objective_kind in {"OPPORTUNITY_EXPANSION", "THESIS_VALIDATION"} and item_exact_support_score < 0.85:
            recommended_next_step = "Seal and verify prior strategic stack history before advancing this campaign beyond the current evidence boundary."
        elif item_exact_support_score >= 0.85 and campaign.objective_kind in {"OPPORTUNITY_EXPANSION", "THESIS_VALIDATION", "DOCTRINE_STABILIZATION"}:
            next_step = next((step for step in campaign.steps if step.step_id == pending_steps[0]), None) if pending_steps else None
            recommended_next_step = (next_step.summary_line if next_step is not None else campaign.recommended_campaign) + " Execute against the exact sealed campaign subject while sealing broader history in parallel."
        elif pending_steps:
            next_step = next((step for step in campaign.steps if step.step_id == pending_steps[0]), None)
            recommended_next_step = next_step.summary_line if next_step is not None else campaign.recommended_campaign
        else:
            recommended_next_step = campaign.recommended_campaign
        recommended_next_step += cadence_recommendation_suffix(
            exact_cadence_signal_classification=exact_cadence_signal_classification,
            exact_evidence_support_score=item_exact_support_score,
        )
        summary_line = (
            f"{campaign.title} is {execution_state.lower()} with progress {progress_score:.2f}, "
            f"blocker {blocker_score:.2f}, drift {drift_score:.2f}, invalidation {invalidation_score:.2f}, "
            f"and history integrity {integrity_status.lower().replace('_', ' ')}."
        )
        items.append(
            OracleStrategicCampaignExecutionItem(
                campaign_id=campaign.campaign_id,
                objective_kind=campaign.objective_kind,
                execution_state=execution_state,
                exact_evidence_support_score=round(item_exact_support_score, 6),
                exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
                exact_feedback_relief_count=cadence.exact_feedback_relief_count,
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                priority_score=round(campaign.priority_score, 6),
                progress_score=round(progress_score, 6),
                blocker_score=round(blocker_score, 6),
                drift_score=round(drift_score, 6),
                invalidation_score=round(invalidation_score, 6),
                operator_friction_score=round(integrity_friction, 6),
                title=campaign.title,
                summary_line=summary_line,
                completed_step_ids=completed_steps,
                pending_step_ids=pending_steps,
                blocked_step_ids=blocked_steps,
                source_priority_ids=campaign.source_priority_ids,
                source_execution_ids=_unique(source_execution_ids),
                related_strategy_ids=campaign.related_strategy_ids,
                evidence=evidence,
                recommended_next_step=recommended_next_step,
            )
        )

    items = _sort_items(items)
    active_campaign_ids = [item.campaign_id for item in items if item.execution_state == "ACTIVE"]
    blocked_campaign_ids = [item.campaign_id for item in items if item.execution_state == "BLOCKED"]
    drifting_campaign_ids = [item.campaign_id for item in items if item.execution_state == "DRIFTING"]
    completed_campaign_ids = [item.campaign_id for item in items if item.execution_state == "COMPLETED"]
    invalidated_campaign_ids = [item.campaign_id for item in items if item.execution_state == "INVALIDATED"]
    operator_actions = _unique(
        [cadence_operator_action(
                exact_cadence_signal_classification=exact_cadence_signal_classification,
                exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
                exact_feedback_relief_count=cadence.exact_feedback_relief_count,
            ), integrity_operator_action(strategic_memory_horizon_report)]
        + [item.recommended_next_step for item in items[:5]]
        + [
            "Track campaign state transitions explicitly so multi-step plans remain replayable across strategic cycles.",
            "Prefer one active conviction-repair or doctrine-stabilization campaign before launching parallel opportunity-expansion campaigns.",
        ]
    )[:8]
    return OracleStrategicCampaignExecutionReport(
        generated_at_utc=issued_at,
        universe_label=universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=campaign_report.dominant_regime,
        strategic_posture=campaign_report.strategic_posture,
        baseline_conviction_state=campaign_report.baseline_conviction_state,
        baseline_conviction_score=campaign_report.baseline_conviction_score,
        baseline_fragility_score=campaign_report.baseline_fragility_score,
        history_integrity_status=integrity_status,
        sealed_history_observation_count=sealed_history_observation_count(strategic_memory_horizon_report),
        unsealed_history_excluded_count=unsealed_history_excluded_count(strategic_memory_horizon_report),
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_evidence_support_score=round(max((item.exact_evidence_support_score for item in items), default=exact_evidence_support_score), 6),
        exact_feedback_confirmation_count=cadence.exact_feedback_confirmation_count,
        exact_feedback_relief_count=cadence.exact_feedback_relief_count,
        exact_cadence_signal_classification=exact_cadence_signal_classification,
        integrity_operator_friction_score=round(integrity_friction, 6),
        summary_line=(
            f"Tracked {len(items)} strategic campaigns for {campaign_report.universe_label}; "
            f"active={len(active_campaign_ids)}, blocked={len(blocked_campaign_ids)}, drifting={len(drifting_campaign_ids)}, "
            f"completed={len(completed_campaign_ids)}, invalidated={len(invalidated_campaign_ids)}, "
            f"history_integrity={integrity_status}, cadence={exact_cadence_signal_classification}, "
            f"exact_confirm={cadence.exact_feedback_confirmation_count}, exact_relief={cadence.exact_feedback_relief_count}."
        ),
        active_campaign_ids=active_campaign_ids,
        blocked_campaign_ids=blocked_campaign_ids,
        drifting_campaign_ids=drifting_campaign_ids,
        completed_campaign_ids=completed_campaign_ids,
        invalidated_campaign_ids=invalidated_campaign_ids,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_strategic_campaign_execution_markdown(report: OracleStrategicCampaignExecutionReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        completed = ", ".join(item.completed_step_ids) or "none"
        pending = ", ".join(item.pending_step_ids) or "none"
        blocked = ", ".join(item.blocked_step_ids) or "none"
        blocks.append(
            f"## {item.title}\n\n"
            f"- Campaign ID: {item.campaign_id}\n"
            f"- Objective kind: {item.objective_kind}\n"
            f"- Execution state: {item.execution_state}\n"
            f"- Priority score: {item.priority_score:.2f}\n"
            f"- Progress score: {item.progress_score:.2f}\n"
            f"- Blocker score: {item.blocker_score:.2f}\n"
            f"- Drift score: {item.drift_score:.2f}\n"
            f"- Invalidation score: {item.invalidation_score:.2f}\n"
            f"- Summary: {item.summary_line}\n"
            f"- Completed steps: {completed}\n"
            f"- Pending steps: {pending}\n"
            f"- Blocked steps: {blocked}\n\n"
            f"### Evidence\n\n{evidence}\n\n"
            f"### Recommended next step\n\n- {item.recommended_next_step}"
        )
    actions = "\n".join(f"- {entry}" for entry in report.operator_actions) or "- none"
    block_lines = "\n\n".join(blocks)
    return f"""# ORACLE STRATEGIC CAMPAIGN EXECUTION REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- History integrity: {report.history_integrity_status}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact cadence signal: {report.exact_cadence_signal_classification}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief: {report.exact_feedback_relief_count}
- Exact evidence support: {report.exact_evidence_support_score:.2f}

## Summary

{report.summary_line}

{block_lines}

## Operator actions

{actions}
"""


def load_strategic_campaign_execution_input(path: Path) -> OracleStrategicCampaignExecutionInput:
    return OracleStrategicCampaignExecutionInput.model_validate(json.loads(path.read_text(encoding="utf-8")))


def load_strategic_campaign_execution_report(path: Path) -> OracleStrategicCampaignExecutionReport:
    return OracleStrategicCampaignExecutionReport.model_validate(json.loads(path.read_text(encoding="utf-8")))
