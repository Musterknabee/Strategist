"""Shared helpers for oracle event/constitutional CLI runners."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.cli.oracle_cli_common import emit_report, print_or_write_payload, write_json, write_markdown
from strategy_validator.cli.application_event_surfaces import (
    append_annual_review_to_lane_payload,
    append_constitutional_digest_to_lane_payload,
    append_doctrine_drift_to_lane_payload,
    append_memory_review_to_lane_payload,
    append_monthly_digest_to_lane_payload,
    append_quarterly_review_to_lane_payload,
    append_semiannual_audit_to_lane_payload,
    append_state_transition_to_lane_payload,
    legacy_compatibility_banner_payload,
)
from strategy_validator.cli.oracle_rollout_legacy_helpers import (
    _write_text_output,
    append_explanation_markdown as _append_explanation_markdown,
    constitutional_gate_banner as _constitutional_gate_banner,
    legacy_banner_with_trust as _legacy_banner_with_trust,
    lineage_banner as _lineage_banner,
    require_legacy_lane_read_opt_in as _require_legacy_lane_read_opt_in,
    run_legacy_horizon_report as _run_legacy_horizon_report,
    run_verify_and_append_manifest as _run_verify_and_append_manifest,
    run_verify_manifest as _run_verify_manifest,
)


def _legacy_banner(surface: str) -> str:
    return legacy_compatibility_banner_payload(legacy_surface=surface)


__all__ = ['_append_explanation_markdown', '_constitutional_gate_banner', '_legacy_banner', '_legacy_banner_with_trust', '_lineage_banner', '_require_legacy_lane_read_opt_in', '_run_legacy_horizon_report', '_run_verify_and_append_manifest', '_run_verify_manifest', '_write_text_output', 'append_annual_review_to_lane_payload', 'append_constitutional_digest_to_lane_payload', 'append_doctrine_drift_to_lane_payload', 'append_memory_review_to_lane_payload', 'append_monthly_digest_to_lane_payload', 'append_quarterly_review_to_lane_payload', 'append_semiannual_audit_to_lane_payload', 'append_state_transition_to_lane_payload', 'emit_report', 'json', 'Path', 'print_or_write_payload', 'sys', 'write_json', 'write_markdown']
