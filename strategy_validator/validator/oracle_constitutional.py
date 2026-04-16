from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from strategy_validator.contracts.operational import DsseEnvelope
from strategy_validator.contracts.oracle import (
    OracleConstitutionalDigestEvidenceManifest,
    OracleConstitutionalDigestEvidenceVerification,
    OracleConstitutionalDigestReport,
    OracleConstitutionalGateReport,
    OracleConstitutionalLaneEntry,
    OracleDoctrineLineageIndex,
    OracleDoctrineLineageVerification,
)
from strategy_validator.validator.oracle_advisory import (
    _artifact_descriptor,
    _json_canonical_bytes,
    _resolve_existing_path as advisory_resolve_existing_path,
    _sha256_bytes,
    _sha256_file,
    _sign_dsse_payload,
    _utc_now as advisory_utc_now,
    _verify_dsse_envelope,
)
from strategy_validator.validator.oracle_evidence_common import (
    collect_evidence_subjects,
    sign_manifest_envelope,
    verify_evidence_bundle,
)


def _normalize_path(path: Path | str) -> str:
    raw = str(path)
    return raw.replace('\\', '/')


def _lineage_seal_rank(status: str) -> int:
    return {
        "ADVISORY_ONLY_INCOMPLETE": 0,
        "PARTIALLY_SEALED": 1,
        "CONSTITUTIONALLY_REPLAYABLE": 2,
        "FULLY_SEALED": 3,
    }[status]


_ORACLE_CONSTITUTIONAL_DIGEST_PAYLOAD_TYPE = "application/vnd.strategy-validator.oracle-constitutional-digest.v1+json"


def _find_constitutional_digest_report_path(*, manifest: OracleConstitutionalDigestEvidenceManifest, manifest_path: Path, repo_root: Path) -> Path:
    for subject in manifest.subjects:
        if subject.path.endswith("ORACLE_CONSTITUTIONAL_DIGEST.json"):
            resolved = advisory_resolve_existing_path(subject.path, repo_root=repo_root, preferred_parent=manifest_path.parent)
            if resolved is None:
                raise FileNotFoundError(f"oracle constitutional digest report subject missing from evidence chain: {subject.path}")
            return resolved
    raise FileNotFoundError("oracle constitutional digest evidence manifest does not include ORACLE_CONSTITUTIONAL_DIGEST.json")


def build_oracle_constitutional_digest_evidence_bundle(*, source_annual_lane_path: Path, report_path: Path, markdown_path: Path, repo_root: Optional[Path] = None, signing_private_key_path: Optional[Path] = None, now_utc: Optional[datetime] = None) -> tuple[OracleConstitutionalDigestEvidenceManifest, DsseEnvelope | None]:
    repo_root = (repo_root or Path.cwd()).resolve()
    source_annual_lane_path = source_annual_lane_path.resolve()
    report_path = report_path.resolve()
    markdown_path = markdown_path.resolve()
    report = OracleConstitutionalDigestReport.model_validate(json.loads(report_path.read_text(encoding="utf-8")))
    subjects, missing_artifact_paths, integrity_status = collect_evidence_subjects(
        artifact_paths=(source_annual_lane_path, report_path, markdown_path),
        repo_root=repo_root,
        artifact_descriptor=_artifact_descriptor,
        normalize_path=_normalize_path,
    )
    constitutional_digest_id = _sha256_bytes(_json_canonical_bytes({"lane_id": report.lane_id, "constitutional_digest_classification": report.constitutional_digest_classification, "window_end_sequence_number": report.window_end_sequence_number, "observed_annual_review_ids": report.observed_annual_review_ids, "summary_line": report.summary_line}))
    manifest = OracleConstitutionalDigestEvidenceManifest(generated_at_utc=now_utc or advisory_utc_now(), constitutional_digest_id=constitutional_digest_id, lane_id=report.lane_id, exact_evidence_support_score=report.exact_evidence_support_score, exact_feedback_confirmation_count=report.exact_feedback_confirmation_count, exact_feedback_relief_count=report.exact_feedback_relief_count, execution_authority="ADVISORY_ONLY", source_annual_lane_path=_normalize_path(source_annual_lane_path), constitutional_digest_classification=report.constitutional_digest_classification, strategic_backing_classification=report.strategic_backing_classification, strategic_stack_evidence_count=report.strategic_stack_evidence_count, strategic_stack_requirement_met=report.strategic_stack_requirement_met, window_entry_count=report.window_entry_count, window_end_sequence_number=report.window_end_sequence_number, latest_annual_review_id=report.latest_annual_review_id, latest_annual_review_classification=report.latest_annual_review_classification, integrity_status=integrity_status, subjects=subjects, missing_artifact_paths=missing_artifact_paths, summary_line=report.summary_line)
    envelope = sign_manifest_envelope(
        manifest=manifest,
        payload_type=_ORACLE_CONSTITUTIONAL_DIGEST_PAYLOAD_TYPE,
        signing_private_key_path=signing_private_key_path,
        json_canonical_bytes=_json_canonical_bytes,
        sign_dsse_payload=_sign_dsse_payload,
    )
    return manifest, envelope


