import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FACADE = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle.py"
COMMON = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_common.py"
TEMPLATES = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_templates.py"
TEMPLATE_ACCEPTANCE = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_template_acceptance.py"
TEMPLATE_COMMANDS = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_template_commands.py"
TEMPLATE_README = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_template_readme.py"
TEMPLATE_RUNTIME = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_template_runtime.py"
VERIFICATION = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_verification.py"
VERIFICATION_GENERATED = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_verification_generated_files.py"
VERIFICATION_HELPERS = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_verification_helpers.py"
VERIFICATION_MANIFEST = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_verification_manifest.py"
VERIFICATION_RUNTIME = ROOT / "strategy_validator/cli/single_tenant_deployment_bundle_verification_runtime.py"


def _module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _function_names(path: Path) -> set[str]:
    return {node.name for node in _module(path).body if isinstance(node, ast.FunctionDef)}


def _class_names(path: Path) -> set[str]:
    return {node.name for node in _module(path).body if isinstance(node, ast.ClassDef)}


def test_single_tenant_deployment_bundle_facade_remains_small_and_public():
    assert FACADE.read_text(encoding="utf-8").count("\n") + 1 < 380
    assert _function_names(FACADE) == {
        "build_single_tenant_deployment_bundle",
        "check_single_tenant_deployment_bundle",
        "main",
    }
    assert _class_names(FACADE) == set()


def test_single_tenant_deployment_bundle_common_owns_contracts_and_secret_helpers():
    assert {"GeneratedFile", "DeploymentBundleReport"}.issubset(_class_names(COMMON))
    assert {
        "_sha256_file",
        "_atomic_write_text",
        "_redacted_env_payload",
        "_repo_asset_manifest",
    }.issubset(_function_names(COMMON))


def test_single_tenant_deployment_bundle_templates_facade_remains_small():
    assert TEMPLATES.read_text(encoding="utf-8").count("\n") + 1 < 80
    assert _function_names(TEMPLATES) == set()


def test_single_tenant_deployment_bundle_runtime_templates_own_service_content():
    assert {
        "_compose_template",
        "_systemd_template",
        "_bundle_gitignore",
    }.issubset(_function_names(TEMPLATE_RUNTIME))


def test_single_tenant_deployment_bundle_command_templates_own_command_helpers():
    assert {
        "_compose_up_script",
        "_api_smoke_script",
        "_restore_ledger_script",
        "_verify_ledger_script",
        "_backup_ledger_script",
    }.issubset(_function_names(TEMPLATE_COMMANDS))


def test_single_tenant_deployment_bundle_acceptance_templates_own_gate_helpers():
    assert {"_acceptance_script", "_post_deploy_evidence_script"}.issubset(
        _function_names(TEMPLATE_ACCEPTANCE)
    )


def test_single_tenant_deployment_bundle_readme_template_owns_readme_only():
    assert _function_names(TEMPLATE_README) == {"_readme"}


def test_single_tenant_deployment_bundle_verification_facade_remains_small():
    assert VERIFICATION.read_text(encoding="utf-8").count("\n") + 1 < 80
    assert _function_names(VERIFICATION) == set()


def test_single_tenant_deployment_bundle_verification_manifest_owns_manifest_checks():
    assert {
        "_verify_manifest_generated_file_digests",
        "_verify_repo_asset_manifest_payload",
        "_collect_generated_files",
    }.issubset(_function_names(VERIFICATION_MANIFEST))


def test_single_tenant_deployment_bundle_verification_generated_files_owns_shape_checks():
    assert {
        "_verify_generated_file_shapes",
        "_verify_generated_command_modes",
    }.issubset(_function_names(VERIFICATION_GENERATED))


def test_single_tenant_deployment_bundle_verification_runtime_owns_runtime_contracts():
    assert {
        "_verify_generated_docker_hardening_counts",
        "_verify_generated_compose_runtime_contract",
        "_verify_generated_compose_lifecycle_contract",
        "_verify_generated_systemd_runtime_contract",
    }.issubset(_function_names(VERIFICATION_RUNTIME))


def test_single_tenant_deployment_bundle_verification_helpers_own_helper_contracts():
    assert {
        "_verify_generated_helper_env_path_contract",
        "_verify_generated_evidence_mount_contract",
        "_verify_generated_restore_breakglass_contract",
        "_verify_generated_post_deploy_path_contract",
    }.issubset(_function_names(VERIFICATION_HELPERS))


def test_legacy_single_tenant_deployment_bundle_imports_remain_stable():
    from strategy_validator.cli import single_tenant_deployment_bundle as bundle

    assert bundle._SCHEMA_VERSION == "single_tenant_deployment_bundle/v1"
    assert "deployment.env.redacted.json" in bundle._REQUIRED_GENERATED_FILES
    assert "Dockerfile" in bundle._REQUIRED_REPO_ASSETS
    assert callable(bundle._systemd_template)
    assert callable(bundle._verify_repo_asset_manifest_payload)
