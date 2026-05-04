from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.contracts.oracle_operator_reports import (
    OracleExplanationNode,
    OracleTrustExplanationReport,
)
from strategy_validator.validator.oracle_transition_common import _utc_now
from strategy_validator.validator.oracle_trust import (
    infer_repo_root_from_artifact_path,
    maybe_verify_oracle_lineage,
    trust_banner_for_constitutional_gate,
    trust_banner_for_derived_view,
    trust_banner_for_event_checkpoint,
    trust_banner_for_lineage_verification,
)




def _strategic_backing_facts(subject: Any) -> list[str]:
    facts: list[str] = []
    source = getattr(subject, "preferred_strategic_backing_source", None)
    classification = getattr(subject, "preferred_strategic_backing_classification", None)
    if source:
        facts.append(f"preferred_strategic_backing_source={source}")
    if classification:
        facts.append(f"preferred_strategic_backing_classification={classification}")
    exact_support = getattr(subject, "exact_evidence_support_score", None)
    if exact_support is not None:
        facts.append(f"exact_evidence_support_score={float(exact_support):.2f}")
    exact_confirm = getattr(subject, "exact_feedback_confirmation_count", None)
    if exact_confirm is not None:
        facts.append(f"exact_feedback_confirmation_count={int(exact_confirm)}")
    exact_relief = getattr(subject, "exact_feedback_relief_count", None)
    if exact_relief is not None:
        facts.append(f"exact_feedback_relief_count={int(exact_relief)}")
    count = getattr(subject, "preferred_strategic_stack_evidence_count", None)
    if count is None:
        count = getattr(subject, "strategic_stack_evidence_count", None)
    if count is not None:
        facts.append(f"strategic_stack_evidence_count={count}")
    requirement = getattr(subject, "preferred_strategic_stack_requirement_met", None)
    if requirement is None:
        requirement = getattr(subject, "strategic_stack_requirement_met", None)
    if requirement is not None:
        facts.append(f"strategic_stack_requirement_met={requirement}")
    return facts

def _append_node(
    nodes: list[OracleExplanationNode],
    *,
    node_id: str,
    parent_node_id: str | None,
    category: str,
    conclusion: str,
    detail: str,
    facts: list[str] | None = None,
) -> None:
    nodes.append(
        OracleExplanationNode(
            node_id=node_id,
            parent_node_id=parent_node_id,
            category=category,
            conclusion=conclusion,
            detail=detail,
            facts=list(facts or []),
        )
    )


def _add_lineage_nodes(
    nodes: list[OracleExplanationNode],
    *,
    parent_node_id: str,
    verification: Any | None,
) -> None:
    if verification is None:
        _append_node(
            nodes,
            node_id=f"{parent_node_id}.lineage",
            parent_node_id=parent_node_id,
            category="lineage",
            conclusion="LINEAGE_UNAVAILABLE",
            detail="Doctrine-lineage verification was not available in this render context, so trust cannot be elevated above restricted replay semantics.",
        )
        return
    banner = trust_banner_for_lineage_verification(verification)
    _append_node(
        nodes,
        node_id=f"{parent_node_id}.lineage",
        parent_node_id=parent_node_id,
        category="lineage",
        conclusion=f"seal_status={getattr(verification, 'seal_status', 'UNKNOWN')}",
        detail=banner.lineage_reason,
        facts=[
            f"completeness_percent={getattr(verification, 'completeness_percent', 0)}",
            f"valid_required_layer_count={getattr(verification, 'valid_required_layer_count', 0)}",
            f"required_layer_count={getattr(verification, 'required_layer_count', 0)}",
        ] + _strategic_backing_facts(verification),
    )
    missing_required_layers = list(getattr(verification, "missing_required_layers", []) or [])
    if missing_required_layers:
        _append_node(
            nodes,
            node_id=f"{parent_node_id}.lineage.missing_required",
            parent_node_id=f"{parent_node_id}.lineage",
            category="lineage",
            conclusion="MISSING_REQUIRED_LAYERS",
            detail="Some required doctrine-lineage layers are missing or invalid.",
            facts=missing_required_layers,
        )
    parse_failures = list(getattr(verification, "parse_failures", []) or [])
    if parse_failures:
        _append_node(
            nodes,
            node_id=f"{parent_node_id}.lineage.parse_failures",
            parent_node_id=f"{parent_node_id}.lineage",
            category="warning",
            conclusion="PARSE_FAILURES",
            detail="One or more doctrine-lineage artifacts failed schema or integrity parsing.",
            facts=parse_failures,
        )
    integrity_warnings = list(getattr(verification, "integrity_warnings", []) or [])
    if integrity_warnings:
        _append_node(
            nodes,
            node_id=f"{parent_node_id}.lineage.integrity_warnings",
            parent_node_id=f"{parent_node_id}.lineage",
            category="warning",
            conclusion="INTEGRITY_WARNINGS",
            detail="Doctrine-lineage indexing emitted integrity warnings that keep the surface from being fully sealed.",
            facts=integrity_warnings,
        )
    backing_facts = _strategic_backing_facts(verification)
    if backing_facts:
        _append_node(
            nodes,
            node_id=f"{parent_node_id}.lineage.strategic_backing",
            parent_node_id=f"{parent_node_id}.lineage",
            category="authority",
            conclusion="STRATEGIC_BACKING_SOURCE",
            detail="These sealed lineage artifacts establish which strategist-grounding source currently controls trust evaluation.",
            facts=backing_facts,
        )


