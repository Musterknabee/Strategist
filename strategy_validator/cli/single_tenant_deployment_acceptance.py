"""Single-tenant backend deployment acceptance gate.

This command produces a machine-readable go/no-go report for a backend-only
single-tenant deployment handoff.  It intentionally does not start Docker or
contact the API; it verifies the env contract, generated deployment bundle, and
repo deployment assets before an operator runs the host-level commands.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from strategy_validator.cli.deployment_env_check import (
    EnvCheckReport,
    absolute_path_preserving_symlink,
    build_single_tenant_deployment_env_check,
    symlink_components_preserving_path,
)
from strategy_validator.cli.single_tenant_deployment_bundle import (
    DeploymentBundleReport,
    check_single_tenant_deployment_bundle,
)

_SCHEMA_VERSION = "single_tenant_deployment_acceptance/v1"
_FRONTEND_PACKAGE = "ui/strategist-web"
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
_REQUIRED_BUNDLE_FILES = (
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
class AcceptanceCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DeploymentAcceptanceReport:
    schema_version: str
    ok: bool
    generated_at_utc: str
    deployment_model: str
    env_file: str
    bundle_dir: str | None
    frontend_expected_package: str
    frontend_package_present: bool
    frontend_readiness_claimed: bool
    env_check: dict[str, object]
    bundle_check: dict[str, object] | None
    checks: tuple[AcceptanceCheck, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "generated_at_utc": self.generated_at_utc,
            "deployment_model": self.deployment_model,
            "env_file": self.env_file,
            "bundle_dir": self.bundle_dir,
            "frontend_expected_package": self.frontend_expected_package,
            "frontend_package_present": self.frontend_package_present,
            "frontend_readiness_claimed": self.frontend_readiness_claimed,
            "env_check": self.env_check,
            "bundle_check": self.bundle_check,
            "checks": [asdict(check) for check in self.checks],
        }


def _check(condition: bool, name: str, pass_detail: str, fail_detail: str) -> AcceptanceCheck:
    return AcceptanceCheck(
        name=name,
        status="PASS" if condition else "FAIL",
        detail=pass_detail if condition else fail_detail,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_bundle_repo_asset_manifest(bundle_dir: Path | None) -> dict[str, dict[str, object]]:
    if bundle_dir is None:
        return {}
    manifest_path = bundle_dir / "repo-assets.manifest.json"
    if not manifest_path.exists():
        return {}
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get("schema_version") != _REPO_ASSET_SCHEMA_VERSION:
        return {}
    assets = payload.get("assets", [])
    if not isinstance(assets, list):
        return {}
    by_path: dict[str, dict[str, object]] = {}
    for item in assets:
        if isinstance(item, dict) and isinstance(item.get("path"), str):
            by_path[str(item["path"])] = item
    return by_path


def _required_repo_asset_checks(repo_root: Path, *, bundle_dir: Path | None = None) -> tuple[AcceptanceCheck, ...]:
    checks: list[AcceptanceCheck] = []
    manifest_assets = _load_bundle_repo_asset_manifest(bundle_dir)
    for relative in _REQUIRED_REPO_ASSETS:
        path = repo_root / relative
        manifest_item = manifest_assets.get(relative)
        manifest_digest = manifest_item.get("sha256") if manifest_item else None
        manifest_size = manifest_item.get("size_bytes") if manifest_item else None

        if path.is_symlink():
            checks.append(
                AcceptanceCheck(
                    name=f"repo_asset:{relative}",
                    status="FAIL",
                    detail=f"{relative} is a symlink; deployment source assets must be regular files",
                )
            )
            continue

        if path.is_file():
            if manifest_item and manifest_item.get("exists") is True and manifest_digest:
                actual_digest = _sha256_file(path)
                actual_size = path.stat().st_size
                digest_matches = actual_digest == manifest_digest
                size_matches = manifest_size == actual_size
                checks.append(
                    AcceptanceCheck(
                        name=f"repo_asset:{relative}",
                        status="PASS" if digest_matches and size_matches else "FAIL",
                        detail=(
                            f"{relative} exists and matches bundle repo-assets.manifest.json sha256={manifest_digest}"
                            if digest_matches and size_matches
                            else (
                                f"{relative} exists but differs from bundle repo-assets.manifest.json "
                                f"expected_sha256={manifest_digest} actual_sha256={actual_digest} "
                                f"expected_size={manifest_size!r} actual_size={actual_size}"
                            )
                        ),
                    )
                )
                continue

            checks.append(
                AcceptanceCheck(
                    name=f"repo_asset:{relative}",
                    status="PASS",
                    detail=f"{relative} exists in repo root; no bundle digest available for drift comparison",
                )
            )
            continue

        manifest_exists = bool(manifest_item and manifest_item.get("exists") is True and manifest_digest)
        checks.append(
            AcceptanceCheck(
                name=f"repo_asset:{relative}",
                status="PASS" if manifest_exists else "FAIL",
                detail=(
                    f"{relative} is covered by bundle repo-assets.manifest.json sha256={manifest_digest}"
                    if manifest_exists
                    else f"{relative} is missing from repo root and bundle repo-assets.manifest.json"
                ),
            )
        )
    return tuple(checks)


def _bundle_file_checks(bundle_dir: Path) -> tuple[AcceptanceCheck, ...]:
    checks: list[AcceptanceCheck] = []
    for relative in _REQUIRED_BUNDLE_FILES:
        checks.append(
            _check(
                (bundle_dir / relative).is_file() and not (bundle_dir / relative).is_symlink(),
                f"bundle_file:{relative}",
                f"{relative} exists as a regular generated deployment bundle file",
                f"{relative} is missing, non-regular, or symlinked in generated deployment bundle",
            )
        )
    return tuple(checks)


def _path_symlink_detail(path: str | Path, *, label: str) -> str | None:
    symlinks = symlink_components_preserving_path(path)
    if not symlinks:
        return None
    return f"{label} contains symlink component(s): " + ", ".join(str(item) for item in symlinks)


def _write_markdown(path: str | Path, report: DeploymentAcceptanceReport) -> None:
    target = absolute_path_preserving_symlink(path)
    detail = _path_symlink_detail(target, label="summary markdown output path")
    if detail is not None:
        raise ValueError(detail)
    target.parent.mkdir(parents=True, exist_ok=True)
    rows = "\n".join(
        f"| {check.status} | `{check.name}` | {check.detail} |" for check in report.checks
    )
    text = f"""# Strategy Validator single-tenant deployment acceptance

