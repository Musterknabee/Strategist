"""Manifest and repo-asset verification for single-tenant deployment bundles."""
from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.deployment_env_check import symlink_components_preserving_path
from strategy_validator.cli.single_tenant_deployment_bundle_common import (
    GeneratedFile,
    _REPO_ASSET_SCHEMA_VERSION,
    _REQUIRED_GENERATED_FILES,
    _REQUIRED_REPO_ASSETS,
    _sha256_file,
)
from strategy_validator.cli.single_tenant_deployment_bundle_verification_common import (
    _is_safe_bundle_relative_path,
    _is_valid_sha256,
    _manifest_generated_file_entries,
)

def _verify_manifest_generated_file_digests(out: Path, manifest: dict[str, object]) -> list[str]:
    """Verify that manifest-listed bundle assets still match size/digest evidence."""

    errors: list[str] = []
    raw_entries = manifest.get("generated_files", [])
    if not isinstance(raw_entries, list):
        return ["manifest generated_files is not a list"]

    entries = _manifest_generated_file_entries(manifest)
    for item in raw_entries:
        if not isinstance(item, dict):
            errors.append("manifest generated_files contains a non-object entry")
            continue
        relative = item.get("path")
        if not _is_safe_bundle_relative_path(relative):
            errors.append(f"manifest generated_files contains unsafe path: {relative!r}")
            continue
        relative_str = str(relative)
        if relative_str == "manifest.json":
            # The manifest cannot self-hash stably.  It is validated by schema
            # checks above and explicitly excluded from generated_files on write.
            errors.append("manifest generated_files must not include manifest.json self-reference")
            continue
        path = out / relative_str
        if path.is_symlink():
            errors.append(f"manifest-listed generated file is a symlink: {relative_str}")
            continue
        if not path.exists():
            errors.append(f"manifest-listed generated file missing: {relative_str}")
            continue
        if not path.is_file():
            errors.append(f"manifest-listed generated path is not a regular file: {relative_str}")
            continue

        expected_size = item.get("size_bytes")
        expected_sha256 = item.get("sha256")
        actual_size = path.stat().st_size
        actual_sha256 = _sha256_file(path)
        if expected_size != actual_size:
            errors.append(
                f"manifest-listed generated file size mismatch: {relative_str} "
                f"expected={expected_size!r} actual={actual_size}"
            )
        if expected_sha256 != actual_sha256:
            errors.append(
                f"manifest-listed generated file sha256 mismatch: {relative_str} "
                f"expected={expected_sha256!r} actual={actual_sha256}"
            )

    for relative in _REQUIRED_GENERATED_FILES:
        if relative == "manifest.json":
            continue
        if relative not in entries:
            errors.append(f"required generated file missing from manifest digest inventory: {relative}")

    return errors

def _verify_repo_asset_manifest_payload(repo_assets: object) -> list[str]:
    """Validate the portable source-asset manifest carried in the bundle."""

    errors: list[str] = []
    if not isinstance(repo_assets, dict):
        return ["repo-assets.manifest.json is not a JSON object"]
    if repo_assets.get("schema_version") != _REPO_ASSET_SCHEMA_VERSION:
        errors.append("repo-assets.manifest.json schema_version is not single_tenant_repo_assets_manifest/v1")

    missing_count = repo_assets.get("missing_asset_count")
    if missing_count not in {0, 0.0}:
        errors.append("repo-assets.manifest.json records missing required repo assets")

    assets = repo_assets.get("assets")
    if not isinstance(assets, list):
        errors.append("repo-assets.manifest.json assets is not a list")
        return errors

    by_path: dict[str, dict[str, object]] = {}
    for item in assets:
        if not isinstance(item, dict):
            errors.append("repo-assets.manifest.json assets contains a non-object entry")
            continue
        relative = item.get("path")
        if not _is_safe_bundle_relative_path(relative):
            errors.append(f"repo-assets.manifest.json contains unsafe asset path: {relative!r}")
            continue
        relative_str = str(relative)
        if relative_str in by_path:
            errors.append(f"repo-assets.manifest.json contains duplicate asset path: {relative_str}")
        by_path[relative_str] = item

        if item.get("is_symlink") is True:
            errors.append(f"repo-assets.manifest.json marks required asset as a symlink: {relative_str}")
        if item.get("exists") is not True:
            errors.append(f"repo-assets.manifest.json marks required asset as missing: {relative_str}")
        if not _is_valid_sha256(item.get("sha256")):
            errors.append(f"repo-assets.manifest.json asset sha256 is invalid: {relative_str}")
        size = item.get("size_bytes")
        if not isinstance(size, int) or size < 0:
            errors.append(f"repo-assets.manifest.json asset size_bytes is invalid: {relative_str}")

    for relative in _REQUIRED_REPO_ASSETS:
        if relative not in by_path:
            errors.append(f"required repo asset missing from repo-assets.manifest.json: {relative}")

    return errors

def _collect_generated_files(output_dir: Path) -> tuple[GeneratedFile, ...]:
    if symlink_components_preserving_path(output_dir):
        return ()
    files: list[GeneratedFile] = []
    for relative in _REQUIRED_GENERATED_FILES:
        path = output_dir / relative
        if path.is_symlink() or not path.is_file():
            continue
        files.append(
            GeneratedFile(
                path=relative,
                sha256=_sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    return tuple(files)
