from __future__ import annotations

from pathlib import Path

from strategy_validator.contracts.operational import (
    ClosureReleaseAttestation,
    ClosureSnapshotVerification,
    GovernedExceptionMemo,
    GovernedExceptionVerification,
)
from strategy_validator.contracts.oracle_cadence_reviews import OracleConstitutionalGateReport
from strategy_validator.contracts.oracle_operator_reports import OracleStatusPackSection
from strategy_validator.validator.oracle_constitutional import verify_oracle_doctrine_lineage
from strategy_validator.validator.oracle_diagnostics_foundations import (
    _TRUST_RANK,
    _actions_from_explanation,
    _default_public_key,
    _exact_cadence_signal_classification,
    _facts_from_explanation,
    _find_latest,
    _load_json,
    _load_temporal_lane_status,
    _resolve_explanation_from_report,
    _unique,
)
from strategy_validator.validator.oracle_explain import explain_lineage_verification
from strategy_validator.validator.oracle_trust import trust_banner_for_lineage_verification
from strategy_validator.validator.rollout_ops import (
    build_closure_release_attestation,
    verify_closure_snapshot,
    verify_governed_exception_memo,
)


def _build_lineage_section(*, resolved_repo_root: Path, resolved_search_root: Path) -> tuple[OracleStatusPackSection, tuple[str, ...], str | None, str | None]:
    lineage = verify_oracle_doctrine_lineage(repo_root=resolved_repo_root, search_root=resolved_search_root)
    lineage_banner = trust_banner_for_lineage_verification(lineage)
    lineage_explanation = explain_lineage_verification(lineage, subject_path=str(resolved_search_root))
    section = OracleStatusPackSection(
        section_id="lineage",
        status=lineage.seal_status,
        summary_line=lineage.summary_line,
        preferred_strategic_backing_source=getattr(lineage, "preferred_strategic_backing_source", None),
        preferred_strategic_backing_classification=getattr(lineage, "preferred_strategic_backing_classification", None),
        exact_feedback_confirmation_count=getattr(lineage, "exact_feedback_confirmation_count", 0),
        exact_feedback_relief_count=getattr(lineage, "exact_feedback_relief_count", 0),
        exact_cadence_signal_classification=_exact_cadence_signal_classification(
            exact_feedback_confirmation_count=getattr(lineage, "exact_feedback_confirmation_count", 0),
            exact_feedback_relief_count=getattr(lineage, "exact_feedback_relief_count", 0),
        ),
        facts=[
            f"trust_status={lineage_banner.trust_status}",
            f"completeness_percent={lineage.completeness_percent}",
            f"valid_required_layer_count={lineage.valid_required_layer_count}",
            f"required_layer_count={lineage.required_layer_count}",
            f"exact_evidence_support_score={getattr(lineage, 'exact_evidence_support_score', 0.0):.2f}",
            f"exact_feedback_confirmation_count={getattr(lineage, 'exact_feedback_confirmation_count', 0)}",
            f"exact_feedback_relief_count={getattr(lineage, 'exact_feedback_relief_count', 0)}",
        ] + [f"missing_required_layer={item}" for item in lineage.missing_required_layers],
        operator_actions=list(lineage.operator_actions),
        explanation=lineage_explanation,
    )
    return (
        section,
        tuple(lineage.operator_actions),
        getattr(lineage, "preferred_strategic_backing_source", None),
        getattr(lineage, "preferred_strategic_backing_classification", None),
    )


def _build_oracle_posture_section(*, derived_path: Path, repo_root: Path) -> tuple[OracleStatusPackSection, tuple[str, ...]]:
    payload, explanation = _resolve_explanation_from_report(derived_path, repo_root=repo_root)
    actions = _actions_from_explanation(explanation)
    section = OracleStatusPackSection(
        section_id="oracle_posture",
        status=explanation.trust_status,
        summary_line=payload.get("summary_line") or explanation.summary_line,
        facts=_unique([
            f"view_label={payload.get('view_label', '')}",
            f"window_entry_count={payload.get('window_entry_count', 0)}",
            f"derived_classification={payload.get('derived_classification', '')}",
            f"subject_path={derived_path}",
        ] + _facts_from_explanation(explanation, categories={"trust", "evidence", "warning"})),
        operator_actions=actions,
        explanation=explanation,
    )
    return section, tuple(actions)


