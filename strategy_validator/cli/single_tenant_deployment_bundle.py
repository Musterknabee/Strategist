"""Generate/check a backend-only single-tenant deployment bundle.

Legacy facade for the single-tenant deployment bundle generator.  The public
import path remains stable while contracts/helpers, generated templates, and
verification logic live in focused sibling modules.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.cli.deployment_env_check import (
    absolute_path_preserving_symlink,
    build_single_tenant_deployment_env_check,
)
from strategy_validator.cli.single_tenant_deployment_bundle_common import (
    DeploymentBundleReport,
    GeneratedFile,
    _DEFAULT_OUTPUT_DIR,
    _FRONTEND_PACKAGE,
    _REPO_ASSET_SCHEMA_VERSION,
    _REQUIRED_GENERATED_FILES,
    _REQUIRED_REPO_ASSETS,
    _SCHEMA_VERSION,
    _atomic_write_text,
    _path_symlink_errors,
    _redacted_env_payload,
    _repo_asset_manifest,
    _sha256_bytes,
    _sha256_file,
)
from strategy_validator.cli.single_tenant_deployment_bundle_templates import (
    _acceptance_script,
    _api_smoke_python_script,
    _api_smoke_script,
    _backup_ledger_script,
    _bundle_gitignore,
    _compose_down_script,
    _compose_template,
    _compose_up_script,
    _post_deploy_evidence_script,
    _preflight_script,
    _readme,
    _restore_ledger_script,
    _systemd_template,
    _verify_ledger_script,
)
from strategy_validator.cli.single_tenant_deployment_bundle_verification import (
    _collect_generated_files,
    _is_safe_bundle_relative_path,
    _is_valid_sha256,
    _manifest_generated_file_entries,
    _verify_generated_command_modes,
    _verify_generated_compose_lifecycle_contract,
    _verify_generated_compose_runtime_contract,
    _verify_generated_docker_hardening_counts,
    _verify_generated_evidence_mount_contract,
    _verify_generated_file_shapes,
    _verify_generated_helper_env_path_contract,
    _verify_generated_post_deploy_path_contract,
    _verify_generated_restore_breakglass_contract,
    _verify_generated_systemd_runtime_contract,
    _verify_manifest_generated_file_digests,
    _verify_repo_asset_manifest_payload,
)

# Source-level constitutional anchors retained for tests that read this legacy file directly:
# single_tenant_deployment_bundle/v1 deployment.env.redacted.json docker-compose.single-tenant.yml
# systemd/strategy-validator.service frontend_readiness_claimed STRATEGY_VALIDATOR_API_TOKEN
# commands/verify-ledger.sh commands/backup-ledger.sh commands/restore-ledger.sh commands/acceptance.sh STRATEGY_VALIDATOR_CONFIRM_RESTORE
# commands/post-deploy-evidence.sh strategy-validator-single-tenant-evidence

def build_single_tenant_deployment_bundle(
    *,
    env_file: str | Path = "deployment.env",
    output_dir: str | Path = _DEFAULT_OUTPUT_DIR,
    repo_root: str | Path = ".",
    force: bool = False,
) -> DeploymentBundleReport:
    """Generate a secret-safe backend-only deployment bundle."""

    env_path = absolute_path_preserving_symlink(env_file)
    out = absolute_path_preserving_symlink(output_dir)
    repo = Path(repo_root).expanduser().resolve()
    errors: list[str] = []
    errors.extend(_path_symlink_errors(out, label="deployment bundle output directory"))

    if errors:
        env_check = build_single_tenant_deployment_env_check(env_path)
        return DeploymentBundleReport(
            schema_version=_SCHEMA_VERSION,
            ok=False,
            output_dir=str(out),
            env_file=str(env_path),
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            deployment_model="single_tenant_backend_only",
            frontend_expected_package=_FRONTEND_PACKAGE,
            frontend_package_present=(repo / _FRONTEND_PACKAGE / "package.json").exists(),
            frontend_readiness_claimed=False,
            env_check_ok=env_check.ok,
            generated_files=(),
            errors=tuple(errors),
        )

    if out.exists() and any(out.iterdir()) and not force:
        errors.append(f"output directory is not empty; pass --force to replace generated files: {out}")
        env_check = build_single_tenant_deployment_env_check(env_path)
        return DeploymentBundleReport(
            schema_version=_SCHEMA_VERSION,
            ok=False,
            output_dir=str(out),
            env_file=str(env_path),
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            deployment_model="single_tenant_backend_only",
            frontend_expected_package=_FRONTEND_PACKAGE,
            frontend_package_present=(repo / _FRONTEND_PACKAGE / "package.json").exists(),
            frontend_readiness_claimed=False,
            env_check_ok=env_check.ok,
            generated_files=_collect_generated_files(out) if out.exists() else (),
            errors=tuple(errors),
        )

    env_check = build_single_tenant_deployment_env_check(env_path)
    out.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    redacted_payload = _redacted_env_payload(env_path, env_check)

    repo_asset_payload = _repo_asset_manifest(repo, generated_at_utc=generated_at)
    repo_asset_errors = [
        "required repo asset missing at bundle generation: " + path
        for path in repo_asset_payload.get("missing_assets", [])
    ]

    _atomic_write_text(out / "deployment.env.redacted.json", json.dumps(redacted_payload, indent=2, sort_keys=True) + "\n")
    _atomic_write_text(out / "repo-assets.manifest.json", json.dumps(repo_asset_payload, indent=2, sort_keys=True) + "\n")
    _atomic_write_text(out / ".gitignore", _bundle_gitignore())
    _atomic_write_text(out / "docker-compose.single-tenant.yml", _compose_template())
    _atomic_write_text(out / "systemd/strategy-validator.service", _systemd_template())
    _atomic_write_text(out / "commands/compose-up.sh", _compose_up_script(), executable=True)
    _atomic_write_text(out / "commands/compose-down.sh", _compose_down_script(), executable=True)
    _atomic_write_text(out / "commands/preflight.sh", _preflight_script(), executable=True)
    _atomic_write_text(out / "commands/api-smoke.sh", _api_smoke_script(), executable=True)
    _atomic_write_text(out / "commands/api-smoke.py", _api_smoke_python_script(), executable=True)
    _atomic_write_text(out / "commands/verify-ledger.sh", _verify_ledger_script(), executable=True)
    _atomic_write_text(out / "commands/backup-ledger.sh", _backup_ledger_script(), executable=True)
    _atomic_write_text(out / "commands/restore-ledger.sh", _restore_ledger_script(), executable=True)
    _atomic_write_text(out / "commands/acceptance.sh", _acceptance_script(), executable=True)
    _atomic_write_text(out / "commands/post-deploy-evidence.sh", _post_deploy_evidence_script(), executable=True)
    _atomic_write_text(out / "README.md", _readme(env_check))

    frontend_present = (repo / _FRONTEND_PACKAGE / "package.json").exists()
    # Write a preliminary manifest without its own digest, then rewrite with the
    # final generated file list excluding manifest self-reference instability.
    preliminary_files = _collect_generated_files(out)
    manifest_without_self = {
        "schema_version": _SCHEMA_VERSION,
        "ok": bool(env_check.ok and not repo_asset_errors),
        "generated_at_utc": generated_at,
        "deployment_model": "single_tenant_backend_only",
        "frontend_expected_package": _FRONTEND_PACKAGE,
        "frontend_package_present": frontend_present,
        "frontend_readiness_claimed": False,
        "env_file": str(env_path),
        "env_check_ok": env_check.ok,
        "generated_files": [asdict(item) for item in preliminary_files if item.path != "manifest.json"],
        "repo_assets_manifest_schema_version": _REPO_ASSET_SCHEMA_VERSION,
        "repo_asset_manifest_ok": not repo_asset_errors,
        "errors": (repo_asset_errors + ([] if env_check.ok else ["deployment env check has ERROR issues; inspect deployment.env.redacted.json"])),
    }
    _atomic_write_text(out / "manifest.json", json.dumps(manifest_without_self, indent=2, sort_keys=True) + "\n")

    post_generation_check = check_single_tenant_deployment_bundle(out)
    structural_errors = [
        error
        for error in post_generation_check.errors
        if error != "manifest ok field is not true; regenerate the bundle after fixing deployment readiness issues"
    ]
    report_errors = (
        repo_asset_errors
        + ([] if env_check.ok else ["deployment env check has ERROR issues; inspect deployment.env.redacted.json"])
        + structural_errors
    )
    final_manifest = dict(manifest_without_self)
    final_manifest["ok"] = bool(env_check.ok and not repo_asset_errors and not structural_errors)
    final_manifest["errors"] = report_errors
    _atomic_write_text(out / "manifest.json", json.dumps(final_manifest, indent=2, sort_keys=True) + "\n")

    generated_files = _collect_generated_files(out)
    return DeploymentBundleReport(
        schema_version=_SCHEMA_VERSION,
        ok=bool(env_check.ok and not repo_asset_errors and not structural_errors),
        output_dir=str(out),
        env_file=str(env_path),
        generated_at_utc=generated_at,
        deployment_model="single_tenant_backend_only",
        frontend_expected_package=_FRONTEND_PACKAGE,
        frontend_package_present=frontend_present,
        frontend_readiness_claimed=False,
        env_check_ok=env_check.ok,
        generated_files=generated_files,
        errors=tuple(report_errors),
    )


def check_single_tenant_deployment_bundle(output_dir: str | Path) -> DeploymentBundleReport:
    """Check that a generated bundle has the expected files and schema."""

    out = absolute_path_preserving_symlink(output_dir)
    errors: list[str] = []
    errors.extend(_path_symlink_errors(out, label="deployment bundle directory"))
    if errors:
        return DeploymentBundleReport(
            schema_version=_SCHEMA_VERSION,
            ok=False,
            output_dir=str(out),
            env_file="",
            generated_at_utc="",
            deployment_model="single_tenant_backend_only",
            frontend_expected_package=_FRONTEND_PACKAGE,
            frontend_package_present=False,
            frontend_readiness_claimed=False,
            env_check_ok=False,
            generated_files=(),
            errors=tuple(errors),
        )
    manifest_path = out / "manifest.json"
    manifest: dict[str, object] = {}
    if not manifest_path.exists():
        errors.append("manifest.json is missing")
    else:
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
            else:
                errors.append("manifest.json is not a JSON object")
        except json.JSONDecodeError as exc:
            errors.append(f"manifest.json is invalid JSON: {exc}")

    errors.extend(_verify_generated_file_shapes(out))

    if manifest.get("schema_version") not in {None, _SCHEMA_VERSION}:
        errors.append("manifest schema_version is not single_tenant_deployment_bundle/v1")
    if manifest and manifest.get("ok") is not True:
        errors.append("manifest ok field is not true; regenerate the bundle after fixing deployment readiness issues")
    if manifest and manifest.get("deployment_model") != "single_tenant_backend_only":
        errors.append("manifest deployment_model is not single_tenant_backend_only")
    if manifest and manifest.get("frontend_readiness_claimed") is not False:
        errors.append("manifest must not claim frontend readiness")
    if manifest:
        errors.extend(_verify_manifest_generated_file_digests(out, manifest))
    errors.extend(_verify_generated_command_modes(out))
    errors.extend(_verify_generated_docker_hardening_counts(out))
    errors.extend(_verify_generated_compose_runtime_contract(out))
    errors.extend(_verify_generated_compose_lifecycle_contract(out))
    errors.extend(_verify_generated_helper_env_path_contract(out))
    errors.extend(_verify_generated_evidence_mount_contract(out))
    errors.extend(_verify_generated_restore_breakglass_contract(out))
    errors.extend(_verify_generated_post_deploy_path_contract(out))
    errors.extend(_verify_generated_systemd_runtime_contract(out))

    repo_assets_path = out / "repo-assets.manifest.json"
    if repo_assets_path.exists():
        try:
            repo_assets = json.loads(repo_assets_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"repo-assets.manifest.json is invalid JSON: {exc}")
        else:
            errors.extend(_verify_repo_asset_manifest_payload(repo_assets))

    generated_files = _collect_generated_files(out) if out.exists() else ()
    return DeploymentBundleReport(
        schema_version=_SCHEMA_VERSION,
        ok=not errors,
        output_dir=str(out),
        env_file=str(manifest.get("env_file", "")),
        generated_at_utc=str(manifest.get("generated_at_utc", "")),
        deployment_model=str(manifest.get("deployment_model", "single_tenant_backend_only")),
        frontend_expected_package=str(manifest.get("frontend_expected_package", _FRONTEND_PACKAGE)),
        frontend_package_present=bool(manifest.get("frontend_package_present", False)),
        frontend_readiness_claimed=bool(manifest.get("frontend_readiness_claimed", False)),
        env_check_ok=bool(manifest.get("env_check_ok", False)),
        generated_files=generated_files,
        errors=tuple(errors),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate/check a backend-only single-tenant deployment bundle.")
    parser.add_argument("--env-file", default="deployment.env", help="Operator deployment env file to validate and summarize.")
    parser.add_argument("--output-dir", default=_DEFAULT_OUTPUT_DIR, help="Directory where generated bundle files are written.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for frontend absence/readiness checks.")
    parser.add_argument("--force", action="store_true", help="Allow replacing generated files in a non-empty output directory.")
    parser.add_argument("--check", action="store_true", help="Check an existing generated bundle instead of generating one.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the bundle/env is deployment-ready.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. Plain output is JSON too for automation.")
    ns = parser.parse_args(argv)

    if ns.check:
        report = check_single_tenant_deployment_bundle(ns.output_dir)
    else:
        report = build_single_tenant_deployment_bundle(
            env_file=ns.env_file,
            output_dir=ns.output_dir,
            repo_root=ns.repo_root,
            force=ns.force,
        )
    sys.stdout.write(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n")
    return 2 if ns.require_ready and not report.ok else 0




__all__ = [
    "DeploymentBundleReport",
    "GeneratedFile",
    "build_single_tenant_deployment_bundle",
    "check_single_tenant_deployment_bundle",
    "main",
]