Schema: `{report.schema_version}`  
Status: **{'PASS' if report.ok else 'FAIL'}**  
Generated: `{report.generated_at_utc}`  
Deployment model: `{report.deployment_model}`  
Frontend readiness claimed: `{str(report.frontend_readiness_claimed).lower()}`

| Status | Check | Detail |
|---|---|---|
{rows}

## Operator sequence after PASS

1. Keep the real `deployment.env` private on the target host.
2. Run `strategy-validator-deployment-env-check deployment.env --require-valid --json`.
3. Run the generated bundle `commands/preflight.sh`.
4. Start the backend with the generated Docker Compose or systemd template.
5. Run `commands/api-smoke.sh` after the API is listening.
6. Run `commands/backup-ledger.sh` before risky changes and keep backup artifacts off-host where appropriate.

This report is backend-only and does not assert `ui/strategist-web` readiness.
"""
    target.write_text(text, encoding="utf-8")


def build_single_tenant_deployment_acceptance(
    *,
    env_file: str | Path = "deployment.env",
    bundle_dir: str | Path | None = None,
    repo_root: str | Path = ".",
) -> DeploymentAcceptanceReport:
    repo = Path(repo_root).expanduser().resolve()
    env_path = absolute_path_preserving_symlink(env_file)
    env_report: EnvCheckReport = build_single_tenant_deployment_env_check(env_path)
    bundle_report: DeploymentBundleReport | None = None
    checks: list[AcceptanceCheck] = []

    checks.append(
        _check(
            env_report.ok,
            "deployment_env_valid",
            "deployment env passes single-tenant production contract",
            "deployment env has ERROR issues; run strategy-validator-deployment-env-check",
        )
    )
    bundle_path: Path | None = None
    if bundle_dir:
        bundle_path = absolute_path_preserving_symlink(bundle_dir)

    checks.extend(_required_repo_asset_checks(repo, bundle_dir=bundle_path))

    if bundle_path is not None:
        bundle_path_symlink_detail = _path_symlink_detail(bundle_path, label="deployment bundle directory")
        if bundle_path_symlink_detail is not None:
            checks.append(
                AcceptanceCheck(
                    name="deployment_bundle_path_not_symlinked",
                    status="FAIL",
                    detail=bundle_path_symlink_detail,
                )
            )
        else:
            bundle_report = check_single_tenant_deployment_bundle(bundle_path)
            checks.append(
                _check(
                    bundle_report.ok,
                    "deployment_bundle_valid",
                    "deployment bundle manifest and generated files verify",
                    "deployment bundle is missing required files or has invalid manifest metadata",
                )
            )
            checks.extend(_bundle_file_checks(bundle_path))
    else:
        checks.append(
            _check(
                True,
                "deployment_bundle_optional",
                "bundle check skipped because no --bundle-dir was supplied",
                "bundle check skipped",
            )
        )

    frontend_present = (repo / _FRONTEND_PACKAGE / "package.json").exists()
    checks.append(
        _check(
            True,
            "backend_only_acceptance_never_claims_frontend_readiness",
            (
                "single-tenant backend acceptance leaves frontend_readiness_claimed=false; "
                + (
                    "ui/strategist-web package is absent."
                    if not frontend_present
                    else "ui/strategist-web package exists but is not certified by this gate."
                )
            ),
            "frontend readiness must not be claimed by this backend-only acceptance path",
        )
    )

    ok = all(check.status == "PASS" for check in checks)
    return DeploymentAcceptanceReport(
        schema_version=_SCHEMA_VERSION,
        ok=ok,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        deployment_model="single_tenant_backend_only",
        env_file=str(env_path),
        bundle_dir=str(bundle_path) if bundle_path else None,
        frontend_expected_package=_FRONTEND_PACKAGE,
        frontend_package_present=frontend_present,
        frontend_readiness_claimed=False,
        env_check=env_report.to_payload(),
        bundle_check=bundle_report.to_payload() if bundle_report is not None else None,
        checks=tuple(checks),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a single-tenant backend deployment go/no-go acceptance report.")
    parser.add_argument("--env-file", default="deployment.env", help="Private deployment env file to validate.")
    parser.add_argument("--bundle-dir", default="", help="Optional generated deployment bundle directory to verify.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for asset and frontend-scope checks.")
    parser.add_argument("--summary-markdown-output-path", default="", help="Optional markdown report output path.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless acceptance status is PASS.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. Plain output is JSON too for stable automation.")
    ns = parser.parse_args(argv)

    report = build_single_tenant_deployment_acceptance(
        env_file=ns.env_file,
        bundle_dir=ns.bundle_dir or None,
        repo_root=ns.repo_root,
    )
    if ns.summary_markdown_output_path:
        markdown_detail = _path_symlink_detail(ns.summary_markdown_output_path, label="summary markdown output path")
        if markdown_detail is not None:
            report = replace(
                report,
                ok=False,
                checks=report.checks
                + (
                    AcceptanceCheck(
                        name="summary_markdown_output_path_not_symlinked",
                        status="FAIL",
                        detail=markdown_detail,
                    ),
                ),
            )
        else:
            _write_markdown(ns.summary_markdown_output_path, report)
    sys.stdout.write(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n")
    return 2 if ns.require_ready and not report.ok else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
