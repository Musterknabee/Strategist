"""Generate a backend-only single-tenant deployment bundle.

The bundle is intentionally operator-facing and secret-safe: it validates the
operator env file, emits a redacted summary, and writes reproducible deployment
helpers without copying raw secrets into the generated artifact directory.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.cli.single_tenant_deployment_bundle_common import (
    DeploymentBundleReport,
    _DEFAULT_OUTPUT_DIR,
    _REQUIRED_GENERATED_FILES,
    _REQUIRED_REPO_ASSETS,
    _SCHEMA_VERSION,
)
from strategy_validator.cli.single_tenant_deployment_bundle_template_runtime import _systemd_template
from strategy_validator.cli.single_tenant_deployment_bundle_verification_manifest import (
    _verify_repo_asset_manifest_payload,
)


def build_single_tenant_deployment_bundle(
    *,
    env_file: str | Path = "deployment.env",
    output_dir: str | Path = _DEFAULT_OUTPUT_DIR,
    repo_root: str | Path = ".",
    force: bool = False,
) -> DeploymentBundleReport:
    from strategy_validator.cli import single_tenant_deployment_bundle_ops as ops

    return ops.build_single_tenant_deployment_bundle(
        env_file=env_file,
        output_dir=output_dir,
        repo_root=repo_root,
        force=force,
    )


def check_single_tenant_deployment_bundle(output_dir: str | Path) -> DeploymentBundleReport:
    from strategy_validator.cli import single_tenant_deployment_bundle_ops as ops

    return ops.check_single_tenant_deployment_bundle(output_dir)


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


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())


__all__ = [
    "_DEFAULT_OUTPUT_DIR",
    "_REQUIRED_GENERATED_FILES",
    "_REQUIRED_REPO_ASSETS",
    "_SCHEMA_VERSION",
    "_systemd_template",
    "_verify_repo_asset_manifest_payload",
    "build_single_tenant_deployment_bundle",
    "check_single_tenant_deployment_bundle",
    "main",
]
