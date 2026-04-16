"""Transition and memory-review CLI runners."""
from __future__ import annotations

from pathlib import Path
import argparse
import json
import sys

from strategy_validator.application import (
    build_annual_review_evidence_bundle_payload,
    build_annual_review_payload,
    build_constitutional_digest_evidence_bundle_payload,
    build_constitutional_digest_payload,
    build_constitutional_gate_payload,
    build_doctrine_drift_evidence_bundle_payload,
    build_doctrine_drift_payload,
    build_doctrine_lineage_index_payload,
    build_memory_lane_summary_payload,
    build_memory_review_evidence_bundle_payload,
    build_memory_review_payload,
    build_monthly_digest_evidence_bundle_payload,
    build_monthly_digest_payload,
    build_quarterly_review_evidence_bundle_payload,
    build_quarterly_review_payload,
    build_semiannual_audit_evidence_bundle_payload,
    build_semiannual_audit_payload,
    build_state_transition_evidence_bundle_payload,
    build_state_transition_payload,
    build_weekly_digest_evidence_bundle_payload,
    build_weekly_digest_payload,
    compare_weekly_digest_payloads,
    explain_checkpoint_from_paths_payload,
    explain_constitutional_gate_payload,
    explain_lineage_verification_payload,
    explain_report_from_path_payload,
    render_annual_review_markdown_payload,
    render_constitutional_digest_markdown_payload,
    render_constitutional_gate_markdown_payload,
    render_doctrine_drift_markdown_payload,
    render_doctrine_lineage_index_markdown_payload,
    render_doctrine_lineage_verification_markdown_payload,
    render_memory_lane_summary_markdown_payload,
    render_memory_review_markdown_payload,
    render_monthly_digest_markdown_payload,
    render_oracle_explanation_markdown_payload,
    render_quarterly_review_markdown_payload,
    render_semiannual_audit_markdown_payload,
    render_state_transition_markdown_payload,
    render_weekly_digest_markdown_payload,
    verify_annual_review_evidence_bundle_payload,
    verify_constitutional_digest_evidence_bundle_payload,
    verify_doctrine_drift_evidence_bundle_payload,
    verify_doctrine_lineage_payload,
    verify_memory_review_evidence_bundle_payload,
    verify_monthly_digest_evidence_bundle_payload,
    verify_quarterly_review_evidence_bundle_payload,
    verify_semiannual_audit_evidence_bundle_payload,
    verify_state_transition_evidence_bundle_payload,
    verify_weekly_digest_evidence_bundle_payload,
)
from strategy_validator.cli.oracle_event_constitutional_runner_common import *
def cmd_oracle_transition(ns: argparse.Namespace) -> int:
    report = build_state_transition_payload(
        previous_manifest_path=Path(ns.previous_manifest),
        current_manifest_path=Path(ns.current_manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        previous_dsse_path=Path(ns.previous_dsse) if ns.previous_dsse else None,
        current_dsse_path=Path(ns.current_dsse) if ns.current_dsse else None,
        previous_public_key_path=Path(ns.previous_public_key) if ns.previous_public_key else None,
        current_public_key_path=Path(ns.current_public_key) if ns.current_public_key else None,
    )
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.markdown_output).write_text(render_state_transition_markdown_payload(report), encoding="utf-8")
    return 0 if report.comparison_status == "VERIFIED" else 2

def cmd_oracle_transition_evidence(ns: argparse.Namespace) -> int:
    report = build_state_transition_payload(
        previous_manifest_path=Path(ns.previous_manifest),
        current_manifest_path=Path(ns.current_manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        previous_dsse_path=Path(ns.previous_dsse) if ns.previous_dsse else None,
        current_dsse_path=Path(ns.current_dsse) if ns.current_dsse else None,
        previous_public_key_path=Path(ns.previous_public_key) if ns.previous_public_key else None,
        current_public_key_path=Path(ns.current_public_key) if ns.current_public_key else None,
    )
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.current_manifest).with_name("ORACLE_STATE_TRANSITION_REPORT.json")
    write_json(report_output, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_state_transition_markdown_payload(report), encoding="utf-8")
    manifest, envelope = build_state_transition_evidence_bundle_payload(
        previous_manifest_path=Path(ns.previous_manifest),
        current_manifest_path=Path(ns.current_manifest),
        report_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_TRANSITION_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_state_transition_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output and dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_TRANSITION_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2

def cmd_verify_oracle_transition_evidence(ns: argparse.Namespace) -> int:
    verification = verify_state_transition_evidence_bundle_payload(
        manifest_path=Path(ns.manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    payload = verification.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2

def cmd_oracle_memory_append(ns: argparse.Namespace) -> int:
    verification = verify_state_transition_evidence_bundle_payload(
        manifest_path=Path(ns.manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else Path(ns.manifest).with_name("ORACLE_TRANSITION_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    try:
        entry = append_state_transition_to_lane_payload(
            manifest_path=Path(ns.manifest),
            verification=verification,
            lane_path=Path(ns.lane_path),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    entry_output = Path(ns.output) if ns.output else Path(ns.manifest).with_name("ORACLE_MEMORY_LANE_ENTRY.json")
    write_json(entry_output, entry.model_dump(mode="json"))
    sys.stdout.write(json.dumps(entry.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0

def cmd_oracle_memory_summary(ns: argparse.Namespace) -> int:
    summary = build_memory_lane_summary_payload(lane_path=Path(ns.lane_path))
    payload = summary.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.markdown_output).write_text(render_memory_lane_summary_markdown_payload(summary), encoding="utf-8")
    return 0

def cmd_oracle_memory_review(ns: argparse.Namespace) -> int:
    review = build_memory_review_payload(
        lane_path=Path(ns.lane_path),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        window_size=ns.window_size,
    )
    payload = review.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.markdown_output).write_text(render_memory_review_markdown_payload(review), encoding="utf-8")
    return 0

def cmd_oracle_memory_review_evidence(ns: argparse.Namespace) -> int:
    review = build_memory_review_payload(
        lane_path=Path(ns.lane_path),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        window_size=ns.window_size,
    )
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.lane_path).with_name("ORACLE_MEMORY_REVIEW_REPORT.json")
    write_json(report_output, review.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    markdown_output.write_text(render_memory_review_markdown_payload(review), encoding="utf-8")
    manifest, envelope = build_memory_review_evidence_bundle_payload(
        source_memory_lane_path=Path(ns.lane_path),
        review_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_MEMORY_REVIEW_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_memory_review_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output and dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_MEMORY_REVIEW_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2

def cmd_verify_oracle_memory_review_evidence(ns: argparse.Namespace) -> int:
    verification = verify_memory_review_evidence_bundle_payload(
        manifest_path=Path(ns.manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    payload = verification.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2

def cmd_oracle_review_lane_append(ns: argparse.Namespace) -> int:
    verification = verify_memory_review_evidence_bundle_payload(
        manifest_path=Path(ns.manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else Path(ns.manifest).with_name("ORACLE_MEMORY_REVIEW_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    try:
        entry = append_memory_review_to_lane_payload(
            manifest_path=Path(ns.manifest),
            verification=verification,
            lane_path=Path(ns.lane_path),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    entry_output = Path(ns.output) if ns.output else Path(ns.manifest).with_name("ORACLE_REVIEW_LANE_ENTRY.json")
    write_json(entry_output, entry.model_dump(mode="json"))
    sys.stdout.write(json.dumps(entry.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0

