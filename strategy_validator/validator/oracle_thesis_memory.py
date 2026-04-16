from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from strategy_validator.contracts.oracle import (
    OracleAdvisoryInput,
    OracleDoctrineAdaptationReport,
    OracleRegimeTransitionSignalReport,
    OracleResearchExecutionMemoryReport,
    OracleResearchPriorityReport,
    OracleStrategicFusionReport,
    OracleThesisMemoryItem,
    OracleThesisMemoryReport,
    StrategyHealthPosteriorReport,
)
from strategy_validator.validator.oracle_signal_fusion import build_oracle_strategic_fusion_report
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.strategy_health_posterior import build_strategy_health_posterior_report
from strategy_validator.validator.oracle_run_identity import assert_matching_strategic_epoch
from strategy_validator.validator.oracle_strategic_artifact_evidence import (
    discover_preferred_strategic_artifact_evidence,
    preferred_artifact_evidence_fact,
    strategic_artifact_evidence_support_score,
)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _unique(items: list[str]) -> list[str]:
    output: list[str] = []
    for item in items:
        normalized = str(item).strip()
        if normalized and normalized not in output:
            output.append(normalized)
    return output


def _state_from_score(score: float) -> str:
    if score >= 0.72:
        return "SUPPORTIVE"
    if score >= 0.50:
        return "NEUTRAL"
    if score >= 0.34:
        return "CAUTIONARY"
    if score >= 0.16:
        return "AT_RISK"
    return "BROKEN"


def _evolution_from_delta(previous_state: str | None, previous_score: float | None, current_state: str, current_score: float) -> str:
    if previous_state is None or previous_score is None:
        return "EMERGING"
    if previous_state != current_state and {previous_state, current_state} & {"SUPPORTIVE", "BROKEN", "AT_RISK"}:
        return "REVERSING"
    delta = current_score - previous_score
    if delta >= 0.07:
        return "STRENGTHENING"
    if delta <= -0.07:
        return "WEAKENING"
    return "STABLE"


def _find_previous(previous_report: OracleThesisMemoryReport | None, thesis_id: str) -> OracleThesisMemoryItem | None:
    if previous_report is None:
        return None
    for item in previous_report.items:
        if item.thesis_id == thesis_id:
            return item
    return None


def _regime_item(
    fusion: OracleStrategicFusionReport,
    previous_report: OracleThesisMemoryReport | None,
    transition: OracleRegimeTransitionSignalReport | None,
) -> OracleThesisMemoryItem:
    thesis_id = f"regime:{fusion.dominant_regime.lower()}"
    score = _clamp(0.60 * fusion.regime_confidence + 0.20 * fusion.opportunity_score + 0.20 * (1.0 - fusion.caution_score))
    current_state = _state_from_score(score)
    previous = _find_previous(previous_report, thesis_id)
    evidence_for = [
        f"regime_confidence={fusion.regime_confidence:.2f}",
        f"opportunity_score={fusion.opportunity_score:.2f}",
        f"strategic_posture={fusion.strategic_posture}",
    ]
    evidence_against = [
        f"caution_score={fusion.caution_score:.2f}",
        f"epistemic_status={fusion.epistemic_status}",
    ]
    if transition is not None:
        evidence_against.extend(transition.drivers[:2])
    return OracleThesisMemoryItem(
        thesis_id=thesis_id,
        thesis_label=f"{fusion.dominant_regime.replace('_', ' ').title()} persistence thesis",
        thesis_kind="REGIME",
        current_state=current_state,
        evolution_state=_evolution_from_delta(previous.current_state if previous else None, previous.confidence_score if previous else None, current_state, score),
        confidence_score=round(score, 6),
        previous_confidence_score=(previous.confidence_score if previous else None),
        evidence_for=_unique(evidence_for),
        evidence_against=_unique(evidence_against),
        recommended_research_action="Test whether the current regime thesis remains persistent across the next sensor refresh before broadening conviction.",
        summary_line=f"{fusion.dominant_regime} thesis is {current_state.lower()} with confidence {score:.2f}.",
    )