def _build_temporal_lane_section(*, temporal_path: Path) -> tuple[OracleStatusPackSection, tuple[str, ...]]:
    temporal_status = _load_temporal_lane_status(temporal_path)
    temporal_facts = [
        f"provider_id={temporal_status.provider_id}",
        f"model_name={temporal_status.model_name}",
        f"batch_window={temporal_status.batch_start_date.isoformat()}..{temporal_status.batch_end_date.isoformat()}",
        f"extraction_days={temporal_status.extraction_days}",
        f"verified_days={temporal_status.verified_days}",
        f"rejected_days={temporal_status.rejected_days}",
        f"canonicalized_days={temporal_status.canonicalized_days}",
        f"canonicalization_skipped_days={temporal_status.canonicalization_skipped_days}",
        f"appended_days={temporal_status.appended_days}",
        f"append_skipped_days={temporal_status.append_skipped_days}",
        f"verification_status={temporal_status.verification_status}",
        f"canonicalization_verification_status={temporal_status.canonicalization_verification_status}",
        f"subject_path={temporal_path}",
    ]
    if temporal_status.append_lane_path:
        temporal_facts.append(f"append_lane_path={temporal_status.append_lane_path}")
    temporal_actions = list(temporal_status.operator_lines[1:] or [temporal_status.summary_line])
    section = OracleStatusPackSection(
        section_id="temporal_lane",
        status=temporal_status.verification_status,
        summary_line=temporal_status.summary_line,
        facts=_unique(temporal_facts),
        operator_actions=_unique(temporal_actions),
        explanation=None,
    )
    return section, tuple(temporal_actions)


def _build_constitutional_gate_section(*, gate_path: Path, repo_root: Path) -> tuple[OracleStatusPackSection, tuple[str, ...], str | None, str | None]:
    payload, explanation = _resolve_explanation_from_report(gate_path, repo_root=repo_root)
    gate_report = OracleConstitutionalGateReport.model_validate(payload)
    section = OracleStatusPackSection(
        section_id="constitutional_gate",
        status=gate_report.trust_status,
        summary_line=gate_report.summary_line,
        preferred_strategic_backing_source=gate_report.preferred_strategic_backing_source,
        preferred_strategic_backing_classification=gate_report.preferred_strategic_backing_classification,
        exact_feedback_confirmation_count=gate_report.exact_feedback_confirmation_count,
        exact_feedback_relief_count=gate_report.exact_feedback_relief_count,
        exact_cadence_signal_classification=_exact_cadence_signal_classification(
            exact_feedback_confirmation_count=gate_report.exact_feedback_confirmation_count,
            exact_feedback_relief_count=gate_report.exact_feedback_relief_count,
        ),
        facts=_unique([
            f"lineage_seal_status={gate_report.lineage_seal_status}",
            f"minimum_required_seal_status={gate_report.minimum_required_seal_status}",
            f"manifest_verification_status={gate_report.manifest_verification_status}",
            f"trusted_for_constitutional_use={gate_report.trusted_for_constitutional_use}",
            f"exact_evidence_support_score={gate_report.exact_evidence_support_score:.2f}",
            f"exact_feedback_confirmation_count={gate_report.exact_feedback_confirmation_count}",
            f"exact_feedback_relief_count={gate_report.exact_feedback_relief_count}",
        ] + [f"blocking_reason={item}" for item in gate_report.blocking_reasons]),
        operator_actions=list(gate_report.operator_actions),
        explanation=explanation,
    )
    return (
        section,
        tuple(gate_report.operator_actions),
        gate_report.preferred_strategic_backing_source,
        gate_report.preferred_strategic_backing_classification,
    )


def _closure_section(*, snapshot_path: Path, verification: ClosureSnapshotVerification, attestation: ClosureReleaseAttestation) -> OracleStatusPackSection:
    return OracleStatusPackSection(
        section_id="closure_attestation",
        status=attestation.signoff_status,
        summary_line=attestation.summary_line,
        facts=_unique([
            f"closure_id={attestation.closure_id}",
            f"verification_status={verification.status}",
            f"machine_decision={attestation.machine_decision}",
            f"primary_classification={attestation.primary_classification}",
            f"final_release_stance={attestation.final_release_stance}",
            f"snapshot_path={snapshot_path}",
        ] + [f"reason={item}" for item in attestation.reasons]),
        operator_actions=list(attestation.required_operator_actions),
    )


