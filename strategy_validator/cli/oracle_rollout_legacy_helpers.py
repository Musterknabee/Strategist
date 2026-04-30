"""Shared legacy/trust helper utilities for rollout-era oracle CLI runners."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.cli.oracle_cli_common import emit_report, print_or_write_payload, write_markdown
from strategy_validator.cli.application_event_surfaces import (
    append_event_log_entry_payload,
    append_state_transition_to_lane_payload,
    append_memory_review_to_lane_payload,
    append_doctrine_drift_to_lane_payload,
    append_monthly_digest_to_lane_payload,
    append_quarterly_review_to_lane_payload,
    append_semiannual_audit_to_lane_payload,
    append_annual_review_to_lane_payload,
    append_constitutional_digest_to_lane_payload,
    build_rolling_review_payload,
    explain_derived_view_trust_payload,
    explain_event_checkpoint_trust_payload,
    legacy_compatibility_banner_payload,
    render_oracle_explanation_markdown_payload,
    render_rolling_review_markdown_payload,
    render_oracle_trust_banner_payload,
    trust_banner_for_constitutional_gate_payload,
    trust_banner_for_derived_view_payload,
    trust_banner_for_event_checkpoint_payload,
    trust_banner_for_legacy_surface_payload,
    trust_banner_for_lineage_verification_payload,
    trust_infer_repo_root_from_artifact_path_payload,
    trust_maybe_verify_oracle_lineage_payload,
)


def _write_text_output(path_value: str, content: str) -> None:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def legacy_banner(surface: str) -> str:
    return legacy_compatibility_banner_payload(legacy_surface=surface)


def compose_banner(*parts: str) -> str:
    return "".join(part for part in parts if part)


def infer_repo_root_from_artifact_path(path: Path | None) -> Path | None:
    return trust_infer_repo_root_from_artifact_path_payload(path)


def maybe_lineage_verification(*, repo_root: Path | None) -> object | None:
    return trust_maybe_verify_oracle_lineage_payload(repo_root=repo_root)


def warn_legacy_lane_read(*, legacy_surface: str, lane_path: Path) -> None:
    sys.stderr.write(
        f"[deprecated] {legacy_surface} is reading the legacy lane directly from `{lane_path}`. "
        "Prefer the canonical Oracle Event Log surfaces (`oracle-horizon-view`, `oracle-rolling-review`, checkpoints, and evidence packs) whenever available.\n"
    )


def require_legacy_lane_read_opt_in(ns: argparse.Namespace, *, legacy_surface: str) -> int | None:
    lane_path_raw = getattr(ns, "lane_path", "")
    if not lane_path_raw:
        sys.stderr.write(
            f"{legacy_surface} could not resolve the canonical Oracle Event Log automatically. "
            "Provide `--log-path` / the standard docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl layout, "
            "or explicitly fall back with `--lane-path` plus `--allow-legacy-lane-read`.\n"
        )
        return 2
    lane_path = Path(lane_path_raw)
    if not getattr(ns, "allow_legacy_lane_read", False):
        sys.stderr.write(
            f"{legacy_surface} direct legacy lane reads now require `--allow-legacy-lane-read`. "
            "The canonical Oracle Event Log remains the primary operator read model.\n"
        )
        return 2
    warn_legacy_lane_read(legacy_surface=legacy_surface, lane_path=lane_path)
    return None


def default_checkpoint_metadata_output(*, lane_path: Path, report_output: Path | None = None, explicit_path: str = "") -> Path:
    if explicit_path:
        return Path(explicit_path)
    base_dir = report_output.parent if report_output is not None else lane_path.parent
    stem = report_output.stem if report_output is not None else f"ORACLE_DERIVED_VIEW_{lane_path.stem}"
    return base_dir / f"{stem}.checkpoint.metadata.json"


def resolve_primary_event_log_path(*, log_path: str = "", lane_path: Path | None = None, repo_root: Path | None = None) -> Path | None:
    if log_path:
        return Path(log_path)
    inferred_repo_root = repo_root or infer_repo_root_from_artifact_path(lane_path)
    candidates: list[Path] = []
    if inferred_repo_root is not None:
        candidates.append((inferred_repo_root / "docs" / "artifacts" / "oracle" / "ORACLE_EVENT_LOG.jsonl").resolve())
    candidates.append(Path("docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl").resolve())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def legacy_banner_with_trust(*, legacy_surface: str, report: object, lane_path: Path | None = None, repo_root: Path | None = None) -> str:
    inferred_repo_root = repo_root or (infer_repo_root_from_artifact_path(lane_path) if lane_path is not None else None)
    lineage = maybe_lineage_verification(repo_root=inferred_repo_root)
    trust_banner = render_oracle_trust_banner_payload(
        trust_banner_for_legacy_surface_payload(legacy_surface=legacy_surface, report=report, lineage_verification=lineage)
    )
    return compose_banner(trust_banner, legacy_banner(legacy_surface))


def derived_view_banner(report: object, *, lane_path: Path | None = None, repo_root: Path | None = None) -> str:
    inferred_repo_root = repo_root or infer_repo_root_from_artifact_path(lane_path)
    lineage = maybe_lineage_verification(repo_root=inferred_repo_root)
    return render_oracle_trust_banner_payload(trust_banner_for_derived_view_payload(report, lineage_verification=lineage))


def event_checkpoint_banner(manifest: object, verification: object, *, artifact_path: Path | None = None, repo_root: Path | None = None) -> str:
    inferred_repo_root = repo_root or infer_repo_root_from_artifact_path(artifact_path)
    lineage = maybe_lineage_verification(repo_root=inferred_repo_root)
    return render_oracle_trust_banner_payload(
        trust_banner_for_event_checkpoint_payload(manifest, verification, lineage_verification=lineage)
    )


def lineage_banner(report: object) -> str:
    return render_oracle_trust_banner_payload(trust_banner_for_lineage_verification_payload(report))


def constitutional_gate_banner(report: object) -> str:
    return render_oracle_trust_banner_payload(trust_banner_for_constitutional_gate_payload(report))


def append_explanation_markdown(body: str, explanation: object) -> str:
    return body + "\n\n" + render_oracle_explanation_markdown_payload(explanation)


def explain_derived_report(report: object, *, lane_path: Path | None = None, repo_root: Path | None = None, subject_path: str | None = None) -> object:
    inferred_repo_root = repo_root or infer_repo_root_from_artifact_path(lane_path)
    lineage = maybe_lineage_verification(repo_root=inferred_repo_root)
    return explain_derived_view_trust_payload(report, lineage_verification=lineage, subject_path=subject_path)


def explain_checkpoint(manifest: object, verification: object, *, artifact_path: Path | None = None, repo_root: Path | None = None, subject_path: str | None = None) -> object:
    inferred_repo_root = repo_root or infer_repo_root_from_artifact_path(artifact_path)
    lineage = maybe_lineage_verification(repo_root=inferred_repo_root)
    return explain_event_checkpoint_trust_payload(manifest, verification, lineage_verification=lineage, subject_path=subject_path)


def legacy_horizon_proxy(ns: argparse.Namespace, *, horizon: str, legacy_surface: str) -> int | None:
    lane_path = Path(ns.lane_path) if getattr(ns, "lane_path", "") else None
    resolved_log_path = resolve_primary_event_log_path(log_path=getattr(ns, "log_path", ""), lane_path=lane_path)
    if resolved_log_path is None:
        return None
    checkpoint_metadata_output = default_checkpoint_metadata_output(
        lane_path=resolved_log_path,
        report_output=Path(ns.output) if getattr(ns, "output", "") else None,
        explicit_path=getattr(ns, "checkpoint_metadata_output", ""),
    )
    report = build_rolling_review_payload(
        lane_path=resolved_log_path,
        horizon=horizon,
        window_size=getattr(ns, "window_size", None),
        checkpoint_metadata_path=checkpoint_metadata_output,
    )
    payload = report.model_dump(mode="json")
    if ns.output:
        Path(ns.output).parent.mkdir(parents=True, exist_ok=True)
        Path(ns.output).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if getattr(ns, "markdown_output", ""):
        write_markdown(
            Path(ns.markdown_output),
            render_rolling_review_markdown_payload(report),
            banner=legacy_banner_with_trust(legacy_surface=legacy_surface, report=report, lane_path=resolved_log_path),
        )
    return 0


def run_legacy_horizon_report(ns: argparse.Namespace, *, horizon: str, legacy_surface: str, generate_fn, render_markdown_fn) -> int:
    proxied = legacy_horizon_proxy(ns, horizon=horizon, legacy_surface=legacy_surface)
    if proxied is not None:
        return proxied
    lane_guard = require_legacy_lane_read_opt_in(ns, legacy_surface=legacy_surface)
    if lane_guard is not None:
        return lane_guard
    report = generate_fn(
        lane_path=Path(ns.lane_path),
        window_size=ns.window_size,
        repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
        search_root=Path(ns.search_root) if getattr(ns, "search_root", "") else None,
    )
    emit_report(
        report,
        output=ns.output,
        markdown_output=getattr(ns, "markdown_output", ""),
        render_markdown=render_markdown_fn,
        banner=legacy_banner_with_trust(legacy_surface=legacy_surface, report=report, lane_path=Path(ns.lane_path)),
    )
    return 0


def run_verify_manifest(ns: argparse.Namespace, *, verify_fn) -> tuple[int, object | None]:
    try:
        verification = verify_fn(
            manifest_path=Path(ns.manifest),
            repo_root=Path(ns.repo_root) if getattr(ns, "repo_root", "") else None,
            dsse_path=Path(ns.dsse) if getattr(ns, "dsse", "") else None,
            public_key_path=Path(ns.public_key) if getattr(ns, "public_key", "") else None,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2, None
    print_or_write_payload(verification.model_dump(mode="json"), getattr(ns, "output", ""))
    return (0 if getattr(verification, "status", None) == "VERIFIED" else 2), verification


def _append_entry(append_fn, *, verification_path: Path, verification: object, entry_path: Path, ns: argparse.Namespace) -> object:
    del verification_path, entry_path
    kwargs = {
        "manifest_path": Path(ns.manifest),
        "verification": verification,
        "lane_path": Path(ns.lane_path),
    }
    if getattr(ns, "repo_root", ""):
        kwargs["repo_root"] = Path(ns.repo_root)
    return append_fn(**kwargs)


def run_verify_and_append_manifest(ns: argparse.Namespace, *, verify_fn, append_fn, default_verification_name: str, default_entry_name: str) -> int:
    status, verification = run_verify_manifest(ns, verify_fn=verify_fn)
    if verification is None:
        return status

    verification_output = Path(getattr(ns, "verification_output", "") or default_verification_name)
    verification_output.parent.mkdir(parents=True, exist_ok=True)
    verification_output.write_text(json.dumps(verification.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")

    entry_output = Path(getattr(ns, "entry_output", "") or default_entry_name)
    try:
        entry = _append_entry(append_fn, verification_path=verification_output, verification=verification, entry_path=entry_output, ns=ns)
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    if entry_output:
        entry_output.parent.mkdir(parents=True, exist_ok=True)
        entry_output.write_text(json.dumps(entry.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    return status


__all__ = [
    "append_explanation_markdown",
    "constitutional_gate_banner",
    "default_checkpoint_metadata_output",
    "derived_view_banner",
    "event_checkpoint_banner",
    "explain_checkpoint",
    "explain_derived_report",
    "infer_repo_root_from_artifact_path",
    "legacy_banner",
    "legacy_banner_with_trust",
    "legacy_horizon_proxy",
    "lineage_banner",
    "maybe_lineage_verification",
    "require_legacy_lane_read_opt_in",
    "resolve_primary_event_log_path",
    "run_legacy_horizon_report",
    "run_verify_and_append_manifest",
    "run_verify_manifest",
    "warn_legacy_lane_read",
    "_write_text_output",
]
