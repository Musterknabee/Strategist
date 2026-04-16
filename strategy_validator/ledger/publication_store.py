from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from strategy_validator.application.evidence_verification import compute_payload_digest
from strategy_validator.contracts.publications import PublicationArtifactRecord


class PublicationStore(Protocol):
    def publish_json_artifact(
        self,
        *,
        publication_label: str,
        artifact_path: Path,
        payload: dict,
        source_snapshot_id: str | None = None,
    ) -> PublicationArtifactRecord: ...


@dataclass(slots=True)
class FilesystemPublicationStore:
    publication_family: str = 'application_publication'

    def publish_json_artifact(
        self,
        *,
        publication_label: str,
        artifact_path: Path,
        payload: dict,
        source_snapshot_id: str | None = None,
    ) -> PublicationArtifactRecord:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text(json.dumps(payload, indent=2, default=str) + '\n', encoding='utf-8')
        return PublicationArtifactRecord(
            publication_id=f'pub-{uuid4().hex}',
            publication_family=self.publication_family,
            manifest_path=str(artifact_path),
            artifact_paths=[str(artifact_path)],
            source_snapshot_ids=[source_snapshot_id] if source_snapshot_id else [],
            digest_sha256=compute_payload_digest(payload),
        )
