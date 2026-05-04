"""Application-layer façades for controlled rollout and release operations."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.validator.rollout_ops import (
    build_closure_release_attestation,
    build_closure_snapshot,
    build_daily_checklist,
    build_governed_exception_memo,
    build_rollout_bundle,
    default_startup_json_bundle,
    generate_host_fingerprint,
    generate_snapshot_signing_keypair,
    load_controlled_rollout_rules,
    parse_analyze_summary,
    render_decision_reconciliation_markdown,
    render_final_release_signoff_markdown,
    render_governed_exception_markdown,
    review_runtime_evidence,
    verify_closure_snapshot,
    verify_governed_exception_memo,
)


def generate_host_fingerprint_payload(
    *,
    host_kind,
    host_label: str | None = None,
    policy_path: str | Path,
    env_keys=None,
    now_utc=None,
):
    return generate_host_fingerprint(
        host_kind=host_kind,
        host_label=host_label,
        policy_path=Path(policy_path),
        env_keys=env_keys if env_keys is not None else ("APCA_API_KEY_ID", "APCA_API_SECRET_KEY", "STRATEGY_VALIDATOR_ALPACA_API_KEY_ID_ENV", "STRATEGY_VALIDATOR_ALPACA_API_SECRET_KEY_ENV"),
        now_utc=now_utc,
    )


def generate_snapshot_signing_keypair_payload(*, private_key_path: str | Path, public_key_path: str | Path):
    return generate_snapshot_signing_keypair(
        private_key_path=Path(private_key_path),
        public_key_path=Path(public_key_path),
    )


def build_rollout_bundle_payload(**kwargs):
    return build_rollout_bundle(**kwargs)


def parse_analyze_summary_payload(path: str | Path):
    return parse_analyze_summary(Path(path))


def default_startup_json_bundle_payload(*, startup_json: str | Path | None = None, readiness_json: str | Path | None = None):
    return default_startup_json_bundle()


def load_controlled_rollout_rules_payload(*, path: str | Path | None = None):
    return load_controlled_rollout_rules(Path(path) if path is not None else None)


def build_daily_checklist_payload(**kwargs):
    return build_daily_checklist(**kwargs)


def review_runtime_evidence_payload(**kwargs):
    return review_runtime_evidence(**kwargs)


def build_closure_snapshot_payload(**kwargs):
    return build_closure_snapshot(**kwargs)


def verify_closure_snapshot_payload(**kwargs):
    return verify_closure_snapshot(**kwargs)


def build_governed_exception_memo_payload(**kwargs):
    return build_governed_exception_memo(**kwargs)


def verify_governed_exception_memo_payload(**kwargs):
    return verify_governed_exception_memo(**kwargs)


def render_governed_exception_markdown_payload(*, memo):
    return render_governed_exception_markdown(memo)


def build_closure_release_attestation_payload(**kwargs):
    return build_closure_release_attestation(**kwargs)


def render_final_release_signoff_markdown_payload(*, manifest: Any, verification: Any, attestation: Any, **_: Any):
    return render_final_release_signoff_markdown(
        manifest=manifest,
        verification=verification,
        attestation=attestation,
    )


def render_decision_reconciliation_markdown_payload(*, manifest: Any, verification: Any, attestation: Any, **_: Any):
    return render_decision_reconciliation_markdown(
        manifest=manifest,
        verification=verification,
        attestation=attestation,
    )