def explain_lineage_verification(verification: Any, *, subject_path: str | None = None) -> OracleTrustExplanationReport:
    banner = trust_banner_for_lineage_verification(verification)
    nodes: list[OracleExplanationNode] = []
    _append_node(
        nodes,
        node_id="root",
        parent_node_id=None,
        category="trust",
        conclusion=banner.trust_status,
        detail=banner.lineage_reason,
        facts=[f"summary={getattr(verification, 'summary_line', '')}"],
    )
    _add_lineage_nodes(nodes, parent_node_id="root", verification=verification)
    operator_actions = list(getattr(verification, "operator_actions", []) or [])
    if operator_actions:
        _append_node(
            nodes,
            node_id="root.operator_actions",
            parent_node_id="root",
            category="operator_action",
            conclusion="NEXT_ACTIONS",
            detail="Operators should use these remediation or follow-up steps before escalating reliance.",
            facts=operator_actions,
        )
    return OracleTrustExplanationReport(
        generated_at_utc=_utc_now(),
        explanation_kind="lineage_verification",
        subject_schema_version=getattr(verification, "schema_version", "unknown"),
        subject_path=subject_path,
        trust_status=banner.trust_status,
        preferred_strategic_backing_source=getattr(verification, "preferred_strategic_backing_source", None),
        preferred_strategic_backing_classification=getattr(verification, "preferred_strategic_backing_classification", None),
        exact_feedback_confirmation_count=int(getattr(verification, "exact_feedback_confirmation_count", 0) or 0),
        exact_feedback_relief_count=int(getattr(verification, "exact_feedback_relief_count", 0) or 0),
        summary_line=banner.lineage_reason,
        nodes=nodes,
    )


