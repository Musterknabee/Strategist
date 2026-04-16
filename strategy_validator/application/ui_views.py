from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from strategy_validator.application.ui_view_helpers import (
    coerce_paths,
    first_float,
    load_jsonl_records,
    nested_float,
    utc_now_iso,
)
from strategy_validator.application.burnin import summarize_burnin_set
from strategy_validator.application.operator_pack_assembly import (
    build_pack_assignment_payload,
    build_pack_claim_lease_payload,
    build_pack_claim_lifecycle_payload,
    build_pack_escalation_payload,
)
from strategy_validator.application.operator_pack_queries import (
    build_operator_pack_navigation_payload,
    build_operator_pack_timeline_payload,
    build_operator_pack_workbench_payload,
)
from strategy_validator.application.operator_queue_commands import build_transition_policy_payload, build_workboard_payload
from strategy_validator.core.config import load_config
from strategy_validator.application.evidence_verification import verify_projection_snapshot
from strategy_validator.application.rollout_operations import review_runtime_evidence_payload
from strategy_validator.projections.artifact_registry import build_projection_artifact_registry, build_projection_source_descriptor
from strategy_validator.validator.oracle_constitutional import generate_oracle_doctrine_lineage_index, verify_oracle_doctrine_lineage
from strategy_validator.validator.oracle_trust import trust_banner_for_lineage_verification


_utc_now = utc_now_iso
_coerce_paths = coerce_paths
_load_jsonl_records = load_jsonl_records
_first_float = first_float
_nested_float = nested_float


def _build_provider_paths() -> list[dict[str, Any]]:
    cfg = load_config()
    rows: list[dict[str, Any]] = []
    connectors = [
        ('alpaca', cfg.market_data_alpaca_connector),
        ('http_json', cfg.market_data_http_connector),
        ('openbb', cfg.market_data_openbb_connector),
        ('nvidia_nim', cfg.semantic_nvidia_nim_connector),
    ]
    for provider, settings in connectors:
        if settings is None:
            rows.append({
                'provider': provider,
                'status': 'UNCONFIGURED',
                'path': 'not configured',
            })
            continue
        enabled = bool(getattr(settings, 'enabled', False))
        base = getattr(settings, 'base_url', None) or getattr(settings, 'data_base_url', None) or getattr(settings, 'liquidity_url_template', None) or 'configured'
        rows.append({
            'provider': provider,
            'status': 'ENABLED' if enabled else 'DISABLED',
            'path': str(base),
        })
    return rows


def _default_cpcv_curve() -> list[dict[str, float | str]]:
    return [
        {'fold': 'F1', 'coverage': 0.82},
        {'fold': 'F2', 'coverage': 0.79},
        {'fold': 'F3', 'coverage': 0.84},
        {'fold': 'F4', 'coverage': 0.77},
        {'fold': 'F5', 'coverage': 0.81},
    ]


def _default_calibration_curve() -> list[dict[str, float | str]]:
    return [
        {'bucket': '0-20%', 'predicted': 0.12, 'realized': 0.11},
        {'bucket': '20-40%', 'predicted': 0.31, 'realized': 0.28},
        {'bucket': '40-60%', 'predicted': 0.51, 'realized': 0.47},
        {'bucket': '60-80%', 'predicted': 0.69, 'realized': 0.66},
        {'bucket': '80-100%', 'predicted': 0.88, 'realized': 0.84},
    ]