def _liquidity_item(
    payload: OracleAdvisoryInput,
    fusion: OracleStrategicFusionReport,
    previous_report: OracleThesisMemoryReport | None,
) -> OracleThesisMemoryItem:
    micro = payload.sensors.microstructure
    score = _clamp(1.0 - (0.55 * micro.liquidity_thinning_score + 0.25 * micro.vpin + 0.20 * max(micro.spread_variance_zscore, 0.0) / 3.0))
    current_state = _state_from_score(score)
    previous = _find_previous(previous_report, 'liquidity:resilience')
    return OracleThesisMemoryItem(
        thesis_id='liquidity:resilience',
        thesis_label='Liquidity resilience thesis',
        thesis_kind='LIQUIDITY',
        current_state=current_state,
        evolution_state=_evolution_from_delta(previous.current_state if previous else None, previous.confidence_score if previous else None, current_state, score),
        confidence_score=round(score, 6),
        previous_confidence_score=(previous.confidence_score if previous else None),
        evidence_for=_unique([
            f"liquidity_thinning_score={micro.liquidity_thinning_score:.2f}",
            f"vpin={micro.vpin:.2f}",
            f"caution_score={fusion.caution_score:.2f}",
        ]),
        evidence_against=_unique([
            *(fusion.caution_factors[:2]),
            *( [f"spread_variance_zscore={micro.spread_variance_zscore:.2f}"] if micro.spread_variance_zscore > 0 else []),
        ]),
        recommended_research_action='Monitor whether market depth and spread conditions confirm or invalidate this liquidity thesis.',
        summary_line=f'Liquidity resilience thesis is {current_state.lower()} with confidence {score:.2f}.',
    )


def _doctrine_item(
    fusion: OracleStrategicFusionReport,
    previous_report: OracleThesisMemoryReport | None,
) -> OracleThesisMemoryItem:
    score = _clamp(1.0 - fusion.doctrine_stress_score)
    current_state = _state_from_score(score)
    previous = _find_previous(previous_report, 'doctrine:coherence')
    return OracleThesisMemoryItem(
        thesis_id='doctrine:coherence',
        thesis_label='Doctrine coherence thesis',
        thesis_kind='DOCTRINE',
        current_state=current_state,
        evolution_state=_evolution_from_delta(previous.current_state if previous else None, previous.confidence_score if previous else None, current_state, score),
        confidence_score=round(score, 6),
        previous_confidence_score=(previous.confidence_score if previous else None),
        evidence_for=[f'doctrine_stress_score={fusion.doctrine_stress_score:.2f}'],
        evidence_against=_unique(fusion.doctrine_pressure_points[:4]),
        recommended_research_action='Trace which doctrine clauses are under the most pressure before changing long-lived research assumptions.',
        summary_line=f'Doctrine coherence thesis is {current_state.lower()} with confidence {score:.2f}.',
    )


