from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleInvestigationOutcomeInput,
    OracleResearchExecutionMemoryItem,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
)
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_strategic_artifact_evidence import (
    discover_preferred_strategic_artifact_evidence,
    preferred_artifact_evidence_fact,
    strategic_artifact_evidence_support_score,
)


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _match_priority(report: OracleResearchPriorityReport, priority_id: str):
    return next((item for item in report.items if item.priority_id == priority_id), None)


def build_oracle_research_execution_memory_report(
    priority_report: OracleResearchPriorityReport,
    outcome_input: OracleInvestigationOutcomeInput,
    *,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleResearchExecutionMemoryReport:
    issued_at = now_utc or _utc_now()
    oracle_run_id, input_timestamp_utc, universe_label = assert_matching_strategic_epoch(priority_report)
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or resolved_repo_root / "docs" / "artifacts").resolve()
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(doctrine_adaptation_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(research_priority_report_path),
        repo_root=resolved_repo_root,
        search_root=resolved_search_root,
    ) if research_priority_report_path is not None and Path(research_priority_report_path).exists() else None
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    preferred_backing_source = (
        (doctrine_artifact_evidence or {}).get("preferred_strategic_backing_source")
        or (research_artifact_evidence or {}).get("preferred_strategic_backing_source")
        or priority_report.preferred_strategic_backing_source
    )
    preferred_backing_classification = (
        (doctrine_artifact_evidence or {}).get("preferred_strategic_backing_classification")
        or (research_artifact_evidence or {}).get("preferred_strategic_backing_classification")
        or priority_report.preferred_strategic_backing_classification
    )
    report_support = max(doctrine_exact_support, research_exact_support)
    items: list[OracleResearchExecutionMemoryItem] = []
    for outcome in outcome_input.items:
        priority = _match_priority(priority_report, outcome.priority_id)
        if priority is None:
            continue
        related_strategy_ids = outcome.related_strategy_ids or priority.related_strategy_ids
        if priority.priority_kind == "DOCTRINE_REVIEW":
            exact_support = doctrine_exact_support or report_support
        elif priority.priority_kind in {"STRATEGY_VALIDATION", "THESIS_REVIEW"}:
            exact_support = research_exact_support or report_support
        else:
            exact_support = max(report_support * 0.65, research_exact_support * 0.5, doctrine_exact_support * 0.5)
        summary = (
            f"{outcome.execution_state.title()} {priority.priority_kind.lower()} {priority.priority_id} "
            f"with disposition {(outcome.outcome_disposition or 'none').lower()}, confidence impact {outcome.confidence_impact:+.2f}, "
            f"and exact evidence support {exact_support:.2f}."
        )
        items.append(
            OracleResearchExecutionMemoryItem(
                execution_id=outcome.outcome_id,
                priority_id=priority.priority_id,
                priority_kind=priority.priority_kind,
                execution_state=outcome.execution_state,
                outcome_disposition=outcome.outcome_disposition,
                thesis_effect=outcome.thesis_effect,
                doctrine_effect=outcome.doctrine_effect,
                cohort_effect=outcome.cohort_effect,
                exact_evidence_support_score=round(exact_support, 6),
                confidence_impact=round(outcome.confidence_impact, 6),
                urgency_impact=round(outcome.urgency_impact, 6),
                related_strategy_ids=related_strategy_ids[:4],
                thesis_ids=outcome.thesis_ids[:6],
                doctrine_clause_ids=outcome.doctrine_clause_ids[:6],
                finding_summary=outcome.finding_summary,
                evidence=_unique(
                    outcome.evidence
                    + preferred_artifact_evidence_fact("doctrine", doctrine_artifact_evidence)
                    + preferred_artifact_evidence_fact("research", research_artifact_evidence)
                    + priority.evidence
                )[:12],
                next_action=(
                    outcome.next_action
                    + (" Advance with the exact sealed supporting subject while sealing broader history in parallel." if exact_support >= 0.85 else "")
                ),
                summary_line=summary,
            )
        )
    items.sort(key=lambda item: (item.execution_state != 'COMPLETED', item.outcome_disposition != 'ESCALATED', -abs(item.confidence_impact), item.priority_id))
    completed = [item.priority_id for item in items if item.execution_state == 'COMPLETED']
    deferred = [item.priority_id for item in items if item.execution_state == 'DEFERRED']
    escalated = [item.priority_id for item in items if item.outcome_disposition == 'ESCALATED' or item.doctrine_effect == 'FREEZE_CANDIDATE']
    operator_actions = _unique([item.next_action for item in items] + [
        'Persist investigation outcomes beside thesis/cohort/doctrine reports so strategic learning remains replayable.',
        'Prefer promoting campaign changes from investigation outcomes when the exact supporting doctrine/research subjects are sealed.',
    ])[:8]
    summary_line = (
        f"Tracked {len(items)} investigation outcomes for {priority_report.universe_label}; "
        f"completed={len(completed)}, deferred={len(deferred)}, escalated={len(escalated)}, exact_evidence_support={report_support:.2f}."
    )
    return OracleResearchExecutionMemoryReport(
        generated_at_utc=issued_at,
        universe_label=universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_evidence_support_score=round(report_support, 6),
        summary_line=summary_line,
        completed_priority_ids=completed,
        deferred_priority_ids=deferred,
        escalated_priority_ids=escalated,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_research_execution_memory_markdown(report: OracleResearchExecutionMemoryReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        evidence = "\n".join(f"- {entry}" for entry in item.evidence) or "- none"
        strategies = ", ".join(item.related_strategy_ids) if item.related_strategy_ids else 'n/a'
        blocks.append(
            f"## {item.priority_id}\n\n"
            f"- Priority kind: {item.priority_kind}\n"
            f"- Execution state: {item.execution_state}\n"
            f"- Outcome disposition: {item.outcome_disposition or 'NONE'}\n"
            f"- Thesis effect: {item.thesis_effect}\n"
            f"- Doctrine effect: {item.doctrine_effect}\n"
            f"- Cohort effect: {item.cohort_effect}\n"
            f"- Related strategies: {strategies}\n"
            f"- Finding: {item.finding_summary}\n"
            f"- Summary: {item.summary_line}\n\n"
            f"### Evidence\n\n{evidence}\n\n"
            f"### Next action\n\n- {item.next_action}"
        )
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or '- none'
    return f"""# ORACLE RESEARCH EXECUTION MEMORY REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}

## Summary

{report.summary_line}

{"\n\n".join(blocks)}

## Operator actions

{actions}
"""


def load_investigation_outcome_input(path: Path) -> OracleInvestigationOutcomeInput:
    return OracleInvestigationOutcomeInput.model_validate(json.loads(path.read_text(encoding='utf-8')))


def load_research_execution_memory_report(path: Path) -> OracleResearchExecutionMemoryReport:
    return OracleResearchExecutionMemoryReport.model_validate(json.loads(path.read_text(encoding='utf-8')))