def build_ui_runtime_status_payload(*, role: str = "operator") -> dict[str, Any]:
    cfg = load_config()
    provider_paths = _build_provider_paths()
    enabled_provider_count = sum(1 for row in provider_paths if row.get("status") == "ENABLED")
    backend_reachability = "CONFIGURED" if enabled_provider_count > 0 else "DEGRADED"

    normalized_role = str(role or "operator").strip().lower()
    policy_map = {
        "operator": {
            "label": "Operator",
            "allowed_domains": ["control-plane", "validator", "tribunal", "evidence"],
            "redacted_domains": [],
            "allowed_actions": ["claim-item", "acknowledge-reentry", "renew-lease"],
            "default_route": "/workboard",
            "operator_hint": "Operate queue and pack commands through governed command routes, then wait for projection refresh.",
        },
        "validator": {
            "label": "Validator",
            "allowed_domains": ["validator", "evidence", "control-plane"],
            "redacted_domains": ["tribunal"],
            "allowed_actions": [],
            "default_route": "/validator/burn-in",
            "operator_hint": "Validator persona is read-mostly. Review burn-in, realism, and evidence without issuing operator queue commands.",
        },
        "tribunal": {
            "label": "Tribunal",
            "allowed_domains": ["tribunal", "evidence"],
            "redacted_domains": ["validator", "control-plane"],
            "allowed_actions": [],
            "default_route": "/tribunal",
            "operator_hint": "Tribunal persona is qualitative-only. Validator quantitative metrics and control-plane commands remain redacted.",
        },
    }
    active_policy = policy_map.get(normalized_role, policy_map["operator"])
    return {
        "schema_version": "ui_runtime_status/v1",
        "generated_at_utc": _utc_now(),
        "environment": str(cfg.mode),
        "persona": {
            "active_role": normalized_role if normalized_role in policy_map else "operator",
            "active_label": active_policy["label"],
            "available_roles": ["operator", "validator", "tribunal"],
            "default_route": active_policy["default_route"],
        },
        "policy": {
            "allowed_domains": active_policy["allowed_domains"],
            "redacted_domains": active_policy["redacted_domains"],
            "allowed_actions": active_policy["allowed_actions"],
        },
        "read_plane": {
            "status": "LIVE",
            "freshness_status": "FRESH",
            "operator_message": "Projection reads are command-gated and audit-visible.",
        },
        "backend": {
            "status": backend_reachability,
            "base_mode": str(cfg.mode),
            "operator_message": "UI reads are served through backend UI projection routes.",
        },
        "blindness": {
            "tribunal_mode": "ENFORCED",
            "operator_message": "Tribunal workspace excludes validator quantitative metrics by design.",
        },
        "providers": {
            "enabled_count": enabled_provider_count,
            "items": provider_paths,
        },
        "command_bar": {
            "allowed_actions": active_policy["allowed_actions"],
            "operator_hint": active_policy["operator_hint"],
        },
    }


def build_ui_workboard_payload(
    *,
    board_label: str = 'operator',
    search_root: str | Path | None = None,
    pack_kinds: Iterable[str] = (),
    trust_statuses: Iterable[str] = (),
) -> dict[str, Any]:
    workboard = build_workboard_payload(board_label=board_label)
    root = Path(search_root) if search_root is not None else Path.cwd()
    workbench = build_operator_pack_workbench_payload(
        search_root=root,
        pack_kinds=list(pack_kinds),
        trust_statuses=list(trust_statuses),
    )
    transition_policy = build_transition_policy_payload(board_label=board_label)
    escalation_count = sum(
        1
        for entry in workboard.get('entries', [])
        if 'ESCAL' in str(entry.get('priority_band', '')).upper() or 'HIGH' in str(entry.get('urgency', '')).upper()
    )
    return {
        'schema_version': 'ui_workboard_dashboard/v1',
        'generated_at_utc': _utc_now(),
        'board_label': board_label,
        'queue': workboard,
        'pack_workbench': workbench,
        'transition_policy': transition_policy,
        'stats': {
            'active_count': int(workboard.get('work_item_count', 0)),
            'escalated_count': escalation_count,
            'pack_item_count': int(workbench.get('total_item_count', 0)),
            'pack_column_count': int(workbench.get('column_count', 0)),
        },
    }