def explain_derived_view_trust(
    report: Any,
    *,
    lineage_verification: Any | None = None,
    subject_path: str | None = None,
) -> OracleTrustExplanationReport:
    banner = trust_banner_for_derived_view(report, lineage_verification=lineage_verification)
    nodes: list[OracleExplanationNode] = []
    _append_node(
        nodes,
        node_id="root",
        parent_node_id=None,
        category="trust",
        conclusion=banner.trust_status,
        detail=banner.lineage_reason,
        facts=[
            f"view_label={getattr(report, 'view_label', '')}",
            f"derived_classification={getattr(report, 'derived_classification', '')}",
            f"window_entry_count={getattr(report, 'window_entry_count', 0)}",
        ],
    )
    evidence_gap_count = int(getattr(report, "evidence_gap_count", 0) or 0)
    elevated_or_unknown_count = int(getattr(report, "elevated_or_unknown_count", 0) or 0)
    _append_node(
        nodes,
        node_id="root.evidence",
        parent_node_id="root",
        category="evidence",
        conclusion="EVIDENCE_GAP_PRESENT" if evidence_gap_count > 0 else "EVIDENCE_WINDOW_VERIFIED",
        detail=(
            "The derived Event Log window contains evidence gaps or unverifiable entries."
            if evidence_gap_count > 0
            else "The derived Event Log window did not report direct evidence gaps."
        ),
        facts=[
            f"evidence_gap_count={evidence_gap_count}",
            f"elevated_or_unknown_count={elevated_or_unknown_count}",
            f"average_posterior_edge_confidence={getattr(report, 'average_posterior_edge_confidence', 0.0)}",
        ],
    )
    _add_lineage_nodes(nodes, parent_node_id="root", verification=lineage_verification)
    operator_actions = list(getattr(report, "operator_actions", []) or [])
    if operator_actions:
        _append_node(
            nodes,
            node_id="root.operator_actions",
            parent_node_id="root",
            category="operator_action",
            conclusion="NEXT_ACTIONS",
            detail="The derived view already proposes the following operator actions.",
            facts=operator_actions,
        )
    return OracleTrustExplanationReport(
        generated_at_utc=_utc_now(),
        explanation_kind="derived_view",
        subject_schema_version=getattr(report, "schema_version", "unknown"),
        subject_path=subject_path,
        trust_status=banner.trust_status,
        preferred_strategic_backing_source=getattr(lineage_verification, "preferred_strategic_backing_source", None),
        preferred_strategic_backing_classification=getattr(lineage_verification, "preferred_strategic_backing_classification", None),
        exact_feedback_confirmation_count=int(getattr(lineage_verification, "exact_feedback_confirmation_count", 0) or 0),
        exact_feedback_relief_count=int(getattr(lineage_verification, "exact_feedback_relief_count", 0) or 0),
        summary_line=banner.lineage_reason,
        nodes=nodes,
    )


def explain_event_checkpoint_trust(
    manifest: Any,
    verification: Any,
    *,
    lineage_verification: Any | None = None,
    subject_path: str | None = None,
) -> OracleTrustExplanationReport:
    banner = trust_banner_for_event_checkpoint(manifest, verification, lineage_verification=lineage_verification)
    nodes: list[OracleExplanationNode] = []
    _append_node(
        nodes,
        node_id="root",
        parent_node_id=None,
        category="trust",
        conclusion=banner.trust_status,
        detail=banner.lineage_reason,
        facts=[
            f"checkpoint_id={getattr(manifest, 'checkpoint_id', '')}",
            f"verification_status={getattr(verification, 'status', 'UNVERIFIED')}",
            f"integrity_status={getattr(manifest, 'integrity_status', 'UNKNOWN')}",
        ],
    )
    _append_node(
        nodes,
        node_id="root.evidence",
        parent_node_id="root",
        category="evidence",
        conclusion=f"verification_status={getattr(verification, 'status', 'UNVERIFIED')}",
        detail="Checkpoint trust depends on manifest digest verification, signature verification, and missing-artifact state.",
        facts=[
            f"artifact_digests_verified={getattr(verification, 'artifact_digests_verified', False)}",
            f"signature_verified={getattr(verification, 'signature_verified', False)}",
            f"verified_subject_count={getattr(verification, 'verified_subject_count', 0)}",
        ] + [f"missing_artifact={item}" for item in list(getattr(verification, 'missing_artifact_paths', []) or [])] + [f"digest_mismatch={item}" for item in list(getattr(verification, 'digest_mismatches', []) or [])],
    )
    _add_lineage_nodes(nodes, parent_node_id="root", verification=lineage_verification)
    return OracleTrustExplanationReport(
        generated_at_utc=_utc_now(),
        explanation_kind="event_checkpoint",
        subject_schema_version=getattr(manifest, "schema_version", "unknown"),
        subject_path=subject_path,
        trust_status=banner.trust_status,
        preferred_strategic_backing_source=getattr(lineage_verification, "preferred_strategic_backing_source", None),
        preferred_strategic_backing_classification=getattr(lineage_verification, "preferred_strategic_backing_classification", None),
        exact_feedback_confirmation_count=int(getattr(lineage_verification, "exact_feedback_confirmation_count", 0) or 0),
        exact_feedback_relief_count=int(getattr(lineage_verification, "exact_feedback_relief_count", 0) or 0),
        summary_line=banner.lineage_reason,
        nodes=nodes,
    )


