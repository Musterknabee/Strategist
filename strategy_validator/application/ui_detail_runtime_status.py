from __future__ import annotations

from typing import Any

from strategy_validator.api.auth import get_mutation_auth_runtime_status
from strategy_validator.application.ui_view_helpers import utc_now_iso
from strategy_validator.core.config import load_config

_utc_now = utc_now_iso

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
        base = (
            getattr(settings, 'base_url', None)
            or getattr(settings, 'data_base_url', None)
            or getattr(settings, 'liquidity_url_template', None)
            or 'configured'
        )
        rows.append({
            'provider': provider,
            'status': 'ENABLED' if enabled else 'DISABLED',
            'path': str(base),
        })
    return rows

def build_ui_runtime_status_payload(*, role: str = 'operator') -> dict[str, Any]:
    cfg = load_config()
    provider_paths = _build_provider_paths()
    enabled_provider_count = sum(1 for row in provider_paths if row.get('status') == 'ENABLED')
    backend_reachability = 'CONFIGURED' if enabled_provider_count > 0 else 'DEGRADED'

    normalized_role = str(role or 'operator').strip().lower()
    policy_map = {
        'operator': {
            'label': 'Operator',
            'allowed_domains': ['control-plane', 'validator', 'tribunal', 'evidence'],
            'redacted_domains': [],
            'allowed_actions': ['claim-item', 'acknowledge-reentry', 'renew-lease'],
            'default_route': '/workboard',
            'operator_hint': 'Operate queue and pack commands through governed command routes, then wait for projection refresh.',
        },
        'validator': {
            'label': 'Validator',
            'allowed_domains': ['validator', 'evidence', 'control-plane'],
            'redacted_domains': ['tribunal'],
            'allowed_actions': [],
            'default_route': '/validator/burn-in',
            'operator_hint': 'Validator persona is read-mostly. Review burn-in, realism, and evidence without issuing operator queue commands.',
        },
        'tribunal': {
            'label': 'Tribunal',
            'allowed_domains': ['tribunal', 'evidence'],
            'redacted_domains': ['validator', 'control-plane'],
            'allowed_actions': [],
            'default_route': '/tribunal',
            'operator_hint': 'Tribunal persona is qualitative-only. Validator quantitative metrics and control-plane commands remain redacted.',
        },
    }
    active_policy = policy_map.get(normalized_role, policy_map['operator'])
    mutation_safety = get_mutation_auth_runtime_status()
    return {
        'schema_version': 'ui_runtime_status/v1',
        'generated_at_utc': _utc_now(),
        'environment': str(cfg.mode),
        'persona': {
            'active_role': normalized_role if normalized_role in policy_map else 'operator',
            'active_label': active_policy['label'],
            'available_roles': ['operator', 'validator', 'tribunal'],
            'default_route': active_policy['default_route'],
        },
        'policy': {
            'allowed_domains': active_policy['allowed_domains'],
            'redacted_domains': active_policy['redacted_domains'],
            'allowed_actions': active_policy['allowed_actions'],
        },
        'read_plane': {
            'status': 'LIVE',
            'freshness_status': 'FRESH',
            'operator_message': 'Projection reads are command-gated and audit-visible.',
        },
        'backend': {
            'status': backend_reachability,
            'base_mode': str(cfg.mode),
            'operator_message': 'UI reads are served through backend UI projection routes.',
        },
        'blindness': {
            'tribunal_mode': 'ENFORCED',
            'operator_message': 'Tribunal workspace excludes validator quantitative metrics by design.',
        },
        'providers': {
            'enabled_count': enabled_provider_count,
            'items': provider_paths,
        },
        'command_bar': {
            'allowed_actions': active_policy['allowed_actions'],
            'operator_hint': active_policy['operator_hint'],
        },
        'mutation_safety': mutation_safety.model_dump(mode='json'),
    }