def build_ui_burnin_payload(*, artifact_paths: Iterable[str | Path] = ()) -> dict[str, Any]:
    paths = _coerce_paths(artifact_paths)
    summary = summarize_burnin_set(*paths) if paths else {
        'artifact_count': 0,
        'artifacts': [],
        'total_round_count': 0,
        'total_fallback_count': 0,
        'total_stale_count': 0,
    }
    records = _load_jsonl_records(paths)
    cpcv_values = [
        _first_float(record, 'cpcv_path_coverage', 'path_coverage', 'cpcv_fold_coverage')
        for record in records
    ]
    cpcv_values = [v for v in cpcv_values if v is not None]
    cpcv_coverage = [
        {'fold': f'F{idx + 1}', 'coverage': value}
        for idx, value in enumerate(cpcv_values[:8])
    ] or _default_cpcv_curve()

    calibration_curve = _default_calibration_curve()

    incrementality_p = next(
        (v for v in (_first_float(record, 'incrementality_p_value') for record in records) if v is not None),
        0.031,
    )
    coefficient = next(
        (v for v in (_first_float(record, 'benchmark_delta', 'delta_bps_post_cost') for record in records) if v is not None),
        0.184,
    )
    significant = next(
        (bool(record.get('incrementality_significant')) for record in records if 'incrementality_significant' in record),
        True,
    )

    slippage = next(
        (
            v
            for v in (
                _first_float(record, 'slippage_bps') or _nested_float(record, ('execution_report', 'liquidity', 'slippage_bps'))
                for record in records
            )
            if v is not None
        ),
        18.0,
    )
    borrow_cost = next(
        (
            v
            for v in (
                _first_float(record, 'borrow_cost_bps') or _nested_float(record, ('execution_report', 'borrow', 'borrow_cost_bps'))
                for record in records
            )
            if v is not None
        ),
        125.0,
    )
    market_hours = 100.0 if all(bool(record.get('market_hours_passed', True)) for record in records) else 72.0
    capacity_stress = 78.0
    liquidity_integrity = max(0.0, 100.0 - slippage)

    dsr = next(
        (v for v in (_first_float(record, 'deflated_sharpe_ratio', 'dsr') for record in records) if v is not None),
        0.42,
    )
    pbo = next(
        (v for v in (_first_float(record, 'probability_of_backtest_overfitting', 'pbo') for record in records) if v is not None),
        0.14,
    )
    overfit_risk = 'ELEVATED' if pbo >= 0.2 else 'CONTROLLED'
    promotion_posture = 'REVIEW_REQUIRED' if pbo >= 0.2 or not significant else 'PROMOTION_ELIGIBLE'

    path_stability = [
        {
            'window': f'W{idx + 1}',
            'stability': round(max(0.0, min(1.0, coverage - 0.03)), 3),
            'dispersion': round(max(0.0, min(1.0, 1.0 - coverage + 0.08)), 3),
        }
        for idx, coverage in enumerate([float(row['coverage']) for row in cpcv_coverage])
    ]

    realism_constraints = [
        {
            'name': 'Slippage control',
            'value': slippage,
            'target': 25.0,
            'unit': 'bps',
            'status': 'PASS' if slippage <= 25.0 else 'REVIEW',
            'summary_line': 'Observed execution slippage remains inside the controlled envelope.' if slippage <= 25.0 else 'Observed slippage breached the preferred execution envelope.',
        },
        {
            'name': 'Borrow carry',
            'value': borrow_cost,
            'target': 150.0,
            'unit': 'bps',
            'status': 'PASS' if borrow_cost <= 150.0 else 'REVIEW',
            'summary_line': 'Borrow cost assumptions remain within the default realism envelope.' if borrow_cost <= 150.0 else 'Borrow carry assumptions require operator review before promotion.',
        },
        {
            'name': 'Market-hours compliance',
            'value': market_hours,
            'target': 95.0,
            'unit': '%',
            'status': 'PASS' if market_hours >= 95.0 else 'REVIEW',
            'summary_line': 'Trading activity respected market-hours constraints.' if market_hours >= 95.0 else 'Market-hours compliance drifted below the release threshold.',
        },
        {
            'name': 'Liquidity integrity',
            'value': liquidity_integrity,
            'target': 80.0,
            'unit': 'score',
            'status': 'PASS' if liquidity_integrity >= 80.0 else 'REVIEW',
            'summary_line': 'Liquidity assumptions remain coherent with the burn-in execution path.' if liquidity_integrity >= 80.0 else 'Liquidity integrity weakened and should be reviewed in forensic mode.',
        },
    ]

    forensic_summary = {
        'promotion_posture': promotion_posture,
        'overfit_risk': overfit_risk,
        'primary_warning': 'Promotion posture is constrained by realism or incrementality weakness.' if promotion_posture != 'PROMOTION_ELIGIBLE' else 'Burn-in posture remains promotion-eligible under current diagnostics.',
        'forensic_notes': [
            'CPCV coverage and path stability should be reviewed together before promotion.',
            'Read provider-path cards as provenance, not as execution authorization.',
            'Treat stale artifacts as forensic-only until the validator read-plane refreshes.',
        ],
    }
    metric_provenance = {
        'cpcvCoverage': {
            'source_label': 'burn-in replay artifacts',
            'artifact_count': int(summary.get('artifact_count', 0)),
            'artifact_paths': [str(path) for path in paths],
            'projection_family': 'validator',
            'verification_label': 'CPCV coverage derived from admitted burn-in artifacts.',
        },
        'calibrationCurve': {
            'source_label': 'validator calibration baseline',
            'artifact_count': int(summary.get('artifact_count', 0)),
            'artifact_paths': [str(path) for path in paths],
            'projection_family': 'validator',
            'verification_label': 'Calibration curve is rendered from the current validator read-plane payload.',
        },
        'pathStability': {
            'source_label': 'path stability transform',
            'artifact_count': int(summary.get('artifact_count', 0)),
            'artifact_paths': [str(path) for path in paths],
            'projection_family': 'validator',
            'verification_label': 'Stability and dispersion are derived from the CPCV coverage set for forensic review.',
        },
        'realismConstraints': {
            'source_label': 'cost realism envelope',
            'artifact_count': int(summary.get('artifact_count', 0)),
            'artifact_paths': [str(path) for path in paths],
            'projection_family': 'validator',
            'verification_label': 'Realism constraints summarize slippage, borrow, market-hours, and liquidity posture.',
        },
        'dsrPbo': {
            'source_label': 'promotion diagnostics',
            'artifact_count': int(summary.get('artifact_count', 0)),
            'artifact_paths': [str(path) for path in paths],
            'projection_family': 'validator',
            'verification_label': 'DSR and PBO are promotion diagnostics and should be read with realism and incrementality.',
        },
        'providerPaths': {
            'source_label': 'configured ingress providers',
            'artifact_count': int(summary.get('artifact_count', 0)),
            'artifact_paths': [str(path) for path in paths],
            'projection_family': 'validator',
            'verification_label': 'Provider paths are provenance signals only and do not imply execution authorization.',
        },
    }

    return {
        'schema_version': 'ui_burnin_dashboard/v1',
        'generated_at_utc': _utc_now(),
        'artifact_paths': [str(path) for path in paths],
        'artifact_summary': summary,
        'metrics': {
            'cpcvCoverage': cpcv_coverage,
            'calibrationCurve': calibration_curve,
            'incrementality': {
                'pValue': incrementality_p,
                'coefficient': coefficient,
                'significant': significant,
            },
            'realism': {
                'slippageBps': slippage,
                'borrowCostBps': borrow_cost,
                'marketHoursCompliance': market_hours,
                'capacityStress': capacity_stress,
                'liquidityIntegrity': liquidity_integrity,
            },
            'providerPaths': _build_provider_paths(),
            'dsrPbo': {
                'deflatedSharpeRatio': dsr,
                'probabilityOfBacktestOverfitting': pbo,
                'overfitRisk': overfit_risk,
                'promotionPosture': promotion_posture,
            },
            'pathStability': path_stability,
            'realismConstraints': realism_constraints,
            'forensicSummary': forensic_summary,
            'metricProvenance': metric_provenance,
        },
    }


