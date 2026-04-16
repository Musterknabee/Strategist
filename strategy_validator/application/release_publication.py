from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.burnin import summarize_burnin_set
from strategy_validator.contracts.operator_reports import ReleaseReadinessReport
from strategy_validator.core.exceptions import ConstitutionalViolation
from strategy_validator.ledger.publication_store import FilesystemPublicationStore
from strategy_validator.validator.rollout_ops import build_rollout_bundle
from strategy_validator.validator.services.integrity_gate_service import get_current_readiness


def publish_release_readiness_bundle(
    *,
    policy_path: Path,
    keyed_host_fingerprint_path: Path,
    burnin_artifact_paths: list[Path],
    scope: str,
    publication_path: Path,
) -> dict[str, Any]:
    readiness = get_current_readiness()
    if not readiness.adjudication_allowed:
        blocker_codes = [blocker.code for blocker in readiness.blockers]
        raise ConstitutionalViolation(
            'RELEASE_PUBLICATION_BLOCKED: '
            f'readiness_status={readiness.status}; blocker_codes={",".join(blocker_codes) or "NONE"}'
        )
    bundle = build_rollout_bundle(
        policy_path=policy_path,
        keyed_host_fingerprint_path=keyed_host_fingerprint_path,
        burnin_artifact_paths=burnin_artifact_paths,
        scope=scope,
    )
    burnin_summary = summarize_burnin_set(*burnin_artifact_paths) if burnin_artifact_paths else {
        'artifact_count': 0,
        'artifacts': [],
        'total_round_count': 0,
        'total_fallback_count': 0,
        'total_stale_count': 0,
    }
    payload = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'readiness': readiness.model_dump(mode='json'),
        'rollout_bundle': bundle.model_dump(mode='json'),
        'burnin_summary': burnin_summary,
    }
    store = FilesystemPublicationStore(publication_family='release_readiness_publication')
    record = store.publish_json_artifact(
        publication_label='release_readiness_bundle',
        artifact_path=publication_path,
        payload=payload,
        source_snapshot_id=readiness.config_fingerprint,
    )
    report = ReleaseReadinessReport(
        report_id=f'release:{readiness.config_fingerprint}',
        readiness_status=readiness.status,
        adjudication_allowed=readiness.adjudication_allowed,
        blocker_codes=[blocker.code for blocker in readiness.blockers],
        published_artifact_paths=record.artifact_paths,
        summary_line=f"Readiness {readiness.status}; published {len(record.artifact_paths)} artifact(s).",
    )
    return {
        'publication_record': record.model_dump(mode='json'),
        'release_report': report.model_dump(mode='json'),
        'payload': payload,
    }
