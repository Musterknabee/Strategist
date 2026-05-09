"""Shared contracts and helpers for single-tenant deployment bundle generation."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from strategy_validator.cli.deployment_env_check import (
    EnvCheckReport,
    parse_env_file,
    symlink_components_preserving_path,
)

_SCHEMA_VERSION = "single_tenant_deployment_bundle/v1"
_FRONTEND_PACKAGE = "ui/strategist-web"
_DEFAULT_OUTPUT_DIR = "scratch/single-tenant-deployment-bundle"
_REPO_ASSET_SCHEMA_VERSION = "single_tenant_repo_assets_manifest/v1"
_REQUIRED_REPO_ASSETS = (
    "Dockerfile",
    "deployment.env.sample",
    "docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md",
    "scripts/single_tenant_api_smoke.py",
    "strategy_validator/cli/single_tenant_preflight.py",
    "strategy_validator/cli/deployment_env_check.py",
    "strategy_validator/cli/single_tenant_deployment_bundle.py",
    "strategy_validator/cli/single_tenant_deployment_acceptance.py",
    "strategy_validator/cli/single_tenant_deployment_evidence.py",
)

_SECRET_KEY_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "KEY")
_REQUIRED_GENERATED_FILES = (
    "manifest.json",
    "deployment.env.redacted.json",
    "repo-assets.manifest.json",
    ".gitignore",
    "docker-compose.single-tenant.yml",
    "systemd/strategy-validator.service",
    "commands/compose-up.sh",
    "commands/compose-down.sh",
    "commands/preflight.sh",
    "commands/api-smoke.sh",
    "commands/api-smoke.py",
    "commands/verify-ledger.sh",
    "commands/backup-ledger.sh",
    "commands/restore-ledger.sh",
    "commands/acceptance.sh",
    "commands/post-deploy-evidence.sh",
    "README.md",
)

@dataclass(frozen=True)
class GeneratedFile:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class DeploymentBundleReport:
    schema_version: str
    ok: bool
    output_dir: str
    env_file: str
    generated_at_utc: str
    deployment_model: str
    frontend_expected_package: str
    frontend_package_present: bool
    frontend_readiness_claimed: bool
    env_check_ok: bool
    generated_files: tuple[GeneratedFile, ...]
    errors: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "output_dir": self.output_dir,
            "env_file": self.env_file,
            "generated_at_utc": self.generated_at_utc,
            "deployment_model": self.deployment_model,
            "frontend_expected_package": self.frontend_expected_package,
            "frontend_package_present": self.frontend_package_present,
            "frontend_readiness_claimed": self.frontend_readiness_claimed,
            "env_check_ok": self.env_check_ok,
            "generated_files": [asdict(item) for item in self.generated_files],
            "errors": list(self.errors),
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_text(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    if executable:
        tmp.chmod(0o755)
    tmp.replace(path)


def _path_symlink_errors(path: Path, *, label: str) -> list[str]:
    symlinks = symlink_components_preserving_path(path)
    if not symlinks:
        return []
    return [f"{label} contains symlink component(s): " + ", ".join(str(item) for item in symlinks)]


def _is_secret_key(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in _SECRET_KEY_MARKERS)


def _redact_value(key: str, value: str) -> str:
    if not _is_secret_key(key):
        return value
    if not value:
        return ""
    return f"<redacted:{len(value)} chars>"


def _redacted_env_payload(env_file: Path, env_check: EnvCheckReport) -> dict[str, object]:
    values, parse_issues = parse_env_file(env_file)
    return {
        "schema_version": "single_tenant_deployment_env_redacted/v1",
        "env_file": str(env_file),
        "env_check": env_check.to_payload(),
        "values": {key: _redact_value(key, values[key]) for key in sorted(values)},
        "parse_issue_count": len(parse_issues),
    }


def _repo_asset_manifest(repo_root: Path, *, generated_at_utc: str) -> dict[str, object]:
    assets: list[dict[str, object]] = []
    for relative in _REQUIRED_REPO_ASSETS:
        path = repo_root / relative
        is_symlink = path.is_symlink()
        exists = path.is_file() and not is_symlink
        assets.append(
            {
                "path": relative,
                "exists": exists,
                "is_symlink": is_symlink,
                "sha256": _sha256_file(path) if exists else None,
                "size_bytes": path.stat().st_size if exists else None,
            }
        )
    missing = [str(item["path"]) for item in assets if not item["exists"]]
    return {
        "schema_version": _REPO_ASSET_SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc,
        "repo_root": str(repo_root),
        "asset_count": len(assets),
        "missing_asset_count": len(missing),
        "missing_assets": missing,
        "assets": assets,
    }