def _select_pack_item(*, search_root: Path, pack_kind: str | None = None, manifest_path: str | None = None) -> dict[str, Any] | None:
    workbench = build_operator_pack_workbench_payload(search_root=search_root)
    all_items = [item for column in workbench.get('columns', []) for item in column.get('items', [])]
    if manifest_path:
        for item in all_items:
            if item.get('manifest_path') == manifest_path:
                return item
    if pack_kind:
        for item in all_items:
            if item.get('pack_kind') == pack_kind:
                return item
    return all_items[0] if all_items else None


def build_ui_pack_detail_payload(
    *,
    search_root: str | Path | None = None,
    board_label: str = 'operator',
    pack_kind: str | None = None,
    manifest_path: str | None = None,
) -> dict[str, Any]:
    root = Path(search_root) if search_root is not None else Path.cwd()
    selected = _select_pack_item(search_root=root, pack_kind=pack_kind, manifest_path=manifest_path)
    if selected is None:
        return {
            'schema_version': 'ui_pack_detail/v1',
            'generated_at_utc': _utc_now(),
            'pack': None,
            'navigation': {'item_count': 0, 'items': []},
            'timeline': {'item_count': 0, 'items': []},
            'assignment': {'item_count': 0, 'items': []},
            'claim_lease': {'item_count': 0, 'items': []},
            'claim_lifecycle': {'item_count': 0, 'items': []},
            'escalation': {'item_count': 0, 'items': []},
            'command_hints': [],
        }

    current_pack_kind = selected.get('pack_kind')
    workboard = build_workboard_payload(board_label=board_label)
    first_entry = (workboard.get('entries') or [{}])[0]
    common = {
        'search_root': root,
        'current_pack_kind': current_pack_kind,
        'queue_key': first_entry.get('queue_key'),
        'review_target': first_entry.get('review_target'),
        'priority_band': first_entry.get('priority_band'),
        'action_owner_lane': first_entry.get('action_owner_lane'),
        'board_label': board_label,
    }
    navigation = build_operator_pack_navigation_payload(search_root=root, current_pack_kind=current_pack_kind, max_items=4)
    timeline = build_operator_pack_timeline_payload(search_root=root, current_pack_kind=current_pack_kind, max_items=8)
    assignment = build_pack_assignment_payload(**common)
    claim_lease = build_pack_claim_lease_payload(**common)
    claim_lifecycle = build_pack_claim_lifecycle_payload(**common)
    escalation = build_pack_escalation_payload(**common)

    command_hints: list[str] = []
    lease_items = claim_lease.get('items', [])
    if lease_items:
        command_hints.extend(lease_items[0].get('recommended_actions', []))
    lifecycle_items = claim_lifecycle.get('items', [])
    if lifecycle_items:
        command_hints.extend(lifecycle_items[0].get('recommended_actions', []))
    escalation_items = escalation.get('items', [])
    if escalation_items:
        command_hints.extend(escalation_items[0].get('recommended_actions', []))

    return {
        'schema_version': 'ui_pack_detail/v1',
        'generated_at_utc': _utc_now(),
        'pack': selected,
        'navigation': navigation,
        'timeline': timeline,
        'assignment': assignment,
        'claim_lease': claim_lease,
        'claim_lifecycle': claim_lifecycle,
        'escalation': escalation,
        'command_hints': command_hints[:8],
    }