def verify_oracle_constitutional_digest_evidence_bundle(*, manifest_path: Path, repo_root: Optional[Path] = None, dsse_path: Optional[Path] = None, public_key_path: Optional[Path] = None) -> OracleConstitutionalDigestEvidenceVerification:
    repo_root = (repo_root or Path.cwd()).resolve()
    manifest_path = manifest_path.resolve()
    manifest = OracleConstitutionalDigestEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    summary = verify_evidence_bundle(
        manifest_path=manifest_path,
        repo_root=repo_root,
        subjects=manifest.subjects,
        manifest_missing_artifact_paths=manifest.missing_artifact_paths,
        resolver=advisory_resolve_existing_path,
        sha256_file=_sha256_file,
        dsse_path=dsse_path,
        public_key_path=public_key_path,
        payload_type=_ORACLE_CONSTITUTIONAL_DIGEST_PAYLOAD_TYPE,
        expected_payload=_json_canonical_bytes(manifest.model_dump(mode="json")),
        dsse_model=DsseEnvelope,
        verify_dsse_envelope=_verify_dsse_envelope,
    )
    return OracleConstitutionalDigestEvidenceVerification(verified_at_utc=advisory_utc_now(), manifest_path=_normalize_path(manifest_path), status=summary.status, artifact_digests_verified=summary.artifact_digests_verified, signature_verified=summary.signature_verified, verified_subject_count=summary.verified_subject_count, digest_mismatches=summary.digest_mismatches, missing_artifact_paths=summary.missing_artifact_paths, notes=summary.notes)


