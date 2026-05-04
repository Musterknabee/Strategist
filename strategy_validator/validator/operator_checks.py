"""
Operator-facing validation helpers (startup / remediation text).

Kept separate from adjudication so failures here are advisory unless wired
into readiness by explicit policy.
"""
from __future__ import annotations

import json
from typing import List, Tuple

from strategy_validator.core.config import AppConfig, load_config
from strategy_validator.validator.observability import export_operational_state, get_runtime_blocker_summaries
from strategy_validator.validator.readiness import perform_readiness_check


def validate_alpaca_market_data_connector(cfg: AppConfig) -> List[Tuple[str, str]]:
    """Validate Alpaca connector env when enabled (secrets must exist, HTTPS base URL)."""
    issues: List[Tuple[str, str]] = []
    ac = cfg.market_data_alpaca_connector
    if ac is None or not ac.enabled:
        return issues
    if not str(ac.data_base_url).lower().startswith("https://"):
        issues.append(
            ("ALPACA_INSECURE_BASE_URL", "Alpaca data_base_url must use https:// for operator deployments."),
        )
    import os

    kid = os.environ.get(ac.api_key_id_env, "").strip()
    sec = os.environ.get(ac.api_secret_key_env, "").strip()
    if not kid or not sec:
        issues.append(
            (
                "ALPACA_CREDENTIALS_MISSING",
                f"Set non-empty {ac.api_key_id_env} and {ac.api_secret_key_env} for Alpaca Market Data.",
            ),
        )
    if ac.enable_borrow_from_trading_api:
        if not str(ac.trading_base_url).lower().startswith("https://"):
            issues.append(
                (
                    "ALPACA_INSECURE_TRADING_BASE_URL",
                    "Alpaca trading_base_url must use https:// when borrow/locate is enabled.",
                ),
            )
    return issues




def validate_openbb_market_data_connector(cfg: AppConfig) -> List[Tuple[str, str]]:
    """Validate optional OpenBB connector settings."""
    issues: List[Tuple[str, str]] = []
    oc = cfg.market_data_openbb_connector
    if oc is None or not oc.enabled:
        return issues
    if oc.mode == "http":
        if not (
            oc.base_url
            or oc.liquidity_url_template
            or oc.borrow_url_template
            or getattr(oc, "oracle_macro_url_template", "")
            or getattr(oc, "oracle_microstructure_url_template", "")
        ):
            issues.append(("OPENBB_MISCONFIGURED", "OpenBB HTTP mode requires a base_url or at least one URL template."))
        if oc.base_url and not str(oc.base_url).lower().startswith("https://"):
            issues.append(("OPENBB_INSECURE_BASE_URL", "OpenBB base_url should use https:// for operator deployments."))
    elif oc.mode != "python":
        issues.append(("OPENBB_MODE_INVALID", f"Unsupported OpenBB mode {oc.mode!r}; use 'http' or 'python'."))
    if oc.api_key_env_var:
        import os

        if oc.api_key_env_var not in os.environ or not os.environ.get(oc.api_key_env_var, "").strip():
            issues.append(("OPENBB_SECRET_MISSING", f"Referenced API key env var {oc.api_key_env_var!r} is unset or empty."))
    return issues



def validate_nvidia_nim_connector(cfg: AppConfig) -> List[Tuple[str, str]]:
    """Validate optional NVIDIA NIM semantic connector settings."""
    issues: List[Tuple[str, str]] = []
    nc = cfg.semantic_nvidia_nim_connector
    if nc is None or not nc.enabled:
        return issues
    if not str(nc.base_url).lower().startswith("https://"):
        issues.append(("NVIDIA_NIM_INSECURE_BASE_URL", "NVIDIA NIM base_url must use https://."))
    import os

    if nc.api_key_env not in os.environ or not os.environ.get(nc.api_key_env, "").strip():
        issues.append(("NVIDIA_NIM_CREDENTIALS_MISSING", f"Set non-empty {nc.api_key_env} for NVIDIA NIM access."))
    return issues


