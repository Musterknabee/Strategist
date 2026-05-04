"""Build digest-linked paper broker status artifacts (read-plane evidence)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from strategy_validator.brokers.alpaca_paper import evaluate_alpaca_paper_policy, get_alpaca_paper_account
from strategy_validator.contracts.paper_broker import PaperBrokerPolicyStatus, PaperBrokerStatusArtifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _endpoint_class(env: dict[str, str]) -> str:
    base = (env.get("ALPACA_BASE_URL") or "").strip().lower()
    if not base:
        return "UNSET"
    if "paper-api" in base:
        return "PAPER_HOST"
    if "alpaca" in base:
        return "LIVE_HOST_BLOCKED"
    return "UNKNOWN"


def build_paper_broker_status_artifact(
    env: dict[str, str],
    *,
    allow_network: bool = False,
) -> PaperBrokerStatusArtifact:
    pol, warns, blocks = evaluate_alpaca_paper_policy(env)
    now = datetime.now(timezone.utc)
    mode = (env.get("ALPACA_TRADING_MODE") or "").strip() or None
    key = bool((env.get("ALPACA_API_KEY") or "").strip() and (env.get("ALPACA_API_SECRET") or "").strip())
    ep = _endpoint_class(env)
    live_blocked = pol != PaperBrokerPolicyStatus.PAPER_READY or ep == "LIVE_HOST_BLOCKED"
    acct_summary = None
    w = list(warns)
    b = list(blocks)
    if pol == PaperBrokerPolicyStatus.PAPER_READY and allow_network:
        acct = get_alpaca_paper_account(env, allow_network=True)
        w.extend(acct.warnings)
        acct_summary = {
            "account_id": acct.account_id,
            "equity": acct.equity,
            "buying_power": acct.buying_power,
            "currency": acct.currency,
            "paper_endpoint_verified": acct.paper_endpoint_verified,
        }
    elif pol == PaperBrokerPolicyStatus.PAPER_READY and not allow_network:
        w.append("ACCOUNT_PROBE_SKIPPED_ALLOW_NETWORK_FALSE")

    art = PaperBrokerStatusArtifact(
        generated_at_utc=now,
        broker_id="alpaca_paper",
        mode=mode,
        endpoint_classification=ep,
        key_configured=key,
        policy_status=pol.value,
        paper_trading_only=True,
        live_trading_blocked=True,
        account_summary=acct_summary,
        warnings=w,
        blockers=b,
    )
    body = art.model_dump(mode="json")
    body.pop("manifest_sha256", None)
    return art.model_copy(update={"manifest_sha256": canonical_json_sha256(body)})


def write_paper_broker_status_artifact(output_root: Path, art: PaperBrokerStatusArtifact) -> Path:
    latest = output_root.resolve() / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    path = latest / "paper_broker_status.json"
    path.write_text(json.dumps(art.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


__all__ = ["build_paper_broker_status_artifact", "write_paper_broker_status_artifact"]
