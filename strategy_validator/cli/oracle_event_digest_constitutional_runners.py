"""Digest, doctrine, constitutional, and explanation CLI runners."""
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
def cmd_oracle_weekly_digest(ns: argparse.Namespace) -> int:
    return _run_legacy_horizon_report(
        ns,
        horizon="weekly",
        legacy_surface="oracle-weekly-digest",
        generate_fn=build_weekly_digest_payload,
        render_markdown_fn=render_weekly_digest_markdown_payload,
    )

def cmd_oracle_weekly_digest_evidence(ns: argparse.Namespace) -> int:
    lane_guard = _require_legacy_lane_read_opt_in(ns, legacy_surface="oracle-weekly-digest-evidence")
    if lane_guard is not None:
        return lane_guard
    digest = build_weekly_digest_payload(
        lane_path=Path(ns.lane_path),
        window_size=ns.window_size,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    digest_output = Path(ns.report_output) if ns.report_output else Path(ns.lane_path).with_name("ORACLE_WEEKLY_DIGEST.json")
    write_json(digest_output, digest.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else digest_output.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(markdown_output, render_weekly_digest_markdown_payload(digest), banner=_legacy_banner_with_trust(legacy_surface="oracle-weekly-digest", report=digest, lane_path=Path(ns.lane_path)))
    manifest, envelope = build_weekly_digest_evidence_bundle_payload(
        source_review_lane_path=Path(ns.lane_path),
        digest_path=digest_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else digest_output.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_weekly_digest_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output and dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2

def cmd_verify_oracle_weekly_digest_evidence(ns: argparse.Namespace) -> int:
    verification = verify_weekly_digest_evidence_bundle_payload(
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

def cmd_oracle_doctrine_drift(ns: argparse.Namespace) -> int:
    report = compare_weekly_digest_payloads(
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
        Path(ns.markdown_output).write_text(render_doctrine_drift_markdown_payload(report), encoding="utf-8")
    return 0 if report.comparison_status == "VERIFIED" else 2

def cmd_oracle_doctrine_drift_evidence(ns: argparse.Namespace) -> int:
    report = compare_weekly_digest_payloads(
        previous_manifest_path=Path(ns.previous_manifest),
        current_manifest_path=Path(ns.current_manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        previous_dsse_path=Path(ns.previous_dsse) if ns.previous_dsse else None,
        current_dsse_path=Path(ns.current_dsse) if ns.current_dsse else None,
        previous_public_key_path=Path(ns.previous_public_key) if ns.previous_public_key else None,
        current_public_key_path=Path(ns.current_public_key) if ns.current_public_key else None,
    )
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.current_manifest).with_name("ORACLE_DOCTRINE_DRIFT_REPORT.json")
    write_json(report_output, report.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(markdown_output, render_doctrine_drift_markdown_payload(report), banner=_legacy_banner_with_trust(legacy_surface="oracle-doctrine-drift", report=report, lane_path=Path(ns.current_manifest)))
    manifest, envelope = build_doctrine_drift_evidence_bundle_payload(
        source_previous_digest_path=Path(ns.previous_manifest),
        source_current_digest_path=Path(ns.current_manifest),
        report_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_DOCTRINE_DRIFT_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_doctrine_drift_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output and dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_DOCTRINE_DRIFT_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2

def cmd_verify_oracle_doctrine_drift_evidence(ns: argparse.Namespace) -> int:
    verification = verify_doctrine_drift_evidence_bundle_payload(
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

def cmd_oracle_doctrine_lane_append(ns: argparse.Namespace) -> int:
    verification = verify_doctrine_drift_evidence_bundle_payload(
        manifest_path=Path(ns.manifest),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=Path(ns.dsse) if ns.dsse else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else Path(ns.manifest).with_name("ORACLE_DOCTRINE_DRIFT_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    try:
        entry = append_doctrine_drift_to_lane_payload(
            manifest_path=Path(ns.manifest),
            verification=verification,
            lane_path=Path(ns.lane_path),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    entry_output = Path(ns.output) if ns.output else Path(ns.manifest).with_name("ORACLE_DOCTRINE_LANE_ENTRY.json")
    write_json(entry_output, entry.model_dump(mode="json"))
    sys.stdout.write(json.dumps(entry.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0

def cmd_oracle_monthly_digest(ns: argparse.Namespace) -> int:
    return _run_legacy_horizon_report(
        ns,
        horizon="monthly",
        legacy_surface="oracle-monthly-digest",
        generate_fn=build_monthly_digest_payload,
        render_markdown_fn=render_monthly_digest_markdown_payload,
    )

def cmd_oracle_monthly_digest_evidence(ns: argparse.Namespace) -> int:
    lane_guard = _require_legacy_lane_read_opt_in(ns, legacy_surface="oracle-monthly-digest-evidence")
    if lane_guard is not None:
        return lane_guard
    digest = build_monthly_digest_payload(
        lane_path=Path(ns.lane_path),
        window_size=ns.window_size,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.lane_path).with_name("ORACLE_MONTHLY_DIGEST.json")
    write_json(report_output, digest.model_dump(mode="json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_suffix(".md")
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(markdown_output, render_monthly_digest_markdown_payload(digest), banner=_legacy_banner_with_trust(legacy_surface="oracle-monthly-digest", report=digest, lane_path=Path(ns.lane_path)))
    manifest, envelope = build_monthly_digest_evidence_bundle_payload(
        source_doctrine_lane_path=Path(ns.lane_path),
        digest_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_MONTHLY_DIGEST_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_monthly_digest_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output and dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_MONTHLY_DIGEST_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2

def cmd_verify_oracle_monthly_digest_evidence(ns: argparse.Namespace) -> int:
    status, _ = _run_verify_manifest(ns, verify_fn=verify_monthly_digest_evidence_bundle_payload)
    return status

def cmd_oracle_monthly_lane_append(ns: argparse.Namespace) -> int:
    return _run_verify_and_append_manifest(
        ns,
        verify_fn=verify_monthly_digest_evidence_bundle_payload,
        append_fn=append_monthly_digest_to_lane_payload,
        default_verification_name="ORACLE_MONTHLY_DIGEST_EVIDENCE.verification.json",
        default_entry_name="ORACLE_MONTHLY_LANE_ENTRY.json",
    )

def cmd_oracle_quarterly_review(ns: argparse.Namespace) -> int:
    return _run_legacy_horizon_report(
        ns,
        horizon="quarterly",
        legacy_surface="oracle-quarterly-review",
        generate_fn=build_quarterly_review_payload,
        render_markdown_fn=render_quarterly_review_markdown_payload,
    )

def cmd_oracle_quarterly_review_evidence(ns: argparse.Namespace) -> int:
    lane_guard = _require_legacy_lane_read_opt_in(ns, legacy_surface="oracle-quarterly-review-evidence")
    if lane_guard is not None:
        return lane_guard
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.lane_path).with_name("ORACLE_QUARTERLY_REVIEW.json")
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_name("ORACLE_QUARTERLY_REVIEW.md")
    report = build_quarterly_review_payload(
        lane_path=Path(ns.lane_path),
        window_size=ns.window_size,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    write_json(report_output, report.model_dump(mode="json"))
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(markdown_output, render_quarterly_review_markdown_payload(report), banner=_legacy_banner_with_trust(legacy_surface="oracle-quarterly-review", report=report, lane_path=Path(ns.lane_path)))
    manifest, envelope = build_quarterly_review_evidence_bundle_payload(
        source_monthly_lane_path=Path(ns.lane_path),
        report_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_QUARTERLY_REVIEW_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_name("ORACLE_QUARTERLY_REVIEW_EVIDENCE.dsse.json")
    if envelope is not None:
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_quarterly_review_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_QUARTERLY_REVIEW_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0

def cmd_verify_oracle_quarterly_review_evidence(ns: argparse.Namespace) -> int:
    status, _ = _run_verify_manifest(ns, verify_fn=verify_quarterly_review_evidence_bundle_payload)
    return status

def cmd_oracle_quarterly_lane_append(ns: argparse.Namespace) -> int:
    return _run_verify_and_append_manifest(
        ns,
        verify_fn=verify_quarterly_review_evidence_bundle_payload,
        append_fn=append_quarterly_review_to_lane_payload,
        default_verification_name="ORACLE_QUARTERLY_REVIEW_EVIDENCE.verification.json",
        default_entry_name="ORACLE_QUARTERLY_LANE_ENTRY.json",
    )

def cmd_oracle_semiannual_audit(ns: argparse.Namespace) -> int:
    return _run_legacy_horizon_report(
        ns,
        horizon="semiannual",
        legacy_surface="oracle-semiannual-audit",
        generate_fn=build_semiannual_audit_payload,
        render_markdown_fn=render_semiannual_audit_markdown_payload,
    )

def cmd_oracle_semiannual_audit_evidence(ns: argparse.Namespace) -> int:
    lane_guard = _require_legacy_lane_read_opt_in(ns, legacy_surface="oracle-semiannual-audit-evidence")
    if lane_guard is not None:
        return lane_guard
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.lane_path).with_name("ORACLE_SEMIANNUAL_AUDIT.json")
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_name("ORACLE_SEMIANNUAL_AUDIT.md")
    report = build_semiannual_audit_payload(
        lane_path=Path(ns.lane_path),
        window_size=ns.window_size,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    write_json(report_output, report.model_dump(mode="json"))
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(markdown_output, render_semiannual_audit_markdown_payload(report), banner=_legacy_banner_with_trust(legacy_surface="oracle-semiannual-audit", report=report, lane_path=Path(ns.lane_path)))
    manifest, envelope = build_semiannual_audit_evidence_bundle_payload(
        source_quarterly_lane_path=Path(ns.lane_path),
        report_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_name("ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.dsse.json")
    if envelope is not None:
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_semiannual_audit_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0

def cmd_verify_oracle_semiannual_audit_evidence(ns: argparse.Namespace) -> int:
    status, _ = _run_verify_manifest(ns, verify_fn=verify_semiannual_audit_evidence_bundle_payload)
    return status

def cmd_oracle_semiannual_lane_append(ns: argparse.Namespace) -> int:
    return _run_verify_and_append_manifest(
        ns,
        verify_fn=verify_semiannual_audit_evidence_bundle_payload,
        append_fn=append_semiannual_audit_to_lane_payload,
        default_verification_name="ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json",
        default_entry_name="ORACLE_SEMIANNUAL_LANE_ENTRY.json",
    )

def cmd_oracle_annual_review(ns: argparse.Namespace) -> int:
    return _run_legacy_horizon_report(
        ns,
        horizon="annual",
        legacy_surface="oracle-annual-review",
        generate_fn=build_annual_review_payload,
        render_markdown_fn=render_annual_review_markdown_payload,
    )

def cmd_oracle_annual_review_evidence(ns: argparse.Namespace) -> int:
    lane_guard = _require_legacy_lane_read_opt_in(ns, legacy_surface="oracle-annual-review-evidence")
    if lane_guard is not None:
        return lane_guard
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.lane_path).with_name("ORACLE_ANNUAL_REVIEW.json")
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_name("ORACLE_ANNUAL_REVIEW.md")
    report = build_annual_review_payload(
        lane_path=Path(ns.lane_path),
        window_size=ns.window_size,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    write_json(report_output, report.model_dump(mode="json"))
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(markdown_output, render_annual_review_markdown_payload(report), banner=_legacy_banner_with_trust(legacy_surface="oracle-annual-review", report=report, lane_path=Path(ns.lane_path)))
    manifest, envelope = build_annual_review_evidence_bundle_payload(
        source_semiannual_lane_path=Path(ns.lane_path),
        report_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_ANNUAL_REVIEW_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_name("ORACLE_ANNUAL_REVIEW_EVIDENCE.dsse.json")
    if envelope is not None:
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_annual_review_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0

def cmd_verify_oracle_annual_review_evidence(ns: argparse.Namespace) -> int:
    status, _ = _run_verify_manifest(ns, verify_fn=verify_annual_review_evidence_bundle_payload)
    return status

def cmd_oracle_annual_lane_append(ns: argparse.Namespace) -> int:
    return _run_verify_and_append_manifest(
        ns,
        verify_fn=verify_annual_review_evidence_bundle_payload,
        append_fn=append_annual_review_to_lane_payload,
        default_verification_name="ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json",
        default_entry_name="ORACLE_ANNUAL_LANE_ENTRY.json",
    )

def cmd_oracle_constitutional_digest(ns: argparse.Namespace) -> int:
    return _run_legacy_horizon_report(
        ns,
        horizon="constitutional",
        legacy_surface="oracle-constitutional-digest",
        generate_fn=build_constitutional_digest_payload,
        render_markdown_fn=render_constitutional_digest_markdown_payload,
    )

def cmd_oracle_constitutional_digest_evidence(ns: argparse.Namespace) -> int:
    lane_guard = _require_legacy_lane_read_opt_in(ns, legacy_surface="oracle-constitutional-digest-evidence")
    if lane_guard is not None:
        return lane_guard
    report_output = Path(ns.report_output) if ns.report_output else Path(ns.lane_path).with_name("ORACLE_CONSTITUTIONAL_DIGEST.json")
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_name("ORACLE_CONSTITUTIONAL_DIGEST.md")
    report = build_constitutional_digest_payload(
        lane_path=Path(ns.lane_path),
        window_size=ns.window_size,
    )
    write_json(report_output, report.model_dump(mode="json"))
    markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(markdown_output, render_constitutional_digest_markdown_payload(report), banner=_legacy_banner_with_trust(legacy_surface="oracle-constitutional-digest", report=report, lane_path=Path(ns.lane_path), repo_root=Path(ns.repo_root) if ns.repo_root else None))
    manifest, envelope = build_constitutional_digest_evidence_bundle_payload(
        source_annual_lane_path=Path(ns.lane_path),
        report_path=report_output,
        markdown_path=markdown_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_name("ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.dsse.json")
    if envelope is not None:
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification = verify_constitutional_digest_evidence_bundle_payload(
        manifest_path=manifest_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        dsse_path=dsse_output if dsse_output.exists() else None,
        public_key_path=Path(ns.public_key) if ns.public_key else None,
    )
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name("ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.verification.json")
    write_json(verification_output, verification.model_dump(mode="json"))
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0

def cmd_verify_oracle_constitutional_digest_evidence(ns: argparse.Namespace) -> int:
    status, _ = _run_verify_manifest(ns, verify_fn=verify_constitutional_digest_evidence_bundle_payload)
    return status

def cmd_oracle_constitutional_lane_append(ns: argparse.Namespace) -> int:
    return _run_verify_and_append_manifest(
        ns,
        verify_fn=verify_constitutional_digest_evidence_bundle_payload,
        append_fn=append_constitutional_digest_to_lane_payload,
        default_verification_name="ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.verification.json",
        default_entry_name="ORACLE_CONSTITUTIONAL_LANE_ENTRY.json",
    )

def cmd_oracle_doctrine_lineage_index(ns: argparse.Namespace) -> int:
    index = build_doctrine_lineage_index_payload(
        repo_root=Path(ns.repo_root),
        search_root=Path(ns.search_root) if ns.search_root else None,
    )
    payload = index.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        lineage = verify_doctrine_lineage_payload(repo_root=Path(ns.repo_root), search_root=Path(ns.search_root) if ns.search_root else None)
        write_markdown(Path(ns.markdown_output), render_doctrine_lineage_index_markdown_payload(index), banner=_lineage_banner(lineage))
    return 0

def cmd_oracle_doctrine_lineage_verify(ns: argparse.Namespace) -> int:
    verification = verify_doctrine_lineage_payload(
        repo_root=Path(ns.repo_root),
        search_root=Path(ns.search_root) if ns.search_root else None,
    )
    payload = verification.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(
            Path(ns.markdown_output),
            _append_explanation_markdown(
                render_doctrine_lineage_verification_markdown_payload(verification),
                explain_lineage_verification_payload(verification, subject_path=str(Path(ns.output)) if ns.output else None),
            ),
            banner=_lineage_banner(verification),
        )
    return 0 if verification.seal_status in {"FULLY_SEALED", "CONSTITUTIONALLY_REPLAYABLE"} else 2

def cmd_oracle_constitutional_gate(ns: argparse.Namespace) -> int:
    try:
        report = build_constitutional_gate_payload(
            repo_root=Path(ns.repo_root),
            manifest_path=Path(ns.manifest),
            search_root=Path(ns.search_root) if ns.search_root else None,
            dsse_path=Path(ns.dsse) if ns.dsse else None,
            public_key_path=Path(ns.public_key) if ns.public_key else None,
            minimum_required_seal_status=ns.minimum_required_seal_status,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = report.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(
            Path(ns.markdown_output),
            _append_explanation_markdown(
                render_constitutional_gate_markdown_payload(report),
                explain_constitutional_gate_payload(report, subject_path=str(Path(ns.output)) if ns.output else None),
            ),
            banner=_constitutional_gate_banner(report),
        )
    return 0 if report.trusted_for_constitutional_use else 2

def cmd_oracle_explain(ns: argparse.Namespace) -> int:
    repo_root = Path(ns.repo_root) if ns.repo_root else None
    try:
        if ns.manifest and ns.verification:
            explanation = explain_checkpoint_from_paths_payload(
                Path(ns.manifest),
                Path(ns.verification),
                repo_root=repo_root,
            )
        elif ns.report:
            explanation = explain_report_from_path_payload(Path(ns.report), repo_root=repo_root)
        else:
            sys.stderr.write("oracle-explain requires either --report or both --manifest and --verification.\n")
            return 2
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = explanation.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        Path(ns.markdown_output).parent.mkdir(parents=True, exist_ok=True)
        write_markdown(Path(ns.markdown_output), render_oracle_explanation_markdown_payload(explanation))
    return 0

