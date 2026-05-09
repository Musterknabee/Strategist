from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_view_helpers import utc_now_iso

_utc_now = utc_now_iso

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
        'summary': {
            'workflow_count': 3,
            'ready_workflow_count': 3,
            'prompt_evaluation_count': 2,
            'falsification_check_count': 2,
            'sealed_history_count': 2,
            'active_doctrine_count': 2,
            'thesis_graph_node_count': 4,
            'thesis_graph_edge_count': 3,
            'quantitative_metric_family_count': 0,
            'read_plane_only': True,
        },
        'guardrails': {
            'read_plane_only': True,
            'mutation_authority': 'NONE',
            'promotion_authority': 'NONE',
            'execution_authority': 'NONE',
            'blindness_enforced': True,
            'quantitative_payloads_present': False,
        },
        'section_provenance': {
            'agent_workflows': {
                'source_label': 'tribunal qualitative workspace',
                'artifact_count': 3,
                'artifact_paths': ['strategy_validator/tribunal/', 'strategy_validator/application/ui_detail_views.py'],
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
                'artifact_paths': ['strategy_validator/tribunal/', 'strategy_validator/application/ui_detail_views.py'],
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