def validate_http_market_data_connector(cfg: AppConfig) -> List[Tuple[str, str]]:
    """
    Validate optional HTTP JSON market-data connector settings.

    Returns a list of (code, message) tuples (non-fatal unless operators treat as blockers).
    """
    issues: List[Tuple[str, str]] = []
    mdc = cfg.market_data_http_connector
    if mdc is None or not mdc.enabled:
        return issues
    if not mdc.liquidity_url_template.strip() and not mdc.borrow_url_template.strip():
        issues.append(
            ("HTTP_MARKET_DATA_MISCONFIGURED", "HTTP connector enabled but both URL templates are empty."),
        )
    if mdc.api_key_env_var:
        import os

        if mdc.api_key_env_var not in os.environ or not os.environ.get(mdc.api_key_env_var, "").strip():
            issues.append(
                ("HTTP_MARKET_DATA_SECRET_MISSING", f"Referenced API key env var {mdc.api_key_env_var!r} is unset or empty."),
            )
    return issues


def run_startup_self_check() -> Tuple[int, str]:
    """
    Run consolidated startup checks for operators / init containers.

    Returns (exit_code, human_text) where exit_code 0 means readiness READY
    and no HTTP connector misconfiguration was detected.
    """
    readiness = perform_readiness_check()
    cfg = load_config()
    http_issues = validate_http_market_data_connector(cfg)
    alpaca_issues = validate_alpaca_market_data_connector(cfg)
    openbb_issues = validate_openbb_market_data_connector(cfg)
    nim_issues = validate_nvidia_nim_connector(cfg)

    lines: List[str] = [
        f"readiness_status={readiness.status}",
        f"adjudication_allowed={readiness.adjudication_allowed}",
        f"schema_version={readiness.schema_version} expected={readiness.expected_schema_version}",
        f"mutation_authorization_mode={readiness.mutation_safety.authorization_mode}",
        f"mutation_token_configured={readiness.mutation_safety.token_configured}",
        f"mutation_routes_safe={readiness.mutation_safety.mutation_routes_safe}",
    ]
    for b in readiness.blockers:
        lines.append(f"BLOCKER {b.code}: {b.message}")
    for w in readiness.warnings:
        lines.append(f"WARNING {w.code}: {w.message}")
    for code, msg in http_issues:
        lines.append(f"CONNECTOR_ISSUE {code}: {msg}")
    for code, msg in alpaca_issues:
        lines.append(f"ALPACA_ISSUE {code}: {msg}")
    for code, msg in openbb_issues:
        lines.append(f"OPENBB_ISSUE {code}: {msg}")
    for code, msg in nim_issues:
        lines.append(f"NVIDIA_NIM_ISSUE {code}: {msg}")

    exit_code = 0
    if readiness.status != "READY":
        exit_code = 1
    if http_issues or alpaca_issues or openbb_issues or nim_issues:
        exit_code = 1

    return exit_code, "\n".join(lines) + "\n"


def export_startup_json_bundle() -> str:
    """JSON bundle: heartbeat + health + blocker summaries + connector validation."""
    blockers = get_runtime_blocker_summaries()
    base = json.loads(export_operational_state(format="json"))
    base["runtime_blocker_summaries"] = [b.model_dump(mode="json") for b in blockers]
    cfg = load_config()
    base["http_market_data_connector_issues"] = [
        {"code": c, "message": m} for c, m in validate_http_market_data_connector(cfg)
    ]
    base["alpaca_market_data_connector_issues"] = [
        {"code": c, "message": m} for c, m in validate_alpaca_market_data_connector(cfg)
    ]
    base["openbb_market_data_connector_issues"] = [
        {"code": c, "message": m} for c, m in validate_openbb_market_data_connector(cfg)
    ]
    base["nvidia_nim_connector_issues"] = [
        {"code": c, "message": m} for c, m in validate_nvidia_nim_connector(cfg)
    ]
    return json.dumps(base, indent=2, default=str)
