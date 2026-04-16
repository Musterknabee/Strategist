from __future__ import annotations

from pathlib import Path
from typing import Iterable, Literal

from strategy_validator.validator.oracle_schema_registry import iter_registered_artifacts, load_artifact_payload

OracleSupportVerificationStatus = Literal["VERIFIED", "INCOMPLETE", "UNVERIFIED", "ABSENT"]


def verification_status_for_manifest(manifest_path: Path) -> tuple[OracleSupportVerificationStatus, str | None]:
    verification_path = manifest_path.with_name(f"{manifest_path.stem}.verification.json")
    if not verification_path.exists():
        return "ABSENT", None
    try:
        payload = load_artifact_payload(verification_path)
    except Exception:
        return "UNVERIFIED", str(verification_path)
    status = payload.get("status")
    if status in {"VERIFIED", "INCOMPLETE", "UNVERIFIED"}:
        return status, str(verification_path)
    return "UNVERIFIED", str(verification_path)


def discover_report_support_manifests(
    *,
    report_path: Path,
    repo_root: Path,
    search_root: Path | None = None,
    manifest_schemas: set[str] | None = None,
    manifest_families: set[str] | None = None,
) -> list[Path]:
    resolved_report_path = report_path.resolve()
    resolved_repo_root = repo_root.resolve()
    resolved_search_root = (search_root or repo_root).resolve()
    if not resolved_search_root.exists():
        return []
    matches: list[Path] = []
    seen: set[Path] = set()
    for candidate, _, _, manifest in iter_registered_artifacts(
        roots=[resolved_search_root],
        expected_schemas=manifest_schemas,
        expected_families=manifest_families,
    ):
        subjects = getattr(manifest, "subjects", []) or []
        for subject in subjects:
            try:
                subject_path = (resolved_repo_root / subject.path).resolve()
            except Exception:
                continue
            if subject_path == resolved_report_path:
                resolved_candidate = candidate.resolve()
                if resolved_candidate not in seen:
                    seen.add(resolved_candidate)
                    matches.append(resolved_candidate)
                break
    return sorted(matches)


def summarize_support_verification(manifest_paths: Iterable[Path]) -> tuple[OracleSupportVerificationStatus, list[str], str]:
    statuses: list[OracleSupportVerificationStatus] = []
    verification_paths: list[str] = []
    manifest_count = 0
    for manifest_path in manifest_paths:
        manifest_count += 1
        status, verification_path = verification_status_for_manifest(Path(manifest_path))
        statuses.append(status)
        if verification_path:
            verification_paths.append(verification_path)
    if not statuses:
        summary = "Support verification status=ABSENT; no formal evidence verification artifacts were discovered for the current support chain."
        return "ABSENT", [], summary
    if any(status == "UNVERIFIED" for status in statuses):
        aggregate: OracleSupportVerificationStatus = "UNVERIFIED"
    elif any(status == "INCOMPLETE" for status in statuses):
        aggregate = "INCOMPLETE"
    elif all(status == "VERIFIED" for status in statuses):
        aggregate = "VERIFIED"
    else:
        aggregate = "ABSENT"
    summary = (
        f"Support verification status={aggregate}; manifests={manifest_count}; "
        f"verified={sum(1 for item in statuses if item == 'VERIFIED')}; "
        f"incomplete={sum(1 for item in statuses if item == 'INCOMPLETE')}; "
        f"unverified={sum(1 for item in statuses if item == 'UNVERIFIED')}; "
        f"absent={sum(1 for item in statuses if item == 'ABSENT')}"
    )
    return aggregate, verification_paths, summary