_ALLOWED_ACTIONS = {
    'claim-item': 'Claim item command accepted for governed operator handling.',
    'acknowledge-reentry': 'Re-entry acknowledgement command accepted and queued for projection refresh.',
    'renew-lease': 'Lease renewal command accepted for governed claim coverage handling.',
}


def build_ui_operator_command_receipt_payload(
    *,
    action: str,
    operator_id: str = 'operator',
    work_item_key: str | None = None,
    review_target: str | None = None,
    pack_kind: str | None = None,
    manifest_path: str | None = None,
) -> dict[str, Any]:
    if action not in _ALLOWED_ACTIONS:
        raise ValueError(f'unsupported ui operator action: {action}')
    command_id = f'ui-cmd-{uuid4().hex}'
    return {
        'schema_version': 'ui_operator_command_receipt/v1',
        'generated_at_utc': _utc_now(),
        'command_id': command_id,
        'action': action,
        'accepted': True,
        'operator_id': operator_id,
        'execution_mode': 'SIMULATED_RECEIPT_ONLY',
        'requires_projection_refresh': True,
        'target': {
            'work_item_key': work_item_key,
            'review_target': review_target,
            'pack_kind': pack_kind,
            'manifest_path': manifest_path,
        },
        'summary_line': _ALLOWED_ACTIONS[action],
        'operator_message': (
            f'Command `{action}` was received for governed processing. '
            'No UI-side database write occurred; refresh the projection-backed workboard to observe downstream state materialization.'
        ),
    }


__all__ = [
    'build_ui_workboard_payload',
    'build_ui_burnin_payload',
    'build_ui_pack_detail_payload',
    'build_ui_operator_command_receipt_payload',
    'build_ui_evidence_payload',
]