def _build_governed_exception_and_closure_sections(
    *,
    resolved_repo_root: Path,
    resolved_search_root: Path,
    snapshot_path: Path,
    closure_dsse_path: Path | None,
    closure_public_key_path: Path | None,
    governed_exception_memo_path: Path | None,
    governed_exception_dsse_path: Path | None,
    governed_exception_public_key_path: Path | None,
) -> tuple[tuple[OracleStatusPackSection, ...], tuple[str, ...], tuple[str, ...]]:
    snapshot_path = snapshot_path.resolve()
    if closure_dsse_path is None:
        candidate = snapshot_path.with_name("CLOSURE_SNAPSHOT.dsse.json")
        closure_dsse_path = candidate if candidate.exists() else None
    if closure_public_key_path is None:
        closure_public_key_path = _default_public_key(resolved_repo_root)
    closure_verification = verify_closure_snapshot(
        snapshot_path=snapshot_path,
        repo_root=resolved_repo_root,
        dsse_path=closure_dsse_path,
        public_key_path=closure_public_key_path,
    )
    sections: list[OracleStatusPackSection] = []
    operator_actions: list[str] = []
    active_ids: list[str] = []
    governed_memo: GovernedExceptionMemo | None = None
    governed_verification: GovernedExceptionVerification | None = None
    memo_path = governed_exception_memo_path
    if memo_path is None and resolved_search_root.exists():
        memo_path = _find_latest(resolved_search_root, ["GOVERNED_EXCEPTION_MEMO.json"])
    if memo_path is not None and memo_path.exists():
        memo_path = memo_path.resolve()
        if governed_exception_dsse_path is None:
            candidate = memo_path.with_name("GOVERNED_EXCEPTION_MEMO.dsse.json")
            governed_exception_dsse_path = candidate if candidate.exists() else None
        if governed_exception_public_key_path is None:
            governed_exception_public_key_path = closure_public_key_path or _default_public_key(resolved_repo_root)
        governed_memo = GovernedExceptionMemo.model_validate(_load_json(memo_path))
        governed_verification = verify_governed_exception_memo(
            memo_path=memo_path,
            repo_root=resolved_repo_root,
            dsse_path=governed_exception_dsse_path,
            public_key_path=governed_exception_public_key_path,
        )
        section = OracleStatusPackSection(
            section_id="governed_exception",
            status=governed_verification.status,
            summary_line=f"Governed exception `{governed_memo.exception_id}` verification is {governed_verification.status}.",
            facts=_unique([
                f"closure_id={governed_memo.closure_id}",
                f"governed_exception_code={governed_memo.governed_exception_code}",
                f"approved_by={governed_memo.approved_by}",
                f"valid_until_utc={governed_memo.valid_until_utc.isoformat()}",
            ] + [f"verification_note={item}" for item in governed_verification.notes]),
            operator_actions=[
                "Re-verify or renew the governed exception before its validity window ends."
            ] if governed_verification.status != "VERIFIED" else [
                "Re-evaluate the closure snapshot before the governed exception expires."
            ],
        )
        sections.append(section)
        if governed_verification.status == "VERIFIED":
            active_ids.append(governed_memo.exception_id)
        operator_actions.extend(section.operator_actions)
    attestation, _ = build_closure_release_attestation(
        snapshot_path=snapshot_path,
        repo_root=resolved_repo_root,
        verification=closure_verification,
        verification_path=snapshot_path.with_name("CLOSURE_SNAPSHOT.verification.json") if snapshot_path.with_name("CLOSURE_SNAPSHOT.verification.json").exists() else None,
        review_path=snapshot_path.parent / "RUNTIME_REVIEW.json",
        governed_exception_memo=governed_memo,
        governed_exception_verification=governed_verification,
    )
    sections.append(_closure_section(snapshot_path=snapshot_path, verification=closure_verification, attestation=attestation))
    operator_actions.extend(attestation.required_operator_actions)
    if attestation.applied_governed_exception_id:
        active_ids.append(attestation.applied_governed_exception_id)
    return tuple(sections), tuple(operator_actions), tuple(active_ids)


__all__ = [name for name in globals() if not name.startswith("__")]