def explain_constitutional_gate(report: Any, *, subject_path: str | None = None) -> OracleTrustExplanationReport:
    banner = trust_banner_for_constitutional_gate(report)
    nodes: list[OracleExplanationNode] = []
    _append_node(
        nodes,
        node_id="root",
        parent_node_id=None,
        category="trust",
        conclusion=banner.trust_status,
        detail=banner.lineage_reason,
        facts=[
            f"manifest_verification_status={getattr(report, 'manifest_verification_status', 'UNVERIFIED')}",
            f"lineage_seal_status={getattr(report, 'lineage_seal_status', 'UNKNOWN')}",
            f"minimum_required_seal_status={getattr(report, 'minimum_required_seal_status', 'UNKNOWN')}",
        ] + _strategic_backing_facts(report),
    )
    _append_node(
        nodes,
        node_id="root.policy",
        parent_node_id="root",
        category="policy",
        conclusion=(
            "THRESHOLD_MET"
            if getattr(report, "trusted_for_constitutional_use", False)
            else "THRESHOLD_NOT_MET"
        ),
        detail="The constitutional gate compares verified constitutional evidence against the minimum required doctrine-lineage seal threshold.",
        facts=[
            f"constitutional_digest_classification={getattr(report, 'constitutional_digest_classification', None)}",
            f"lineage_completeness_percent={getattr(report, 'lineage_completeness_percent', 0)}",
        ],
    )
    blocking_reasons = list(getattr(report, "blocking_reasons", []) or [])
    if blocking_reasons:
        _append_node(
            nodes,
            node_id="root.policy.blocking_reasons",
            parent_node_id="root.policy",
            category="policy",
            conclusion="BLOCKING_REASONS",
            detail="These constitutional policy failures blocked full trust.",
            facts=blocking_reasons,
        )
    operator_actions = list(getattr(report, "operator_actions", []) or [])
    backing_facts = _strategic_backing_facts(report)
    if backing_facts:
        _append_node(
            nodes,
            node_id="root.strategic_backing",
            parent_node_id="root",
            category="authority",
            conclusion="STRATEGIC_BACKING_SOURCE",
            detail="This constitutional decision is anchored to the following sealed strategist-backing source.",
            facts=backing_facts,
        )
    if operator_actions:
        _append_node(
            nodes,
            node_id="root.operator_actions",
            parent_node_id="root",
            category="operator_action",
            conclusion="NEXT_ACTIONS",
            detail="The constitutional gate recommends the following operator actions.",
            facts=operator_actions,
        )
    return OracleTrustExplanationReport(
        generated_at_utc=_utc_now(),
        explanation_kind="constitutional_gate",
        subject_schema_version=getattr(report, "schema_version", "unknown"),
        subject_path=subject_path,
        trust_status=banner.trust_status,
        preferred_strategic_backing_source=getattr(report, "preferred_strategic_backing_source", None),
        preferred_strategic_backing_classification=getattr(report, "preferred_strategic_backing_classification", None),
        exact_feedback_confirmation_count=int(getattr(report, "exact_feedback_confirmation_count", 0) or 0),
        exact_feedback_relief_count=int(getattr(report, "exact_feedback_relief_count", 0) or 0),
        summary_line=banner.lineage_reason,
        nodes=nodes,
    )


