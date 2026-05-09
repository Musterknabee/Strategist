"""Structural verification facade for generated single-tenant deployment bundles.

Legacy import path for generated-file, manifest, runtime-envelope, and helper
script checks.  Verification responsibilities live in focused sibling modules;
this module re-exports the historical private helper names used by the CLI and
constitutional tests.
"""
from __future__ import annotations

from strategy_validator.cli.single_tenant_deployment_bundle_verification_common import (
    _is_safe_bundle_relative_path,
    _is_valid_sha256,
    _manifest_generated_file_entries,
)
from strategy_validator.cli.single_tenant_deployment_bundle_verification_generated_files import (
    _verify_generated_command_modes,
    _verify_generated_file_shapes,
)
from strategy_validator.cli.single_tenant_deployment_bundle_verification_helpers import (
    _verify_generated_evidence_mount_contract,
    _verify_generated_helper_env_path_contract,
    _verify_generated_post_deploy_path_contract,
    _verify_generated_restore_breakglass_contract,
)
from strategy_validator.cli.single_tenant_deployment_bundle_verification_manifest import (
    _collect_generated_files,
    _verify_manifest_generated_file_digests,
    _verify_repo_asset_manifest_payload,
)
from strategy_validator.cli.single_tenant_deployment_bundle_verification_runtime import (
    _verify_generated_compose_lifecycle_contract,
    _verify_generated_compose_runtime_contract,
    _verify_generated_docker_hardening_counts,
    _verify_generated_systemd_runtime_contract,
)

__all__ = [
    "_collect_generated_files",
    "_is_safe_bundle_relative_path",
    "_is_valid_sha256",
    "_manifest_generated_file_entries",
    "_verify_generated_command_modes",
    "_verify_generated_compose_lifecycle_contract",
    "_verify_generated_compose_runtime_contract",
    "_verify_generated_docker_hardening_counts",
    "_verify_generated_evidence_mount_contract",
    "_verify_generated_file_shapes",
    "_verify_generated_helper_env_path_contract",
    "_verify_generated_post_deploy_path_contract",
    "_verify_generated_restore_breakglass_contract",
    "_verify_generated_systemd_runtime_contract",
    "_verify_manifest_generated_file_digests",
    "_verify_repo_asset_manifest_payload",
]