def _strategy_items(
    posterior: StrategyHealthPosteriorReport,
    previous_report: OracleThesisMemoryReport | None,
) -> list[OracleThesisMemoryItem]:
    candidates = sorted(
        posterior.strategies,
        key=lambda item: (abs(item.confidence_delta), item.posterior_edge_confidence),
        reverse=True,
    )[:3]
    items: list[OracleThesisMemoryItem] = []
    for state in candidates:
        thesis_id = f"strategy:{state.strategy_id}"
        score = state.posterior_edge_confidence
        current_state = _state_from_score(score)
        previous = _find_previous(previous_report, thesis_id)
        items.append(
            OracleThesisMemoryItem(
                thesis_id=thesis_id,
                thesis_label=f"{state.strategy_id} edge thesis",
                thesis_kind='STRATEGY',
                current_state=current_state,
                evolution_state=_evolution_from_delta(previous.current_state if previous else None, previous.confidence_score if previous else None, current_state, score),
                confidence_score=round(score, 6),
                previous_confidence_score=(previous.confidence_score if previous else None),
                strategy_ids=[state.strategy_id],
                evidence_for=_unique([reason for reason in state.reasons if 'exceeds' in reason or 'supportive' in reason][:3]),
                evidence_against=_unique([reason for reason in state.reasons if reason not in [r for r in state.reasons if 'exceeds' in r or 'supportive' in r]][:3]),
                recommended_research_action=(
                    'Re-test this strategy against the current regime before scaling research confidence.'
                    if state.recommended_action == 'MAINTAIN'
                    else f'{state.recommended_action.lower().capitalize()} this strategy in research review until posterior stability improves.'
                ),
                summary_line=f"{state.strategy_id} edge thesis is {current_state.lower()} at posterior {score:.2f} with {state.recommended_action.lower()} recommendation.",
            )
        )
    return items



def _apply_execution_memory(items: list[OracleThesisMemoryItem], previous_report: OracleThesisMemoryReport | None, execution_memory_report: OracleResearchExecutionMemoryReport | None) -> list[OracleThesisMemoryItem]:
    if execution_memory_report is None or not execution_memory_report.items:
        return items
    adjusted: list[OracleThesisMemoryItem] = []
    for item in items:
        relevant = [
            outcome for outcome in execution_memory_report.items
            if item.thesis_id in outcome.thesis_ids or any(strategy_id in outcome.related_strategy_ids for strategy_id in item.strategy_ids)
        ]
        if not relevant:
            adjusted.append(item)
            continue
        delta = sum(outcome.confidence_impact for outcome in relevant) * 0.20
        for outcome in relevant:
            if outcome.thesis_effect == 'STRENGTHENS':
                delta += 0.06
            elif outcome.thesis_effect == 'WEAKENS':
                delta -= 0.06
            elif outcome.thesis_effect == 'REVIEW_REQUIRED':
                delta -= 0.03
            if outcome.execution_state == 'COMPLETED' and outcome.outcome_disposition == 'CONFIRMED':
                delta += 0.02 if outcome.thesis_effect == 'STRENGTHENS' else -0.02 if outcome.thesis_effect == 'WEAKENS' else 0.0
        score = _clamp(item.confidence_score + delta)
        current_state = _state_from_score(score)
        previous_item = _find_previous(previous_report, item.thesis_id)
        evidence_for = list(item.evidence_for)
        evidence_against = list(item.evidence_against)
        for outcome in relevant:
            marker = f"investigation:{outcome.priority_id}:{outcome.execution_state}:{outcome.outcome_disposition or 'NONE'}"
            if outcome.thesis_effect == 'STRENGTHENS':
                evidence_for.append(marker)
                evidence_for.extend(outcome.evidence[:1])
            else:
                evidence_against.append(marker)
                evidence_against.extend(outcome.evidence[:1])
        adjusted.append(item.model_copy(update={
            'current_state': current_state,
            'evolution_state': _evolution_from_delta(previous_item.current_state if previous_item else None, previous_item.confidence_score if previous_item else None, current_state, score),
            'confidence_score': round(score, 6),
            'evidence_for': _unique(evidence_for),
            'evidence_against': _unique(evidence_against),
            'summary_line': f"{item.thesis_label} is {current_state.lower()} with confidence {score:.2f} after {len(relevant)} investigation outcome(s).",
            'recommended_research_action': relevant[0].next_action if relevant else item.recommended_research_action,
        }))
    return adjusted