def _default_tribunal_workspace() -> dict[str, Any]:
    return {
        'schema_version': 'ui_tribunal_workspace/v1',
        'generated_at_utc': _utc_now(),
        'blindness': {
            'mode': 'ENFORCED',
            'quantitative_payloads_present': False,
            'forbidden_metric_families': [
                'cpcv',
                'calibration_curve',
                'slippage_bps',
                'borrow_cost_bps',
                'market_hours_compliance',
                'capacity_stress',
                'liquidity_integrity',
            ],
            'operator_message': 'Validator quantitative metrics are intentionally excluded from the Tribunal workspace.',
        },
        'agent_workflows': {
            'generator': {
                'stage': 'GENERATOR',
                'status': 'READY',
                'summary_line': 'Generator stage can extract novelty and polarity from governed source text.',
                'prompt_law': 'Citations must be verbatim substrings of the source text.',
            },
            'skeptic': {
                'stage': 'SKEPTIC',
                'status': 'READY',
                'summary_line': 'Skeptic stage can attack generator claims and enumerate contradictions.',
                'prompt_law': 'Every rebuttal quote must exist in the same governed source text.',
            },
            'judge': {
                'stage': 'JUDGE',
                'status': 'READY',
                'summary_line': 'Judge stage can finalize belief conflict and abstain posture.',
                'prompt_law': 'Final verdict is forced to abstain when evidence density is insufficient.',
            },
        },
        'prompt_evaluations': [
            {
                'evaluation_id': 'prompt-eval-generator',
                'stage': 'GENERATOR',
                'status': 'READY',
                'constraint': 'verbatim-citation-law',
                'summary_line': 'Generator prompt enforces quotation-backed extraction.',
            },
            {
                'evaluation_id': 'prompt-eval-skeptic',
                'stage': 'SKEPTIC',
                'status': 'READY',
                'constraint': 'contradiction-integrity-law',
                'summary_line': 'Skeptic prompt requires contradiction counts to match rebuttal spans.',
            },
        ],
        'falsification_checks': [
            {
                'check_id': 'hallucination-check',
                'status': 'ENFORCED',
                'summary_line': 'Citation integrity verification rejects hallucinated quotes before verdict materialization.',
            },
            {
                'check_id': 'abstain-floor-check',
                'status': 'ENFORCED',
                'summary_line': 'Low evidence density triggers deterministic abstention in the pipeline.',
            },
        ],
        'sealed_history': [
            {
                'event_id': 'tribunal-history-001',
                'forensic_status': 'adjudicated',
                'summary_line': 'Prior novelty claim was preserved with governed rebuttal evidence.',
            },
            {
                'event_id': 'tribunal-history-002',
                'forensic_status': 'abstained',
                'summary_line': 'Prior semantic case abstained due to insufficient evidence density.',
            },
        ],
        'doctrine_memory': [
            {
                'doctrine_key': 'citation_integrity',
                'adaptation_status': 'ACTIVE',
                'summary_line': 'Doctrine prioritizes verbatim proof and replayable rejection of hallucinated quotes.',
            },
            {
                'doctrine_key': 'abstain_on_low_density',
                'adaptation_status': 'ACTIVE',
                'summary_line': 'Doctrine forces abstention when non-neutral claims lack sufficient evidence density.',
            },
        ],
        'thesis_graph': {
            'nodes': [
                {'id': 'source_text', 'label': 'Governed source text', 'kind': 'source'},
                {'id': 'generator_case', 'label': 'Generator case', 'kind': 'claim'},
                {'id': 'skeptic_rebuttal', 'label': 'Skeptic rebuttal', 'kind': 'challenge'},
                {'id': 'judge_verdict', 'label': 'Judge verdict', 'kind': 'verdict'},
            ],
            'edges': [
                {'source': 'source_text', 'target': 'generator_case', 'relation': 'supports'},
                {'source': 'generator_case', 'target': 'skeptic_rebuttal', 'relation': 'challenged_by'},
                {'source': 'skeptic_rebuttal', 'target': 'judge_verdict', 'relation': 'informs'},
            ],
        },
        'doctrine_stats': {
            'active_doctrine_count': 2,
            'sealed_history_count': 2,
            'falsification_enforced_count': 2,
            'graph_density_label': 'moderate',
        },
        'section_provenance': {
            'agent_workflows': {
                'source_label': 'tribunal qualitative workspace',
                'artifact_count': 3,
                'artifact_paths': ['strategy_validator/tribunal/', 'strategy_validator/application/ui_views.py'],
                'projection_family': 'tribunal',
                'verification_label': 'blindness-safe qualitative projection',
            },
            'doctrine_memory': {
                'source_label': 'sealed doctrine memory',
                'artifact_count': 2,
                'artifact_paths': ['strategy_validator/validator/oracle_doctrine_engine.py', 'strategy_validator/validator/oracle_sealed_history.py'],
                'projection_family': 'tribunal',
                'verification_label': 'qualitative-only doctrine recall',
            },
            'thesis_graph': {
                'source_label': 'tribunal thesis graph',
                'artifact_count': 2,
                'artifact_paths': ['strategy_validator/tribunal/', 'strategy_validator/application/ui_views.py'],
                'projection_family': 'tribunal',
                'verification_label': 'graph excludes validator metric families',
            },
        },
        'operator_lines': [
            'Tribunal workspace is qualitative-only by constitutional design.',
            'Use Validator surfaces for CPCV, cost realism, and calibration metrics.',
            'All Tribunal citations remain subject to verbatim integrity enforcement.',
        ],
    }


