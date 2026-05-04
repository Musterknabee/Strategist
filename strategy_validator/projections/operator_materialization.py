from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


@dataclass(frozen=True)
class OperatorBundleArtifactCopy:
    artifact_kind: str
    source_path: Path


@dataclass(frozen=True)
class OperatorBundleMaterializationRequest:
    pack_root: Path
    json_filename: str
    markdown_filename: str
    html_filename: str | None = None
    artifact_copies: tuple[OperatorBundleArtifactCopy, ...] = ()


@dataclass(frozen=True)
class OperatorBundleMaterializationResult:
    pack_root: Path
    json_path: Path
    markdown_path: Path
    html_path: Path | None
    artifact_pack_paths: dict[str, str]



def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()



def compute_report_provenance_digest(report: Any) -> str:
    payload = report.model_dump(mode="json")
    payload.pop("generated_at_utc", None)
    payload.pop("provenance_digest_sha256", None)
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return _sha256_bytes(stable)



def with_report_provenance_digest(report: Any) -> Any:
    return report.model_copy(update={"provenance_digest_sha256": compute_report_provenance_digest(report)})



def materialize_operator_bundle(
    request: OperatorBundleMaterializationRequest,
    *,
    report: Any,
    markdown: str,
    html: str | None = None,
) -> tuple[Any, OperatorBundleMaterializationResult]:
    pack_root = request.pack_root
    pack_root.mkdir(parents=True, exist_ok=True)
    artifact_pack_paths: dict[str, str] = {}
    if request.artifact_copies:
        artifacts_root = pack_root / "artifacts"
        artifacts_root.mkdir(parents=True, exist_ok=True)
        for artifact in request.artifact_copies:
            destination = artifacts_root / f"{artifact.artifact_kind}__{artifact.source_path.name}"
            shutil.copy2(artifact.source_path, destination)
            artifact_pack_paths[str(artifact.source_path)] = str(destination.relative_to(pack_root))
    updated_report = with_report_provenance_digest(report)
    json_path = pack_root / request.json_filename
    markdown_path = pack_root / request.markdown_filename
    json_path.write_text(json.dumps(updated_report.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    markdown_path.write_text(markdown, encoding="utf-8")
    html_path: Path | None = None
    if request.html_filename is not None and html is not None:
        html_path = pack_root / request.html_filename
        html_path.write_text(html, encoding="utf-8")
    return updated_report, OperatorBundleMaterializationResult(
        pack_root=pack_root,
        json_path=json_path,
        markdown_path=markdown_path,
        html_path=html_path,
        artifact_pack_paths=artifact_pack_paths,
    )



def build_operator_bundle_output_paths(result: OperatorBundleMaterializationResult) -> list[Path]:
    output_paths: list[Path] = [result.json_path, result.markdown_path]
    if result.html_path is not None:
        output_paths.append(result.html_path)
    return output_paths