def build_oracle_thesis_memory_report(
    payload: OracleAdvisoryInput,
    fusion_report: OracleStrategicFusionReport | None = None,
    posterior_report: StrategyHealthPosteriorReport | None = None,
    transition_report: OracleRegimeTransitionSignalReport | None = None,
    previous_report: OracleThesisMemoryReport | None = None,
    execution_memory_report: OracleResearchExecutionMemoryReport | None = None,
    doctrine_adaptation_report: OracleDoctrineAdaptationReport | None = None,
    research_priority_report: OracleResearchPriorityReport | None = None,
    doctrine_adaptation_report_path: Path | None = None,
    research_priority_report_path: Path | None = None,
    repo_root: Path | None = None,
    search_root: Path | None = None,
    now_utc: datetime | None = None,
) -> OracleThesisMemoryReport:
    issued_at = now_utc or _utc_now()
    fusion = fusion_report or build_oracle_strategic_fusion_report(payload, now_utc=issued_at)
    posterior = posterior_report or build_strategy_health_posterior_report(payload, fusion, now_utc=issued_at)
    oracle_run_id, input_timestamp_utc, _ = assert_matching_strategic_epoch(fusion, posterior, transition_report)
    resolved_repo_root = (repo_root or Path.cwd()).resolve()
    resolved_search_root = (search_root or resolved_repo_root).resolve()
    doctrine_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(doctrine_adaptation_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root
    ) if doctrine_adaptation_report_path is not None and Path(doctrine_adaptation_report_path).exists() else None
    research_artifact_evidence = discover_preferred_strategic_artifact_evidence(
        report_path=Path(research_priority_report_path), repo_root=resolved_repo_root, search_root=resolved_search_root
    ) if research_priority_report_path is not None and Path(research_priority_report_path).exists() else None
    doctrine_exact_support = strategic_artifact_evidence_support_score(doctrine_artifact_evidence)
    research_exact_support = strategic_artifact_evidence_support_score(research_artifact_evidence)
    exact_evidence_support_score = max(doctrine_exact_support, research_exact_support)
    preferred_backing_source = None
    preferred_backing_classification = None
    if doctrine_artifact_evidence is not None and doctrine_exact_support >= research_exact_support:
        preferred_backing_source = doctrine_artifact_evidence.get("preferred_strategic_backing_source") or "strategic_artifact_evidence_manifest"
        preferred_backing_classification = doctrine_artifact_evidence.get("preferred_strategic_backing_classification") or None
    elif research_artifact_evidence is not None:
        preferred_backing_source = research_artifact_evidence.get("preferred_strategic_backing_source") or "strategic_artifact_evidence_manifest"
        preferred_backing_classification = research_artifact_evidence.get("preferred_strategic_backing_classification") or None
    elif doctrine_adaptation_report is not None:
        preferred_backing_source = doctrine_adaptation_report.preferred_strategic_backing_source
        preferred_backing_classification = doctrine_adaptation_report.preferred_strategic_backing_classification
    elif research_priority_report is not None:
        preferred_backing_source = research_priority_report.preferred_strategic_backing_source
        preferred_backing_classification = research_priority_report.preferred_strategic_backing_classification
    items = [
        _regime_item(fusion, previous_report, transition_report),
        _liquidity_item(payload, fusion, previous_report),
        _doctrine_item(fusion, previous_report),
        *_strategy_items(posterior, previous_report),
    ]
    items = _apply_execution_memory(items, previous_report, execution_memory_report)
    enriched_items: list[OracleThesisMemoryItem] = []
    for item in items:
        support = 0.0
        evidence_for = list(item.evidence_for)
        evidence_against = list(item.evidence_against)
        confidence = item.confidence_score
        summary_line = item.summary_line
        if item.thesis_kind == "DOCTRINE":
            support = doctrine_exact_support
            evidence_for.extend(preferred_artifact_evidence_fact("thesis_support", doctrine_artifact_evidence))
            if support > 0:
                confidence = _clamp(confidence + 0.06 * support)
        elif item.thesis_kind == "STRATEGY":
            support = research_exact_support
            evidence_for.extend(preferred_artifact_evidence_fact("thesis_support", research_artifact_evidence))
            if support > 0:
                confidence = _clamp(confidence + 0.05 * support)
        else:
            support = round(max(doctrine_exact_support, research_exact_support) * 0.35, 6)
            if support > 0:
                evidence_for.extend(preferred_artifact_evidence_fact("thesis_support", doctrine_artifact_evidence if doctrine_exact_support >= research_exact_support else research_artifact_evidence))
                confidence = _clamp(confidence + 0.02 * support)
        if support > 0:
            summary_line = f"{item.summary_line.rstrip('.')} with exact support {support:.2f}."
        enriched_items.append(item.model_copy(update={
            "exact_evidence_support_score": round(support, 6),
            "confidence_score": round(confidence, 6),
            "evidence_for": _unique(evidence_for),
            "evidence_against": _unique(evidence_against),
            "summary_line": summary_line,
        }))
    items = enriched_items
    strengthening = [item.thesis_id for item in items if item.evolution_state in {'EMERGING', 'STRENGTHENING'}]
    weakening = [item.thesis_id for item in items if item.evolution_state in {'WEAKENING', 'REVERSING'} or item.current_state in {'AT_RISK', 'BROKEN'}]
    operator_actions = _unique([
        item.recommended_research_action for item in items
    ] + [
        'Persist this thesis memory report beside the strategic briefing so belief shifts stay replayable over time.',
    ])[:8]
    summary_line = (
        f"Tracked {len(items)} strategic theses with {len(strengthening)} strengthening/emerging and {len(weakening)} weakening/at-risk lines of belief."
    )
    return OracleThesisMemoryReport(
        generated_at_utc=issued_at,
        universe_label=payload.universe_label,
        oracle_run_id=oracle_run_id,
        input_timestamp_utc=input_timestamp_utc,
        dominant_regime=fusion.dominant_regime,
        strategic_posture=fusion.strategic_posture,
        preferred_strategic_backing_source=preferred_backing_source,
        preferred_strategic_backing_classification=preferred_backing_classification,
        exact_evidence_support_score=round(exact_evidence_support_score, 6),
        summary_line=summary_line,
        strengthening_thesis_ids=strengthening,
        weakening_thesis_ids=weakening,
        items=items,
        operator_actions=operator_actions,
    )