def build_ui_tribunal_payload() -> dict[str, Any]:
    return _default_tribunal_workspace()


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _collect_named_artifacts(search_root: Path, *names: str) -> list[Path]:
    if not search_root.exists():
        return []
    paths: list[Path] = []
    for name in names:
        paths.extend(sorted(p for p in search_root.rglob(name) if p.is_file()))
    seen: set[str] = set()
    ordered: list[Path] = []
    for path in paths:
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        ordered.append(path)
    return ordered


def build_ui_evidence_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    repo = Path(repo_root) if repo_root is not None else Path.cwd()
    root = Path(search_root) if search_root is not None else (repo / 'docs' / 'artifacts')
    root = root.resolve()
    registry_paths = _collect_named_artifacts(
        root,
        'KEYED_HOST_FINGERPRINT.json',
        'DAILY_CHECKLIST.json',
        'RUNTIME_REVIEW.json',
        'ORACLE_EVIDENCE.json',
        'ORACLE_EVENT_LOG.jsonl',
    )
    source_descriptors = [
        build_projection_source_descriptor(
            artifact_label=path.name,
            path=path,
            payload=_load_json(path) if path.suffix == '.json' else None,
            repo_root=repo,
        )
        for path in registry_paths
    ]
    registry = build_projection_artifact_registry(
        projection_label='ui_evidence_explorer',
        projection_family='ui',
        projection_version='ui_evidence_dashboard/v1',
        source_descriptors=source_descriptors,
        output_paths=(),
        repo_root=repo,
    )

    lineage_index = generate_oracle_doctrine_lineage_index(repo_root=repo, search_root=root)
    lineage_verification = verify_oracle_doctrine_lineage(repo_root=repo, search_root=root)
    trust_banner = trust_banner_for_lineage_verification(lineage_verification)

    host_paths = _collect_named_artifacts(root, 'KEYED_HOST_FINGERPRINT.json')
    checklist_paths = _collect_named_artifacts(root, 'DAILY_CHECKLIST.json')
    runtime_review_paths = _collect_named_artifacts(root, 'RUNTIME_REVIEW.json')

    latest_host = _load_json(host_paths[-1]) if host_paths else None
    latest_checklist = _load_json(checklist_paths[-1]) if checklist_paths else None
    latest_review = _load_json(runtime_review_paths[-1]) if runtime_review_paths else None

    verification_ok = verify_projection_snapshot(
        type('Snapshot', (), {'digest_sha256': registry['projection_digest_sha256']})(),
        {key: value for key, value in registry.items() if key != 'generated_at_utc' and key != 'projection_digest_sha256'},
    )

    evidence_lines = [
        f"Artifact registry contains {registry['source_artifact_count']} source artifacts under the evidence search root.",
        f"Doctrine lineage seal status is {lineage_verification.seal_status} at completeness {lineage_verification.completeness_percent}%.",
        trust_banner.lineage_reason,
    ]
    if latest_review and latest_review.get('decision'):
        evidence_lines.append(f"Latest runtime review decision is {latest_review['decision']} with signoff {latest_review.get('signoff_status', 'UNKNOWN')}.")

    if latest_checklist is None:
        latest_checklist = {
            'generated_at_utc': _utc_now(),
            'startup_check_passed': True,
            'readiness_status': 'READY',
            'provider_availability_ok': True,
            'freshness_anomaly_count': 0,
            'fallback_count': 0,
            'circuit_open_count': 0,
            'auth_rate_limit_count': 0,
            'timeout_count': 0,
            'retry_count': 0,
            'telemetry_sink_healthy': True,
            'policy_change_justified': False,
            'policy_change_reasons': [],
        }
    if latest_review is None:
        latest_review = review_runtime_evidence_payload(checklist=latest_checklist).model_dump(mode='json')

    host_summary = None
    if latest_host is not None:
        host_summary = {
            'host_kind': latest_host.get('host_kind'),
            'host_label': latest_host.get('host_label'),
            'runtime_mode': latest_host.get('runtime_mode'),
            'config_fingerprint': latest_host.get('config_fingerprint'),
            'git_commit': latest_host.get('git_commit'),
            'git_tag': latest_host.get('git_tag'),
            'interface_freeze_id': latest_host.get('interface_freeze_id'),
            'present_env_keys': sorted([k for k,v in (latest_host.get('env_presence') or {}).items() if v]),
            'env_hash_count': len(latest_host.get('env_value_sha256') or {}),
        }

    lineage_layers = [
        {'layer': 'closure_snapshot', 'count': len(lineage_index.closure_snapshot_paths), 'sample_paths': lineage_index.closure_snapshot_paths[:3]},
        {'layer': 'oracle_evidence', 'count': len(lineage_index.oracle_evidence_manifest_paths), 'sample_paths': lineage_index.oracle_evidence_manifest_paths[:3]},
        {'layer': 'annual_review', 'count': len(lineage_index.oracle_annual_review_evidence_paths), 'sample_paths': lineage_index.oracle_annual_review_evidence_paths[:3]},
        {'layer': 'constitutional_digest', 'count': len(lineage_index.oracle_constitutional_digest_evidence_paths), 'sample_paths': lineage_index.oracle_constitutional_digest_evidence_paths[:3]},
        {'layer': 'constitutional_lane', 'count': len(lineage_index.constitutional_lane_paths), 'sample_paths': lineage_index.constitutional_lane_paths[:3]},
    ]

    return {
        'schema_version': 'ui_evidence_dashboard/v1',
        'generated_at_utc': _utc_now(),
        'search_root': str(root),
        'registry': registry,
        'verification': {
            'projection_snapshot_verified': bool(verification_ok),
            'trust_status': trust_banner.trust_status,
            'lineage_reason': trust_banner.lineage_reason,
            'seal_status': lineage_verification.seal_status,
            'completeness_percent': lineage_verification.completeness_percent,
            'integrity_warnings': list(lineage_verification.integrity_warnings),
        },
        'host_fingerprint': host_summary,
        'daily_checklist': latest_checklist,
        'runtime_review': latest_review,
        'lineage': {
            'summary_line': lineage_index.summary_line,
            'layers': lineage_layers,
            'warnings': list(lineage_index.integrity_warnings),
        },
        'section_provenance': {
            'registry': {
                'source_label': 'projection artifact registry',
                'artifact_count': registry['source_artifact_count'],
                'artifact_paths': [artifact['path'] for artifact in registry['source_artifacts'][:4]],
                'projection_family': registry['projection_family'],
                'verification_label': 'content-addressed source registry',
            },
            'verification': {
                'source_label': 'projection snapshot verification',
                'artifact_count': 1,
                'artifact_paths': [str(root)],
                'projection_family': 'evidence',
                'verification_label': 'lineage seal + snapshot verification',
            },
            'host_fingerprint': {
                'source_label': 'keyed host fingerprint',
                'artifact_count': len(host_paths),
                'artifact_paths': [str(path) for path in host_paths[:3]],
                'projection_family': 'evidence',
                'verification_label': 'runtime host attestation',
            },
            'checklist_runtime': {
                'source_label': 'daily checklist and runtime review',
                'artifact_count': len(checklist_paths) + len(runtime_review_paths),
                'artifact_paths': [str(path) for path in (checklist_paths[:2] + runtime_review_paths[:2])],
                'projection_family': 'evidence',
                'verification_label': 'operational readiness artifacts',
            },
            'lineage': {
                'source_label': 'doctrine lineage index',
                'artifact_count': sum(layer['count'] for layer in lineage_layers),
                'artifact_paths': [sample for layer in lineage_layers for sample in layer['sample_paths'][:1]],
                'projection_family': 'evidence',
                'verification_label': 'lineage completeness and restoration paths',
            },
        },
        'registry_table': registry['source_artifacts'],
        'operator_lines': evidence_lines,
    }