def explain_report_from_path(report_path: Path, *, repo_root: Path | None = None) -> OracleTrustExplanationReport:
    import json

    from strategy_validator.contracts.oracle_cadence_reviews import (
    OracleConstitutionalGateReport,
    OracleDoctrineLineageVerification,
    )
    from strategy_validator.contracts.oracle_evidence_events import OracleDerivedViewReport
    from strategy_validator.contracts.oracle_strategic_memory import (
    OracleDoctrineAdaptationReport,
    OracleResearchPriorityReport,
    OracleStrategicInterventionReport,
    )
    from strategy_validator.contracts.oracle_strategic_programs import (
    OracleStrategicCampaignExecutionReport,
    OracleStrategicCampaignReport,
    )
    from strategy_validator.validator.oracle_schema_registry import validate_registered_schema

    payload = json.loads(report_path.read_text(encoding="utf-8"))
    registration = validate_registered_schema(payload, expected_families={"oracle"})
    if registration.schema_version == "oracle_derived_view_report/v1":
        report = OracleDerivedViewReport.model_validate(payload)
        resolved_repo_root = repo_root or infer_repo_root_from_artifact_path(report_path)
        lineage = maybe_verify_oracle_lineage(repo_root=resolved_repo_root)
        return explain_derived_view_trust(report, lineage_verification=lineage, subject_path=str(report_path))
    strategic_models = {
        "oracle_doctrine_adaptation_report/v1": OracleDoctrineAdaptationReport,
        "oracle_research_priority_report/v1": OracleResearchPriorityReport,
        "oracle_strategic_intervention_report/v1": OracleStrategicInterventionReport,
        "oracle_strategic_campaign_report/v1": OracleStrategicCampaignReport,
        "oracle_strategic_campaign_execution_report/v1": OracleStrategicCampaignExecutionReport,
    }
    if registration.schema_version in strategic_models:
        report = strategic_models[registration.schema_version].model_validate(payload)
        resolved_repo_root = repo_root or infer_repo_root_from_artifact_path(report_path)
        lineage = maybe_verify_oracle_lineage(repo_root=resolved_repo_root)
        return explain_derived_view_trust(report, lineage_verification=lineage, subject_path=str(report_path))
    if registration.schema_version == "oracle_doctrine_lineage_verification/v1":
        report = OracleDoctrineLineageVerification.model_validate(payload)
        return explain_lineage_verification(report, subject_path=str(report_path))
    if registration.schema_version == "oracle_constitutional_gate_report/v1":
        report = OracleConstitutionalGateReport.model_validate(payload)
        return explain_constitutional_gate(report, subject_path=str(report_path))
    raise ValueError(
        f"oracle-explain does not yet support schema_version `{registration.schema_version}`; "
        "supported inputs are oracle_derived_view_report/v1, oracle_doctrine_adaptation_report/v1, oracle_research_priority_report/v1, oracle_strategic_intervention_report/v1, oracle_strategic_campaign_report/v1, oracle_strategic_campaign_execution_report/v1, oracle_doctrine_lineage_verification/v1, and oracle_constitutional_gate_report/v1"
    )


def explain_checkpoint_from_paths(
    manifest_path: Path,
    verification_path: Path,
    *,
    repo_root: Path | None = None,
) -> OracleTrustExplanationReport:
    import json

    from strategy_validator.contracts.oracle_evidence_events import (
    OracleEventCheckpointManifest,
    OracleEventCheckpointVerification,
    )

    manifest = OracleEventCheckpointManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    verification = OracleEventCheckpointVerification.model_validate(json.loads(verification_path.read_text(encoding="utf-8")))
    resolved_repo_root = repo_root or infer_repo_root_from_artifact_path(manifest_path)
    lineage = maybe_verify_oracle_lineage(repo_root=resolved_repo_root)
    return explain_event_checkpoint_trust(
        manifest,
        verification,
        lineage_verification=lineage,
        subject_path=str(manifest_path),
    )


def render_oracle_explanation_markdown(report: OracleTrustExplanationReport) -> str:
    lines = [
        "## Trust explanation",
        "",
        f"- Explanation kind: `{report.explanation_kind}`",
        f"- Trust status: `{report.trust_status}`",
        f"- Subject schema: `{report.subject_schema_version}`",
    ]
    if report.subject_path:
        lines.append(f"- Subject path: `{report.subject_path}`")
    if report.preferred_strategic_backing_source:
        lines.append(f"- Preferred strategic backing source: `{report.preferred_strategic_backing_source}`")
    if report.preferred_strategic_backing_classification:
        lines.append(f"- Preferred strategic backing classification: `{report.preferred_strategic_backing_classification}`")
    lines.extend(["", report.summary_line, ""])
    children: dict[str | None, list[OracleExplanationNode]] = {}
    for node in report.nodes:
        children.setdefault(node.parent_node_id, []).append(node)
    for key in children:
        children[key].sort(key=lambda item: item.node_id)

    def _emit(parent_id: str | None, depth: int = 0) -> list[str]:
        emitted: list[str] = []
        for node in children.get(parent_id, []):
            indent = "  " * depth
            emitted.append(f"{indent}- **{node.category}** `{node.conclusion}` — {node.detail}")
            for fact in node.facts:
                emitted.append(f"{indent}  - {fact}")
            emitted.extend(_emit(node.node_id, depth + 1))
        return emitted

    lines.extend(_emit(None))
    lines.append("")
    return "\n".join(lines)