def append_oracle_constitutional_digest_to_lane(*, manifest_path: Path, verification: OracleConstitutionalDigestEvidenceVerification, lane_path: Path, repo_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleConstitutionalLaneEntry:
    if verification.status != "VERIFIED": raise ValueError("oracle constitutional digest evidence must verify before it can be appended to the constitutional lane")
    repo_root = (repo_root or Path.cwd()).resolve(); manifest_path = manifest_path.resolve(); lane_path = lane_path.resolve(); manifest = OracleConstitutionalDigestEvidenceManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    entries=[]
    if lane_path.exists():
        for raw in lane_path.read_text(encoding="utf-8").splitlines():
            raw=raw.strip();
            if raw: entries.append(OracleConstitutionalLaneEntry.model_validate(json.loads(raw)))
    sequence_number=len(entries); previous_entry_hash = entries[-1].entry_hash if entries else None; lane_id=lane_path.stem
    entry_payload = {"lane_id": lane_id, "sequence_number": sequence_number, "constitutional_digest_id": manifest.constitutional_digest_id, "previous_entry_hash": previous_entry_hash, "manifest_sha256": _sha256_file(manifest_path), "constitutional_digest_classification": manifest.constitutional_digest_classification, "exact_evidence_support_score": manifest.exact_evidence_support_score, "exact_feedback_confirmation_count": manifest.exact_feedback_confirmation_count, "exact_feedback_relief_count": manifest.exact_feedback_relief_count, "latest_annual_review_id": manifest.latest_annual_review_id, "evidence_status": verification.status, "summary_line": manifest.summary_line}
    entry_hash = _sha256_bytes(_json_canonical_bytes(entry_payload)); entry_id = _sha256_bytes(_json_canonical_bytes({"lane_id": lane_id, "sequence_number": sequence_number, "entry_hash": entry_hash}))
    try: manifest_ref = manifest_path.relative_to(repo_root)
    except ValueError: manifest_ref = manifest_path
    entry = OracleConstitutionalLaneEntry(appended_at_utc=now_utc or advisory_utc_now(), lane_id=lane_id, exact_evidence_support_score=manifest.exact_evidence_support_score, exact_feedback_confirmation_count=manifest.exact_feedback_confirmation_count, exact_feedback_relief_count=manifest.exact_feedback_relief_count, sequence_number=sequence_number, entry_id=entry_id, constitutional_digest_id=manifest.constitutional_digest_id, previous_entry_hash=previous_entry_hash, entry_hash=entry_hash, manifest_path=_normalize_path(manifest_ref), manifest_sha256=_sha256_file(manifest_path), constitutional_digest_classification=manifest.constitutional_digest_classification, strategic_backing_classification=manifest.strategic_backing_classification, strategic_stack_evidence_count=manifest.strategic_stack_evidence_count, strategic_stack_requirement_met=manifest.strategic_stack_requirement_met, latest_annual_review_id=manifest.latest_annual_review_id, evidence_status=verification.status, summary_line=manifest.summary_line)
    lane_path.parent.mkdir(parents=True, exist_ok=True)
    with lane_path.open("a", encoding="utf-8") as handle: handle.write(json.dumps(entry.model_dump(mode="json"), separators=(",", ":"), default=str) + "\n")
    return entry


def generate_oracle_doctrine_lineage_index(*, repo_root: Path, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleDoctrineLineageIndex:
    repo_root = repo_root.resolve(); search_root = (search_root or repo_root / "docs" / "artifacts").resolve()
    def _collect(filename: str) -> list[str]:
        if not search_root.exists(): return []
        paths = sorted(p for p in search_root.rglob(filename) if p.is_file()); refs=[]
        for p in paths:
            try: refs.append(_normalize_path(p.relative_to(repo_root)))
            except ValueError: refs.append(_normalize_path(p))
        return refs
    index = OracleDoctrineLineageIndex(generated_at_utc=now_utc or advisory_utc_now(), repo_root=_normalize_path(repo_root), search_root=_normalize_path(search_root), closure_snapshot_paths=_collect("CLOSURE_SNAPSHOT.json"), governed_exception_paths=_collect("GOVERNED_EXCEPTION_MEMO.json"), oracle_evidence_manifest_paths=_collect("ORACLE_EVIDENCE.json"), oracle_transition_evidence_paths=_collect("ORACLE_TRANSITION_EVIDENCE.json"), oracle_memory_review_evidence_paths=_collect("ORACLE_MEMORY_REVIEW_EVIDENCE.json"), oracle_weekly_digest_evidence_paths=_collect("ORACLE_WEEKLY_DIGEST_EVIDENCE.json"), oracle_doctrine_drift_evidence_paths=_collect("ORACLE_DOCTRINE_DRIFT_EVIDENCE.json"), oracle_monthly_digest_evidence_paths=_collect("ORACLE_MONTHLY_DIGEST_EVIDENCE.json"), oracle_quarterly_review_evidence_paths=_collect("ORACLE_QUARTERLY_REVIEW_EVIDENCE.json"), oracle_semiannual_audit_evidence_paths=_collect("ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json"), oracle_annual_review_evidence_paths=_collect("ORACLE_ANNUAL_REVIEW_EVIDENCE.json"), oracle_constitutional_digest_evidence_paths=_collect("ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json"), oracle_strategic_stack_evidence_paths=_collect("ORACLE_STRATEGIC_STACK_EVIDENCE.json"), annual_lane_paths=_collect("ORACLE_ANNUAL_LANE.jsonl"), constitutional_lane_paths=_collect("ORACLE_CONSTITUTIONAL_LANE.jsonl"), integrity_warnings=[], summary_line="")
    warnings=[]
    if index.oracle_annual_review_evidence_paths and not index.oracle_constitutional_digest_evidence_paths: warnings.append("Annual review evidence exists without constitutional digest evidence; the doctrine ladder is not yet sealed at the constitutional layer.")
    if index.oracle_constitutional_digest_evidence_paths and not index.constitutional_lane_paths: warnings.append("Constitutional digest evidence exists without an append-only constitutional lane; longer-horizon governance memory is not yet chained.")
    if index.oracle_transition_evidence_paths and not index.oracle_memory_review_evidence_paths: warnings.append("Transition evidence exists without memory-review evidence; the ladder contains transitions but no multi-day review layer.")
    if index.governed_exception_paths and not index.closure_snapshot_paths: warnings.append("Governed exception memo exists without a closure snapshot path in the indexed search root; verify release-governance lineage coverage.")
    layer_counts = {"closure": len(index.closure_snapshot_paths), "governed_exception": len(index.governed_exception_paths), "oracle_evidence": len(index.oracle_evidence_manifest_paths), "transition_evidence": len(index.oracle_transition_evidence_paths), "memory_review_evidence": len(index.oracle_memory_review_evidence_paths), "weekly_digest_evidence": len(index.oracle_weekly_digest_evidence_paths), "doctrine_drift_evidence": len(index.oracle_doctrine_drift_evidence_paths), "monthly_digest_evidence": len(index.oracle_monthly_digest_evidence_paths), "quarterly_review_evidence": len(index.oracle_quarterly_review_evidence_paths), "semiannual_audit_evidence": len(index.oracle_semiannual_audit_evidence_paths), "annual_review_evidence": len(index.oracle_annual_review_evidence_paths), "constitutional_digest_evidence": len(index.oracle_constitutional_digest_evidence_paths), "constitutional_lane": len(index.constitutional_lane_paths)}
    summary_line = "Oracle doctrine lineage index: " + "; ".join(f"{key}={value}" for key, value in layer_counts.items())
    if warnings: summary_line += f"; warnings={len(warnings)}"
    return index.model_copy(update={"integrity_warnings": warnings, "summary_line": summary_line})


def render_oracle_doctrine_lineage_index_markdown(index: OracleDoctrineLineageIndex) -> str:
    def _section(title: str, items: list[str]) -> str:
        body = "\n".join(f"- {item}" for item in items) or "- none"
        return f"## {title}\n\n{body}"
    warnings = "\n".join(f"- {item}" for item in index.integrity_warnings) or "- none"
    sections = [_section("Closure snapshots", index.closure_snapshot_paths), _section("Governed exception memos", index.governed_exception_paths), _section("Oracle evidence manifests", index.oracle_evidence_manifest_paths), _section("Oracle transition evidence", index.oracle_transition_evidence_paths), _section("Oracle memory-review evidence", index.oracle_memory_review_evidence_paths), _section("Oracle weekly-digest evidence", index.oracle_weekly_digest_evidence_paths), _section("Oracle doctrine-drift evidence", index.oracle_doctrine_drift_evidence_paths), _section("Oracle monthly-digest evidence", index.oracle_monthly_digest_evidence_paths), _section("Oracle quarterly-review evidence", index.oracle_quarterly_review_evidence_paths), _section("Oracle semiannual-audit evidence", index.oracle_semiannual_audit_evidence_paths), _section("Oracle annual-review evidence", index.oracle_annual_review_evidence_paths), _section("Oracle constitutional-digest evidence", index.oracle_constitutional_digest_evidence_paths), _section("Oracle strategic-stack evidence", index.oracle_strategic_stack_evidence_paths), _section("Annual lanes", index.annual_lane_paths), _section("Constitutional lanes", index.constitutional_lane_paths)]
    sections_text = "\n\n".join(sections)
    return f"""# ORACLE DOCTRINE LINEAGE INDEX

- Generated at UTC: {index.generated_at_utc.isoformat()}
- Repo root: {index.repo_root}
- Search root: {index.search_root}

## Summary

{index.summary_line}

## Integrity warnings

{warnings}

{sections_text}
"""


def _lineage_layer_paths(index: OracleDoctrineLineageIndex) -> dict[str, list[str]]:
    return {"closure_snapshot": index.closure_snapshot_paths, "oracle_evidence": index.oracle_evidence_manifest_paths, "oracle_transition_evidence": index.oracle_transition_evidence_paths, "oracle_memory_review_evidence": index.oracle_memory_review_evidence_paths, "oracle_weekly_digest_evidence": index.oracle_weekly_digest_evidence_paths, "oracle_doctrine_drift_evidence": index.oracle_doctrine_drift_evidence_paths, "oracle_monthly_digest_evidence": index.oracle_monthly_digest_evidence_paths, "oracle_quarterly_review_evidence": index.oracle_quarterly_review_evidence_paths, "oracle_semiannual_audit_evidence": index.oracle_semiannual_audit_evidence_paths, "oracle_annual_review_evidence": index.oracle_annual_review_evidence_paths, "oracle_constitutional_digest_evidence": index.oracle_constitutional_digest_evidence_paths, "oracle_strategic_stack_evidence": index.oracle_strategic_stack_evidence_paths, "annual_lane": index.annual_lane_paths, "constitutional_lane": index.constitutional_lane_paths}


def _resolve_lineage_index_path(repo_root: Path, path_ref: str) -> Path:
    candidate = Path(path_ref)
    return candidate if candidate.is_absolute() else (repo_root / candidate).resolve()



def _load_json_artifact(path: Path) -> dict | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _load_last_jsonl_artifact(path: Path) -> dict | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    for raw in reversed(lines):
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return None


def _artifact_native_strategic_backing(index: OracleDoctrineLineageIndex, repo_root_path: Path) -> tuple[str | None, str | None, int | None, bool | None]:
    candidates = [
        ("constitutional_lane", index.constitutional_lane_paths, _load_last_jsonl_artifact),
        ("constitutional_digest_manifest", index.oracle_constitutional_digest_evidence_paths, _load_json_artifact),
        ("annual_lane", index.annual_lane_paths, _load_last_jsonl_artifact),
        ("annual_review_manifest", index.oracle_annual_review_evidence_paths, _load_json_artifact),
        ("semiannual_audit_manifest", index.oracle_semiannual_audit_evidence_paths, _load_json_artifact),
    ]
    for source_name, refs, loader in candidates:
        for ref in reversed(refs):
            payload = loader(_resolve_lineage_index_path(repo_root_path, ref))
            if not payload:
                continue
            if "strategic_stack_requirement_met" not in payload and "strategic_backing_classification" not in payload:
                continue
            return (
                source_name,
                payload.get("strategic_backing_classification"),
                payload.get("strategic_stack_evidence_count"),
                payload.get("strategic_stack_requirement_met"),
            )
    return None, None, None, None


def _artifact_native_cadence_feedback(index: OracleDoctrineLineageIndex, repo_root_path: Path) -> tuple[float, int, int]:
    candidates = [
        (index.constitutional_lane_paths, _load_last_jsonl_artifact),
        (index.oracle_constitutional_digest_evidence_paths, _load_json_artifact),
        (index.annual_lane_paths, _load_last_jsonl_artifact),
        (index.oracle_annual_review_evidence_paths, _load_json_artifact),
        (index.oracle_semiannual_audit_evidence_paths, _load_json_artifact),
    ]
    for refs, loader in candidates:
        for ref in reversed(refs):
            payload = loader(_resolve_lineage_index_path(repo_root_path, ref))
            if not payload:
                continue
            if not any(key in payload for key in ("exact_evidence_support_score", "exact_feedback_confirmation_count", "exact_feedback_relief_count")):
                continue
            return (
                float(payload.get("exact_evidence_support_score", 0.0) or 0.0),
                int(payload.get("exact_feedback_confirmation_count", 0) or 0),
                int(payload.get("exact_feedback_relief_count", 0) or 0),
            )
    return 0.0, 0, 0

def _parse_indexed_lineage_artifact(path: Path) -> str | None:
    try: text = path.read_text(encoding="utf-8")
    except OSError as exc: return f"unreadable artifact ({exc})"
    if path.suffix == ".json":
        try: json.loads(text)
        except json.JSONDecodeError as exc: return f"invalid JSON at line {exc.lineno} column {exc.colno}"
        return None
    if path.suffix == ".jsonl":
        parsed_lines = 0
        for lineno, raw in enumerate(text.splitlines(), start=1):
            if not raw.strip(): continue
            parsed_lines += 1
            try: json.loads(raw)
            except json.JSONDecodeError as exc: return f"invalid JSONL at line {lineno}: {exc.msg}"
        return None if parsed_lines else "empty JSONL lane"
    return None


def verify_oracle_doctrine_lineage(*, repo_root: Path, search_root: Optional[Path] = None, now_utc: Optional[datetime] = None) -> OracleDoctrineLineageVerification:
    index = generate_oracle_doctrine_lineage_index(repo_root=repo_root, search_root=search_root, now_utc=now_utc); repo_root_path = Path(index.repo_root)
    layer_presence={}; layer_validity={}; parse_failures=[]
    for layer, refs in _lineage_layer_paths(index).items():
        layer_presence[layer] = bool(refs); valid_refs = 0
        for ref in refs:
            path = _resolve_lineage_index_path(repo_root_path, ref)
            if not path.exists(): parse_failures.append(f"{layer}: missing artifact {ref}"); continue
            parse_problem = _parse_indexed_lineage_artifact(path)
            if parse_problem is not None: parse_failures.append(f"{layer}: {ref}: {parse_problem}"); continue
            valid_refs += 1
        layer_validity[layer] = bool(refs) and valid_refs == len(refs)
    required_layers = ["oracle_evidence", "oracle_transition_evidence", "oracle_memory_review_evidence", "oracle_weekly_digest_evidence", "oracle_doctrine_drift_evidence", "oracle_monthly_digest_evidence", "oracle_quarterly_review_evidence", "oracle_semiannual_audit_evidence", "oracle_annual_review_evidence", "oracle_constitutional_digest_evidence", "annual_lane", "constitutional_lane"]
    optional_layers = ["closure_snapshot"]
    valid_required_layers = [layer for layer in required_layers if layer_validity.get(layer, False)]
    missing_required_layers = [layer for layer in required_layers if not layer_validity.get(layer, False)]
    missing_optional_layers = [layer for layer in optional_layers if not layer_validity.get(layer, False)]
    strategic_stack_layer_valid = layer_validity.get("oracle_strategic_stack_evidence", False)
    scanned_strategic_stack_evidence_count = len(index.oracle_strategic_stack_evidence_paths)
    scanned_strategic_stack_requirement_met = strategic_stack_layer_valid and scanned_strategic_stack_evidence_count > 0
    preferred_source, preferred_classification, preferred_count, preferred_requirement_met = _artifact_native_strategic_backing(index, repo_root_path)
    exact_evidence_support_score, exact_feedback_confirmation_count, exact_feedback_relief_count = _artifact_native_cadence_feedback(index, repo_root_path)
    strategic_stack_evidence_count = preferred_count if preferred_count is not None else scanned_strategic_stack_evidence_count
    strategic_stack_requirement_met = preferred_requirement_met if preferred_requirement_met is not None else scanned_strategic_stack_requirement_met
    doctrine_replayable = all(layer_validity.get(layer, False) for layer in required_layers); closure_valid = layer_validity.get("closure_snapshot", False)
    completeness_score = 0.0 if not required_layers else len(valid_required_layers) / len(required_layers); completeness_percent = int(round(completeness_score * 100))
    if doctrine_replayable and closure_valid and not parse_failures: seal_status = "FULLY_SEALED"
    elif doctrine_replayable and not parse_failures: seal_status = "CONSTITUTIONALLY_REPLAYABLE"
    elif layer_presence.get("oracle_constitutional_digest_evidence") or layer_presence.get("constitutional_lane") or layer_presence.get("oracle_annual_review_evidence"): seal_status = "PARTIALLY_SEALED"
    else: seal_status = "ADVISORY_ONLY_INCOMPLETE"
    integrity_warnings = list(index.integrity_warnings)
    if preferred_source is not None and preferred_requirement_met is not None and preferred_requirement_met != scanned_strategic_stack_requirement_met:
        integrity_warnings.append(f"artifact-native strategic backing from {preferred_source} disagrees with repository scan; preferring sealed artifact metadata for constitutional trust decisions.")
    operator_actions=[]
    if seal_status == "FULLY_SEALED": operator_actions.append("Treat the indexed repo snapshot as fully sealed; preserve closure, doctrine, and constitutional artifacts together for replay.")
    elif seal_status == "CONSTITUTIONALLY_REPLAYABLE": operator_actions.append("Treat doctrine and constitutional outputs as replayable, but restore closure-snapshot coverage before calling the repo fully sealed.")
    elif seal_status == "PARTIALLY_SEALED": operator_actions.append("Repair missing doctrine ladder rungs before trusting long-horizon summaries; partial sealing is not enough for constitutional replay.")
    else: operator_actions.append("Treat the repo as advisory-only incomplete; do not rely on doctrine or constitutional conclusions until more ladder rungs are sealed.")
    if not strategic_stack_requirement_met:
        operator_actions.append("Seal at least one strategic stack evidence bundle before treating constitutional doctrine as strategist-grounded rather than doctrine-only replay.")
    if exact_feedback_confirmation_count > 0:
        operator_actions.append("Repeated exact sealed confirmations are influencing doctrine cadence; preserve that artifact-native trail when escalating constitutional trust or review pressure.")
    elif exact_feedback_relief_count > 0:
        operator_actions.append("Repeated exact sealed relief is influencing doctrine cadence; keep any constitutional de-escalation bounded and artifact-native.")
    if parse_failures: operator_actions.append("Repair malformed or empty indexed artifacts before relying on lineage completeness scores.")
    if missing_optional_layers: operator_actions.append("Optional release-governance coverage is absent in the indexed search root; verify governed-exception paths separately if operator overrides matter.")
    summary_line = f"Oracle doctrine lineage verification: status={seal_status}; completeness={completeness_percent}% ({len(valid_required_layers)}/{len(required_layers)} required layers valid); strategic_stack={strategic_stack_evidence_count}; strategic_stack_requirement_met={str(strategic_stack_requirement_met).lower()}; backing_source={preferred_source or 'repo_scan'}; exact_support={exact_evidence_support_score:.2f}; exact_confirm={exact_feedback_confirmation_count}; exact_relief={exact_feedback_relief_count}; parse_failures={len(parse_failures)}; warnings={len(integrity_warnings)}"
    index = index.model_copy(update={"preferred_strategic_backing_source": preferred_source, "preferred_strategic_backing_classification": preferred_classification, "preferred_strategic_stack_evidence_count": strategic_stack_evidence_count, "preferred_strategic_stack_requirement_met": strategic_stack_requirement_met, "integrity_warnings": integrity_warnings})
    return OracleDoctrineLineageVerification(verified_at_utc=now_utc or advisory_utc_now(), repo_root=index.repo_root, search_root=index.search_root, preferred_strategic_backing_source=preferred_source, preferred_strategic_backing_classification=preferred_classification, exact_evidence_support_score=exact_evidence_support_score, exact_feedback_confirmation_count=exact_feedback_confirmation_count, exact_feedback_relief_count=exact_feedback_relief_count, seal_status=seal_status, completeness_score=completeness_score, completeness_percent=completeness_percent, required_layer_count=len(required_layers), valid_required_layer_count=len(valid_required_layers), layer_presence=layer_presence, layer_validity=layer_validity, strategic_stack_evidence_count=strategic_stack_evidence_count, strategic_stack_layer_valid=strategic_stack_layer_valid, strategic_stack_requirement_met=strategic_stack_requirement_met, missing_required_layers=missing_required_layers, missing_optional_layers=missing_optional_layers, parse_failures=parse_failures, integrity_warnings=index.integrity_warnings, operator_actions=operator_actions, summary_line=summary_line)


def generate_oracle_constitutional_gate(*, repo_root: Path, manifest_path: Path, search_root: Optional[Path] = None, dsse_path: Optional[Path] = None, public_key_path: Optional[Path] = None, minimum_required_seal_status: str = "FULLY_SEALED") -> OracleConstitutionalGateReport:
    lineage = verify_oracle_doctrine_lineage(repo_root=repo_root, search_root=search_root)
    verification = verify_oracle_constitutional_digest_evidence_bundle(manifest_path=manifest_path, repo_root=repo_root, dsse_path=dsse_path, public_key_path=public_key_path)
    manifest = OracleConstitutionalDigestEvidenceManifest.model_validate(json.loads(manifest_path.resolve().read_text(encoding="utf-8")))
    blocking_reasons=[]
    if verification.status != "VERIFIED": blocking_reasons.append(f"constitutional digest evidence status is {verification.status}")
    if manifest.constitutional_digest_classification == "CONSTITUTIONAL_EVIDENCE_GAP": blocking_reasons.append("constitutional digest classification is CONSTITUTIONAL_EVIDENCE_GAP")
    if _lineage_seal_rank(lineage.seal_status) < _lineage_seal_rank(minimum_required_seal_status): blocking_reasons.append(f"lineage seal status {lineage.seal_status} is below required threshold {minimum_required_seal_status}")
    if not lineage.strategic_stack_requirement_met: blocking_reasons.append("lineage is missing sealed strategic stack evidence coverage")
    if lineage.parse_failures: blocking_reasons.append("lineage verification reported parse failures")
    if not blocking_reasons: trust_status = "TRUSTED"
    elif verification.status == "VERIFIED" and _lineage_seal_rank(lineage.seal_status) >= _lineage_seal_rank("CONSTITUTIONALLY_REPLAYABLE"): trust_status = "TRUST_RESTRICTED"
    else: trust_status = "UNTRUSTED"
    trusted_for_constitutional_use = trust_status == "TRUSTED"
    operator_actions=[]
    if trusted_for_constitutional_use: operator_actions.append("Treat the constitutional digest as trusted for long-horizon doctrine use under the current lineage threshold.")
    elif trust_status == "TRUST_RESTRICTED": operator_actions.append("Treat the constitutional digest as replayable but not fully trusted; restore the missing lineage coverage before escalating reliance.")
    else: operator_actions.append("Do not treat the constitutional digest as trusted; repair evidence verification or lineage sealing before relying on constitutional doctrine outputs.")
    operator_actions.extend(lineage.operator_actions)
    if verification.status != "VERIFIED": operator_actions.append("Regenerate or re-verify constitutional digest evidence before treating higher-order doctrine outputs as trusted.")
    summary_line = f"Oracle constitutional gate: trust_status={trust_status}; trusted={str(trusted_for_constitutional_use).lower()}; lineage={lineage.seal_status}; required={minimum_required_seal_status}; manifest_status={verification.status}; strategic_stack={lineage.strategic_stack_evidence_count}; strategic_stack_requirement_met={str(lineage.strategic_stack_requirement_met).lower()}; backing_source={lineage.preferred_strategic_backing_source or 'repo_scan'}; exact_support={lineage.exact_evidence_support_score:.2f}; exact_confirm={lineage.exact_feedback_confirmation_count}; exact_relief={lineage.exact_feedback_relief_count}; digest={manifest.constitutional_digest_classification}"
    try: manifest_ref = manifest_path.resolve().relative_to(repo_root.resolve())
    except ValueError: manifest_ref = manifest_path.resolve()
    return OracleConstitutionalGateReport(generated_at_utc=advisory_utc_now(), repo_root=_normalize_path(repo_root.resolve()), search_root=_normalize_path((search_root or (repo_root / "docs" / "artifacts")).resolve()), preferred_strategic_backing_source=lineage.preferred_strategic_backing_source, preferred_strategic_backing_classification=lineage.preferred_strategic_backing_classification, exact_evidence_support_score=lineage.exact_evidence_support_score, exact_feedback_confirmation_count=lineage.exact_feedback_confirmation_count, exact_feedback_relief_count=lineage.exact_feedback_relief_count, manifest_path=_normalize_path(manifest_ref), minimum_required_seal_status=minimum_required_seal_status, lineage_seal_status=lineage.seal_status, lineage_completeness_percent=lineage.completeness_percent, constitutional_digest_classification=manifest.constitutional_digest_classification, manifest_verification_status=verification.status, strategic_stack_evidence_count=lineage.strategic_stack_evidence_count, strategic_stack_requirement_met=lineage.strategic_stack_requirement_met, trust_status=trust_status, trusted_for_constitutional_use=trusted_for_constitutional_use, blocking_reasons=blocking_reasons, operator_actions=list(dict.fromkeys(operator_actions)), facts=[f"strategic_stack_evidence_count={lineage.strategic_stack_evidence_count}", f"strategic_stack_requirement_met={lineage.strategic_stack_requirement_met}", f"preferred_strategic_backing_source={lineage.preferred_strategic_backing_source or 'repo_scan'}", f"preferred_strategic_backing_classification={lineage.preferred_strategic_backing_classification or 'none'}", f"exact_evidence_support_score={lineage.exact_evidence_support_score:.2f}", f"exact_feedback_confirmation_count={lineage.exact_feedback_confirmation_count}", f"exact_feedback_relief_count={lineage.exact_feedback_relief_count}"], summary_line=summary_line)


def render_oracle_constitutional_gate_markdown(report: OracleConstitutionalGateReport) -> str:
    blocking = "\n".join(f"- {item}" for item in report.blocking_reasons) or "- none"; actions = "\n".join(f"- {item}" for item in report.operator_actions) or "- none"
    return f"""# ORACLE CONSTITUTIONAL GATE

- Generated at UTC: {report.generated_at_utc.isoformat()}
- Repo root: {report.repo_root}
- Search root: {report.search_root}
- Manifest path: {report.manifest_path}
- Trust status: {report.trust_status}
- Trusted for constitutional use: {'yes' if report.trusted_for_constitutional_use else 'no'}
- Minimum required seal status: {report.minimum_required_seal_status}
- Observed lineage seal status: {report.lineage_seal_status}
- Lineage completeness: {report.lineage_completeness_percent}%
- Manifest verification status: {report.manifest_verification_status}
- Strategic stack evidence count: {report.strategic_stack_evidence_count}
- Strategic stack requirement met: {'yes' if report.strategic_stack_requirement_met else 'no'}
- Preferred strategic backing source: {report.preferred_strategic_backing_source or "repo_scan"}
- Exact evidence support score: {report.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {report.exact_feedback_confirmation_count}
- Exact feedback relief signals: {report.exact_feedback_relief_count}
- Constitutional digest classification: {report.constitutional_digest_classification or 'unknown'}

## Summary

{report.summary_line}

## Blocking reasons

{blocking}

## Operator actions

{actions}
"""


def render_oracle_doctrine_lineage_verification_markdown(verification: OracleDoctrineLineageVerification) -> str:
    def _kv_lines(payload: dict[str, bool]) -> str: return "\n".join(f"- {key}: {'yes' if value else 'no'}" for key, value in payload.items()) or "- none"
    missing_required = "\n".join(f"- {item}" for item in verification.missing_required_layers) or "- none"; missing_optional = "\n".join(f"- {item}" for item in verification.missing_optional_layers) or "- none"; parse_failures = "\n".join(f"- {item}" for item in verification.parse_failures) or "- none"; warnings = "\n".join(f"- {item}" for item in verification.integrity_warnings) or "- none"; actions = "\n".join(f"- {item}" for item in verification.operator_actions) or "- none"
    return f"""# ORACLE DOCTRINE LINEAGE VERIFICATION

- Verified at UTC: {verification.verified_at_utc.isoformat()}
- Repo root: {verification.repo_root}
- Search root: {verification.search_root}
- Seal status: {verification.seal_status}
- Completeness: {verification.completeness_percent}% ({verification.valid_required_layer_count}/{verification.required_layer_count} required layers valid)
- Strategic stack evidence count: {verification.strategic_stack_evidence_count}
- Strategic stack layer valid: {'yes' if verification.strategic_stack_layer_valid else 'no'}
- Strategic stack requirement met: {'yes' if verification.strategic_stack_requirement_met else 'no'}
- Preferred strategic backing source: {verification.preferred_strategic_backing_source or "repo_scan"}
- Exact evidence support score: {verification.exact_evidence_support_score:.2f}
- Exact feedback confirmations: {verification.exact_feedback_confirmation_count}
- Exact feedback relief signals: {verification.exact_feedback_relief_count}

## Summary

{verification.summary_line}

## Layer presence

{_kv_lines(verification.layer_presence)}

## Layer validity

{_kv_lines(verification.layer_validity)}

## Missing required layers

{missing_required}

## Missing optional layers

{missing_optional}

## Parse failures

{parse_failures}

## Integrity warnings

{warnings}

## Operator actions

{actions}
"""
