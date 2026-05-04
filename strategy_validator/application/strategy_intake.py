"""Governed strategy intake artifact operations.

Artifact-plane only: proposal intake creates files and read projections, but does
not call the validator orchestrator, ledger writer, broker adapters, or live
execution paths.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_ingress import normalize_proposal_for_adjudication
from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.application.source_registry import SourceRegistry
from strategy_validator.contracts.proposal_manifest import ProposalManifest
from strategy_validator.contracts.strategy_intake import (
    StrategyIntakeArtifact,
    StrategyIntakeIndex,
    StrategyIntakeIndexEntry,
    StrategyIntakeReceipt,
    StrategyIntakeRequest,
)
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_ID_RE = re.compile(r"[^a-zA-Z0-9_.:-]+")
_MAX_INDEX_ENTRIES = 100


def strategy_intake_root_directory(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_STRATEGY_INTAKE_ROOT", "").strip()
    if raw:
        p = Path(raw).expanduser()
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    return (artifact_root_directory(repo_root) / "strategy_intake").resolve()


def _json_default(o: Any) -> str:
    if hasattr(o, "isoformat"):
        return o.isoformat()
    raise TypeError(type(o))


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_slug(value: str, *, fallback: str = "strategy") -> str:
    slug = _ID_RE.sub("-", value.strip().lower()).strip("-_.:")
    return (slug or fallback)[:80]


def _idem_digest(key: str) -> str:
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def _derive_proposal_id(request: StrategyIntakeRequest) -> str:
    stable = {
        "strategy_name": request.strategy_name,
        "thesis": request.thesis,
        "target_universe": request.target_universe,
        "intended_horizon": request.intended_horizon,
        "expected_edge": request.expected_edge,
    }
    return f"proposal-{_safe_slug(request.strategy_name)}-{canonical_json_sha256(stable)[:12]}"


def _derive_intake_id(request: StrategyIntakeRequest, when: datetime) -> str:
    if request.idempotency_key:
        return f"intake-{_safe_slug(request.strategy_name)}-{_idem_digest(request.idempotency_key)[:12]}"
    body = request.model_dump(mode="json") | {"created_at_utc": when.isoformat()}
    return f"intake-{_safe_slug(request.strategy_name)}-{canonical_json_sha256(body)[:12]}"


def _artifact_path(root: Path, intake_id: str) -> Path:
    return root / "intakes" / f"{intake_id}.json"


def _index_path(root: Path) -> Path:
    return root / "latest" / "strategy_intake_index.json"


def _idempotency_path(root: Path, key: str) -> Path:
    return root / "idempotency" / f"{_idem_digest(key)}.json"


def _build_proposal_manifest(request: StrategyIntakeRequest, *, proposal_id: str) -> ProposalManifest:
    evaluation_plan = dict(request.evaluation_plan)
    evaluation_plan.setdefault("intake_source", "ui_strategy_intake")
    evaluation_plan.setdefault("expected_edge", request.expected_edge)
    if request.data_dependencies:
        evaluation_plan.setdefault("data_dependencies", list(request.data_dependencies))
    if request.falsification_rules:
        evaluation_plan.setdefault("falsification_rules", list(request.falsification_rules))
    if request.risk_assumptions:
        evaluation_plan.setdefault("risk_assumptions", list(request.risk_assumptions))
    if request.tags:
        evaluation_plan.setdefault("tags", list(request.tags))
    return ProposalManifest(
        proposal_id=proposal_id,
        thesis=request.thesis,
        target_universe=request.target_universe,
        intended_horizon=request.intended_horizon,
        required_evidence_class=request.required_evidence_class,
        feature_dependencies=request.feature_dependencies,
        source_registry_references=request.source_registry_references,
        evaluation_plan=evaluation_plan,
    )


def _finalize_artifact(artifact: StrategyIntakeArtifact) -> StrategyIntakeArtifact:
    body = artifact.model_dump(mode="json", exclude={"intake_sha256"})
    return artifact.model_copy(update={"intake_sha256": canonical_json_sha256(body)})


def _authorization_payload(auth_context: UiMutationAuthContext | None) -> dict[str, Any]:
    if auth_context is None:
        return {}
    return {
        "runtime_mode": auth_context.runtime_mode,
        "authorization_mode": auth_context.authorization_mode,
        "principal_id": auth_context.principal_id,
        "principal_source": auth_context.principal_source,
        "role": auth_context.role,
        "scopes": list(auth_context.scopes),
    }


def _entry_from_artifact(path: Path, artifact: StrategyIntakeArtifact) -> StrategyIntakeIndexEntry:
    proposal = artifact.proposal_manifest
    return StrategyIntakeIndexEntry(
        intake_id=artifact.intake_id,
        proposal_id=artifact.proposal_id,
        strategy_name=artifact.strategy_name,
        created_at_utc=artifact.created_at_utc,
        operator_id=artifact.operator_id,
        target_universe=proposal.target_universe,
        intended_horizon=proposal.intended_horizon,
        readiness_state=artifact.readiness_state,
        artifact_path=str(path),
        artifact_sha256=artifact.intake_sha256,
        tags=artifact.tags,
    )


def _load_artifacts(root: Path) -> list[tuple[Path, StrategyIntakeArtifact]]:
    intake_dir = root / "intakes"
    if not intake_dir.is_dir():
        return []
    artifacts: list[tuple[Path, StrategyIntakeArtifact]] = []
    for path in sorted(intake_dir.glob("*.json")):
        try:
            artifacts.append((path, StrategyIntakeArtifact.model_validate(_read_json(path))))
        except Exception:
            continue
    return sorted(artifacts, key=lambda item: item[1].created_at_utc, reverse=True)


def build_strategy_intake_index(*, repo_root: Path | None = None) -> StrategyIntakeIndex:
    root = strategy_intake_root_directory(repo_root)
    entries = [_entry_from_artifact(path, artifact) for path, artifact in _load_artifacts(root)[:_MAX_INDEX_ENTRIES]]
    return StrategyIntakeIndex(generated_at_utc=datetime.now(timezone.utc), intake_count=len(entries), entries=tuple(entries))


def write_strategy_intake_index(*, repo_root: Path | None = None) -> Path:
    root = strategy_intake_root_directory(repo_root)
    path = _index_path(root)
    _write_json(path, build_strategy_intake_index(repo_root=repo_root).model_dump(mode="json"))
    return path


def _receipt_from_existing(
    *,
    artifact_path: Path,
    index_path: Path,
    artifact: StrategyIntakeArtifact,
    auth_context: UiMutationAuthContext | None,
) -> StrategyIntakeReceipt:
    return StrategyIntakeReceipt(
        generated_at_utc=datetime.now(timezone.utc),
        accepted=True,
        intake_id=artifact.intake_id,
        proposal_id=artifact.proposal_id,
        artifact_path=str(artifact_path),
        artifact_sha256=artifact.intake_sha256,
        index_path=str(index_path),
        idempotency_status="REPLAYED",
        duplicate_of_intake_id=artifact.intake_id,
        summary_line=f"Replayed strategy intake {artifact.intake_id} for {artifact.strategy_name}",
        authorization=_authorization_payload(auth_context),
    )


def submit_strategy_intake(
    request: StrategyIntakeRequest,
    *,
    auth_context: UiMutationAuthContext | None = None,
    repo_root: Path | None = None,
) -> StrategyIntakeReceipt:
    root = strategy_intake_root_directory(repo_root)
    when = datetime.now(timezone.utc)
    proposal_id = _derive_proposal_id(request)
    intake_id = _derive_intake_id(request, when)
    artifact_path = _artifact_path(root, intake_id)
    index_path = _index_path(root)

    if request.idempotency_key:
        idem_path = _idempotency_path(root, request.idempotency_key)
        if idem_path.is_file():
            previous = _read_json(idem_path)
            previous_path = Path(str(previous.get("artifact_path", "")))
            if previous_path.is_file():
                existing = StrategyIntakeArtifact.model_validate(_read_json(previous_path))
                write_strategy_intake_index(repo_root=repo_root)
                return _receipt_from_existing(
                    artifact_path=previous_path,
                    index_path=index_path,
                    artifact=existing,
                    auth_context=auth_context,
                )

    proposal_manifest = _build_proposal_manifest(request, proposal_id=proposal_id)
    normalized = normalize_proposal_for_adjudication(proposal_manifest, source_registry=SourceRegistry(), feature_lineage=())
    ingestion = normalized["normalized_request"]["ingestion"]
    blockers = tuple(f"MISSING_SOURCE:{src}" for src in ingestion.get("missing_sources", []))
    warnings = tuple(f"UNRESOLVED_FEATURE:{feature}" for feature in ingestion.get("unresolved_features", []))
    readiness_state = "RESEARCH_INTAKE_RECORDED" if not blockers else "RESEARCH_INTAKE_BLOCKED"

    artifact = _finalize_artifact(
        StrategyIntakeArtifact(
            intake_id=intake_id,
            proposal_id=proposal_id,
            strategy_name=request.strategy_name,
            created_at_utc=when,
            operator_id=request.operator_id,
            proposal_manifest=proposal_manifest,
            expected_edge=request.expected_edge,
            data_dependencies=request.data_dependencies,
            falsification_rules=request.falsification_rules,
            risk_assumptions=request.risk_assumptions,
            tags=request.tags,
            readiness_state=readiness_state,
            blockers=blockers,
            warnings=warnings,
        )
    )
    _write_json(artifact_path, artifact.model_dump(mode="json"))
    write_strategy_intake_index(repo_root=repo_root)

    if request.idempotency_key:
        _write_json(
            _idempotency_path(root, request.idempotency_key),
            {
                "schema_version": "strategy_intake_idempotency/v1",
                "idempotency_key_sha256": _idem_digest(request.idempotency_key),
                "intake_id": artifact.intake_id,
                "proposal_id": artifact.proposal_id,
                "artifact_path": str(artifact_path),
                "artifact_sha256": artifact.intake_sha256,
                "recorded_at_utc": when.isoformat(),
            },
        )

    return StrategyIntakeReceipt(
        generated_at_utc=datetime.now(timezone.utc),
        accepted=True,
        intake_id=artifact.intake_id,
        proposal_id=artifact.proposal_id,
        artifact_path=str(artifact_path),
        artifact_sha256=artifact.intake_sha256,
        index_path=str(index_path),
        summary_line=f"Recorded strategy intake {artifact.intake_id} for {artifact.strategy_name}",
        authorization=_authorization_payload(auth_context),
    )


def build_ui_strategy_intake_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = strategy_intake_root_directory(repo_root)
    index_path = _index_path(root)
    degraded: list[str] = []
    if not index_path.is_file():
        degraded.append("NO_STRATEGY_INTAKE_INDEX")
        index = StrategyIntakeIndex(generated_at_utc=datetime.now(timezone.utc), intake_count=0, entries=())
    else:
        try:
            index = StrategyIntakeIndex.model_validate(_read_json(index_path))
        except Exception:
            degraded.append("STRATEGY_INTAKE_INDEX_UNREADABLE")
            index = StrategyIntakeIndex(generated_at_utc=datetime.now(timezone.utc), intake_count=0, entries=())
    return {
        "schema_version": "ui_strategy_intake/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "authority_boundary": "ADVISORY_ARTIFACT_ONLY",
        "scan_root": str(root),
        "index_path": str(index_path),
        "degraded": degraded,
        "latest": index.model_dump(mode="json"),
    }


def submit_ui_strategy_intake(request: StrategyIntakeRequest, *, auth_context: UiMutationAuthContext | None = None) -> dict[str, Any]:
    return submit_strategy_intake(request, auth_context=auth_context).model_dump(mode="json")


__all__ = [
    "build_strategy_intake_index",
    "build_ui_strategy_intake_latest_payload",
    "strategy_intake_root_directory",
    "submit_strategy_intake",
    "submit_ui_strategy_intake",
    "write_strategy_intake_index",
]