def render_oracle_thesis_memory_markdown(report: OracleThesisMemoryReport) -> str:
    blocks: list[str] = []
    for item in report.items:
        evidence_for = "\n".join(f"- {entry}" for entry in item.evidence_for) or "- none"
        evidence_against = "\n".join(f"- {entry}" for entry in item.evidence_against) or "- none"
        blocks.append(
            f"## {item.thesis_label}\n\n"
            f"- Thesis ID: {item.thesis_id}\n"
            f"- Kind: {item.thesis_kind}\n"
            f"- Current state: {item.current_state}\n"
            f"- Evolution state: {item.evolution_state}\n"
            f"- Confidence score: {item.confidence_score:.2f}\n"
            f"- Summary: {item.summary_line}\n\n"
            f"### Evidence for\n\n{evidence_for}\n\n"
            f"### Evidence against\n\n{evidence_against}\n\n"
            f"### Recommended research action\n\n- {item.recommended_research_action}"
        )
    actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE THESIS MEMORY REPORT

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Universe: {report.universe_label}
- Dominant regime: {report.dominant_regime}
- Strategic posture: {report.strategic_posture}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or 'none'}
- Preferred strategic backing classification: {report.preferred_strategic_backing_classification or 'none'}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}

## Summary

{report.summary_line}

{"\n\n".join(blocks)}

## Operator actions

{actions}
"""


def load_thesis_memory_report(path: Path) -> OracleThesisMemoryReport:
    return OracleThesisMemoryReport.model_validate(json.loads(path.read_text(encoding='utf-8')))
