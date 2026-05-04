"""Oracle event/projection runner helpers extracted from rollout_ops."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.cli.application_event_surfaces import (
    append_event_log_entry_payload,
    build_derived_view_payload,
    build_event_checkpoint_payload,
    build_horizon_view_payload,
    build_rolling_review_payload,
    emit_event_checkpoint_projection_registry_payload,
    emit_event_view_projection_registry_payload,
    explain_derived_view_trust_payload,
    explain_event_checkpoint_trust_payload,
    render_derived_view_markdown_payload,
    render_event_checkpoint_markdown_payload,
    render_oracle_explanation_markdown_payload,
    render_oracle_trust_banner_payload,
    render_rolling_review_markdown_payload,
    resolve_horizon_window_payload,
    trust_banner_for_derived_view_payload,
    trust_banner_for_event_checkpoint_payload,
    trust_infer_repo_root_from_artifact_path_payload,
    trust_maybe_verify_oracle_lineage_payload,
    verify_event_checkpoint_payload,
    verify_oracle_evidence_bundle_payload,
)
from strategy_validator.cli.oracle_cli_common import write_json, write_markdown


def _infer_repo_root_from_artifact_path(path: Path | None) -> Path | None:
    return trust_infer_repo_root_from_artifact_path_payload(path)


def _maybe_lineage_verification(*, repo_root: Path | None) -> object | None:
    return trust_maybe_verify_oracle_lineage_payload(repo_root=repo_root)


def _default_checkpoint_metadata_output(*, lane_path: Path, report_output: Path | None = None, explicit_path: str = "") -> Path:
    if explicit_path:
        return Path(explicit_path)
    base_dir = report_output.parent if report_output is not None else lane_path.parent
    stem = report_output.stem if report_output is not None else f"ORACLE_DERIVED_VIEW_{lane_path.stem}"
    return base_dir / f"{stem}.checkpoint.metadata.json"


def _derived_view_banner(report: object, *, lane_path: Path | None = None, repo_root: Path | None = None) -> str:
    inferred_repo_root = repo_root or _infer_repo_root_from_artifact_path(lane_path)
    lineage = _maybe_lineage_verification(repo_root=inferred_repo_root)
    return render_oracle_trust_banner_payload(trust_banner_for_derived_view_payload(report, lineage_verification=lineage))


def _event_checkpoint_banner(manifest: object, verification: object, *, artifact_path: Path | None = None, repo_root: Path | None = None) -> str:
    inferred_repo_root = repo_root or _infer_repo_root_from_artifact_path(artifact_path)
    lineage = _maybe_lineage_verification(repo_root=inferred_repo_root)
    return render_oracle_trust_banner_payload(
        trust_banner_for_event_checkpoint_payload(manifest, verification, lineage_verification=lineage)
    )


def _append_explanation_markdown(body: str, explanation: object) -> str:
    return body + "\n\n" + render_oracle_explanation_markdown_payload(explanation)


def _explain_derived_report(report: object, *, lane_path: Path | None = None, repo_root: Path | None = None, subject_path: str | None = None) -> object:
    inferred_repo_root = repo_root or _infer_repo_root_from_artifact_path(lane_path)
    lineage = _maybe_lineage_verification(repo_root=inferred_repo_root)
    return explain_derived_view_trust_payload(report, lineage_verification=lineage, subject_path=subject_path)


def _explain_checkpoint(manifest: object, verification: object, *, artifact_path: Path | None = None, repo_root: Path | None = None, subject_path: str | None = None) -> object:
    inferred_repo_root = repo_root or _infer_repo_root_from_artifact_path(artifact_path)
    lineage = _maybe_lineage_verification(repo_root=inferred_repo_root)
    return explain_event_checkpoint_trust_payload(manifest, verification, lineage_verification=lineage, subject_path=subject_path)


def cmd_oracle_event_log_append(ns: argparse.Namespace) -> int:
    try:
        verification = verify_oracle_evidence_bundle_payload(
            manifest_path=Path(ns.manifest),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            dsse_path=Path(ns.dsse) if ns.dsse else None,
            public_key_path=Path(ns.public_key) if ns.public_key else None,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    verification_output = Path(ns.verification_output) if ns.verification_output else Path(ns.manifest).with_name(
        "ORACLE_EVENT_LOG_EVIDENCE.verification.json"
    )
    write_json(verification_output, verification.model_dump(mode="json"))
    try:
        entry = append_event_log_entry_payload(
            manifest_path=Path(ns.manifest),
            verification=verification,
            lane_path=Path(ns.log_path),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
        )
    except (FileNotFoundError, ValueError) as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    output = Path(ns.output) if ns.output else Path(ns.manifest).with_name("ORACLE_EVENT_LOG_ENTRY.json")
    write_json(output, entry.model_dump(mode="json"))
    sys.stdout.write(json.dumps(entry.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0


def cmd_oracle_rolling_review(ns: argparse.Namespace) -> int:
    log_path = Path(ns.log_path)
    repo_root = Path(ns.repo_root) if getattr(ns, "repo_root", "") else Path.cwd()
    checkpoint_metadata_output = _default_checkpoint_metadata_output(
        lane_path=log_path,
        report_output=Path(ns.output) if ns.output else None,
        explicit_path=getattr(ns, "checkpoint_metadata_output", ""),
    )
    try:
        report = build_rolling_review_payload(
            lane_path=log_path,
            horizon=ns.horizon,
            window_size=ns.window_size if ns.window_size > 0 else None,
            checkpoint_metadata_path=checkpoint_metadata_output,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = report.model_dump(mode="json")
    output_paths: list[Path] = []
    if ns.output:
        output_path = Path(ns.output)
        write_json(output_path, payload)
        output_paths.append(output_path)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        markdown_path = Path(ns.markdown_output)
        write_markdown(
            markdown_path,
            _append_explanation_markdown(
                render_rolling_review_markdown_payload(report),
                _explain_derived_report(report, lane_path=log_path, subject_path=str(Path(ns.output)) if ns.output else None),
            ),
            banner=_derived_view_banner(report, lane_path=log_path),
        )
        output_paths.append(markdown_path)
    if output_paths:
        emit_event_view_projection_registry_payload(
            registry_output_path=output_paths[0].with_suffix('.projection.registry.json'),
            projection_label='oracle_rolling_review',
            projection_version='oracle_derived_view_report/v1',
            lane_path=log_path,
            report_payload=payload,
            output_paths=output_paths,
            repo_root=repo_root,
            generated_at_utc=report.generated_at_utc,
            index_output_path=output_paths[0].with_name('ORACLE_PROJECTION_ARTIFACT_INDEX.json'),
        )
    return 0


def cmd_oracle_rolling_review_checkpoint(ns: argparse.Namespace) -> int:
    try:
        horizon, resolved_window = resolve_horizon_window_payload(
            horizon=ns.horizon,
            window_size=ns.window_size if ns.window_size > 0 else None,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    log_path = Path(ns.log_path)
    report_output = Path(ns.report_output) if ns.report_output else log_path.with_name("ORACLE_DERIVED_VIEW.json")
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_suffix(".md")
    checkpoint_markdown_output = Path(ns.checkpoint_markdown_output) if ns.checkpoint_markdown_output else report_output.with_name("ORACLE_EVENT_CHECKPOINT.md")
    checkpoint_metadata_output = _default_checkpoint_metadata_output(
        lane_path=log_path,
        report_output=report_output,
        explicit_path=getattr(ns, "checkpoint_metadata_output", ""),
    )
    report = build_rolling_review_payload(
        lane_path=log_path,
        horizon=horizon,
        window_size=resolved_window,
        checkpoint_metadata_path=checkpoint_metadata_output,
    )
    write_json(report_output, report.model_dump(mode="json"))
    write_markdown(
        markdown_output,
        _append_explanation_markdown(
            render_rolling_review_markdown_payload(report),
            _explain_derived_report(
                report,
                lane_path=log_path,
                repo_root=Path(ns.repo_root) if ns.repo_root else None,
                subject_path=str(report_output),
            ),
        ),
        banner=_derived_view_banner(report, lane_path=log_path, repo_root=Path(ns.repo_root) if ns.repo_root else None),
    )
    manifest, envelope, verification, _ = build_event_checkpoint_payload(
        lane_path=log_path,
        report_path=report_output,
        repo_root=Path(ns.repo_root) if ns.repo_root else Path.cwd(),
        view_label=horizon,
        window_size=resolved_window,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
        checkpoint_metadata_path=checkpoint_metadata_output,
    )
    manifest_output = Path(ns.output) if ns.output else report_output.with_name("ORACLE_EVENT_CHECKPOINT.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix(".dsse.json")
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name(
        "ORACLE_EVENT_CHECKPOINT.verification.json"
    )
    write_json(verification_output, verification.model_dump(mode="json"))
    write_markdown(
        checkpoint_markdown_output,
        _append_explanation_markdown(
            render_event_checkpoint_markdown_payload(manifest),
            _explain_checkpoint(
                manifest,
                verification,
                artifact_path=log_path,
                repo_root=Path(ns.repo_root) if ns.repo_root else None,
                subject_path=str(manifest_output),
            ),
        ),
        banner=_event_checkpoint_banner(
            manifest,
            verification,
            artifact_path=log_path,
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
        ),
    )
    emit_event_checkpoint_projection_registry_payload(
        registry_output_path=manifest_output.with_suffix('.projection.registry.json'),
        projection_label='oracle_rolling_review_checkpoint',
        projection_version='oracle_event_checkpoint_manifest/v1',
        lane_path=log_path,
        output_paths=[report_output, markdown_output, checkpoint_metadata_output, manifest_output, verification_output, checkpoint_markdown_output] + ([dsse_output] if dsse_output is not None else []),
        repo_root=Path(ns.repo_root) if ns.repo_root else Path.cwd(),
        generated_at_utc=manifest.generated_at_utc,
        index_output_path=manifest_output.with_name('ORACLE_PROJECTION_ARTIFACT_INDEX.json'),
    )
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_oracle_derived_view(ns: argparse.Namespace) -> int:
    log_path = Path(ns.log_path)
    checkpoint_metadata_output = _default_checkpoint_metadata_output(
        lane_path=log_path,
        report_output=Path(ns.output) if ns.output else None,
        explicit_path=getattr(ns, "checkpoint_metadata_output", ""),
    )
    try:
        report = build_derived_view_payload(
            lane_path=log_path,
            view_label=ns.view_label,
            window_size=ns.window_size,
            checkpoint_metadata_path=checkpoint_metadata_output,
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
        write_markdown(
            Path(ns.markdown_output),
            _append_explanation_markdown(
                render_derived_view_markdown_payload(report),
                _explain_derived_report(report, lane_path=log_path, subject_path=str(Path(ns.output)) if ns.output else None),
            ),
            banner=_derived_view_banner(report, lane_path=log_path),
        )
    return 0 if report.derived_classification != "EVIDENCE_GAP" else 2


def cmd_oracle_event_checkpoint(ns: argparse.Namespace) -> int:
    repo_root = Path(ns.repo_root) if ns.repo_root else Path.cwd()
    lane_path = Path(ns.lane_path)
    report_output = Path(ns.report_output) if ns.report_output else (Path(ns.output).with_name("ORACLE_DERIVED_VIEW.json") if ns.output else lane_path.with_name("ORACLE_DERIVED_VIEW.json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_suffix('.md')
    checkpoint_metadata_output = _default_checkpoint_metadata_output(
        lane_path=lane_path,
        report_output=report_output,
        explicit_path=getattr(ns, "checkpoint_metadata_output", ""),
    )
    report = build_derived_view_payload(
        lane_path=lane_path,
        view_label=ns.view_label,
        window_size=ns.window_size,
        checkpoint_metadata_path=checkpoint_metadata_output,
    )
    write_json(report_output, report.model_dump(mode="json"))
    write_markdown(
        markdown_output,
        _append_explanation_markdown(
            render_derived_view_markdown_payload(report),
            _explain_derived_report(report, lane_path=lane_path, repo_root=repo_root, subject_path=str(report_output)),
        ),
        banner=_derived_view_banner(report, lane_path=lane_path, repo_root=repo_root),
    )
    manifest, envelope, verification, _ = build_event_checkpoint_payload(
        lane_path=lane_path,
        report_path=report_output,
        repo_root=repo_root,
        view_label=ns.view_label,
        window_size=ns.window_size,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
        checkpoint_metadata_path=checkpoint_metadata_output,
    )
    manifest_output = Path(ns.output) if ns.output else lane_path.with_name("ORACLE_EVENT_CHECKPOINT.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix('.dsse.json')
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name(
        "ORACLE_EVENT_CHECKPOINT.verification.json"
    )
    write_json(verification_output, verification.model_dump(mode="json"))
    checkpoint_md = Path(ns.checkpoint_markdown_output) if ns.checkpoint_markdown_output else manifest_output.with_suffix('.md')
    checkpoint_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(
        checkpoint_md,
        _append_explanation_markdown(
            render_event_checkpoint_markdown_payload(manifest),
            _explain_checkpoint(manifest, verification, artifact_path=lane_path, repo_root=repo_root, subject_path=str(manifest_output)),
        ),
        banner=_event_checkpoint_banner(manifest, verification, artifact_path=lane_path, repo_root=repo_root),
    )
    emit_event_checkpoint_projection_registry_payload(
        registry_output_path=manifest_output.with_suffix('.projection.registry.json'),
        projection_label='oracle_event_checkpoint',
        projection_version='oracle_event_checkpoint_manifest/v1',
        lane_path=lane_path,
        output_paths=[report_output, markdown_output, checkpoint_metadata_output, manifest_output, verification_output, checkpoint_md] + ([dsse_output] if dsse_output is not None else []),
        repo_root=repo_root,
        generated_at_utc=manifest.generated_at_utc,
        index_output_path=manifest_output.with_name('ORACLE_PROJECTION_ARTIFACT_INDEX.json'),
    )
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_oracle_horizon_view(ns: argparse.Namespace) -> int:
    log_path = Path(ns.log_path)
    repo_root = Path(ns.repo_root) if getattr(ns, "repo_root", "") else Path.cwd()
    checkpoint_metadata_output = _default_checkpoint_metadata_output(
        lane_path=log_path,
        report_output=Path(ns.output) if ns.output else None,
        explicit_path=getattr(ns, "checkpoint_metadata_output", ""),
    )
    try:
        horizon, resolved_window = resolve_horizon_window_payload(
            horizon=ns.horizon,
            window_size=ns.window_size if ns.window_size > 0 else None,
        )
        report = build_horizon_view_payload(
            lane_path=log_path,
            horizon=horizon,
            window_size=resolved_window,
            checkpoint_metadata_path=checkpoint_metadata_output,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = report.model_dump(mode="json")
    output_paths: list[Path] = []
    if ns.output:
        output_path = Path(ns.output)
        write_json(output_path, payload)
        output_paths.append(output_path)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    if ns.markdown_output:
        markdown_path = Path(ns.markdown_output)
        write_markdown(
            markdown_path,
            _append_explanation_markdown(
                render_derived_view_markdown_payload(report),
                _explain_derived_report(report, lane_path=log_path, subject_path=str(Path(ns.output)) if ns.output else None),
            ),
            banner=_derived_view_banner(report, lane_path=log_path),
        )
        output_paths.append(markdown_path)
    if output_paths:
        emit_event_view_projection_registry_payload(
            registry_output_path=output_paths[0].with_suffix('.projection.registry.json'),
            projection_label='oracle_horizon_view',
            projection_version='oracle_derived_view_report/v1',
            lane_path=log_path,
            report_payload=payload,
            output_paths=output_paths,
            repo_root=repo_root,
            generated_at_utc=report.generated_at_utc,
            index_output_path=output_paths[0].with_name('ORACLE_PROJECTION_ARTIFACT_INDEX.json'),
        )
    return 0 if report.derived_classification != "EVIDENCE_GAP" else 2


def cmd_oracle_horizon_checkpoint(ns: argparse.Namespace) -> int:
    try:
        horizon, resolved_window = resolve_horizon_window_payload(
            horizon=ns.horizon,
            window_size=ns.window_size if ns.window_size > 0 else None,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    repo_root = Path(ns.repo_root) if ns.repo_root else Path.cwd()
    log_path = Path(ns.log_path)
    report_output = Path(ns.report_output) if ns.report_output else (Path(ns.output).with_name("ORACLE_DERIVED_VIEW.json") if ns.output else log_path.with_name("ORACLE_DERIVED_VIEW.json"))
    markdown_output = Path(ns.markdown_output) if ns.markdown_output else report_output.with_suffix('.md')
    checkpoint_metadata_output = _default_checkpoint_metadata_output(
        lane_path=log_path,
        report_output=report_output,
        explicit_path=getattr(ns, "checkpoint_metadata_output", ""),
    )
    report = build_horizon_view_payload(
        lane_path=log_path,
        horizon=horizon,
        window_size=resolved_window,
        checkpoint_metadata_path=checkpoint_metadata_output,
    )
    write_json(report_output, report.model_dump(mode="json"))
    write_markdown(
        markdown_output,
        _append_explanation_markdown(
            render_derived_view_markdown_payload(report),
            _explain_derived_report(report, lane_path=log_path, repo_root=repo_root, subject_path=str(report_output)),
        ),
        banner=_derived_view_banner(report, lane_path=log_path, repo_root=repo_root),
    )
    manifest, envelope, verification, _ = build_event_checkpoint_payload(
        lane_path=log_path,
        report_path=report_output,
        repo_root=repo_root,
        view_label=horizon,
        window_size=resolved_window,
        signing_private_key_path=Path(ns.signing_private_key) if ns.signing_private_key else None,
        checkpoint_metadata_path=checkpoint_metadata_output,
    )
    manifest_output = Path(ns.output) if ns.output else log_path.with_name("ORACLE_EVENT_CHECKPOINT.json")
    write_json(manifest_output, manifest.model_dump(mode="json"))
    dsse_output = None
    if envelope is not None:
        dsse_output = Path(ns.dsse_output) if ns.dsse_output else manifest_output.with_suffix('.dsse.json')
        write_json(dsse_output, envelope.model_dump(mode="json"))
    verification_output = Path(ns.verification_output) if ns.verification_output else manifest_output.with_name(
        "ORACLE_EVENT_CHECKPOINT.verification.json"
    )
    write_json(verification_output, verification.model_dump(mode="json"))
    checkpoint_md = Path(ns.checkpoint_markdown_output) if ns.checkpoint_markdown_output else manifest_output.with_suffix('.md')
    checkpoint_md.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(
        checkpoint_md,
        _append_explanation_markdown(
            render_event_checkpoint_markdown_payload(manifest),
            _explain_checkpoint(manifest, verification, artifact_path=log_path, repo_root=repo_root, subject_path=str(manifest_output)),
        ),
        banner=_event_checkpoint_banner(manifest, verification, artifact_path=log_path, repo_root=repo_root),
    )
    emit_event_checkpoint_projection_registry_payload(
        registry_output_path=manifest_output.with_suffix('.projection.registry.json'),
        projection_label='oracle_horizon_checkpoint',
        projection_version='oracle_event_checkpoint_manifest/v1',
        lane_path=log_path,
        output_paths=[report_output, markdown_output, checkpoint_metadata_output, manifest_output, verification_output, checkpoint_md] + ([dsse_output] if dsse_output is not None else []),
        repo_root=repo_root,
        generated_at_utc=manifest.generated_at_utc,
        index_output_path=manifest_output.with_name('ORACLE_PROJECTION_ARTIFACT_INDEX.json'),
    )
    sys.stdout.write(json.dumps(manifest.model_dump(mode="json"), indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2


def cmd_verify_oracle_event_checkpoint(ns: argparse.Namespace) -> int:
    try:
        verification = verify_event_checkpoint_payload(
            manifest_path=Path(ns.manifest),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            dsse_path=Path(ns.dsse) if ns.dsse else None,
            public_key_path=Path(ns.public_key) if ns.public_key else None,
        )
    except ValueError as exc:
        sys.stderr.write(str(exc) + "\n")
        return 2
    payload = verification.model_dump(mode="json")
    if ns.output:
        write_json(Path(ns.output), payload)
    else:
        sys.stdout.write(json.dumps(payload, indent=2, default=str) + "\n")
    return 0 if verification.status == "VERIFIED" else 2
