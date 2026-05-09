"""Generated file template compatibility facade for the single-tenant deployment bundle."""
from __future__ import annotations

from strategy_validator.cli.single_tenant_deployment_bundle_template_acceptance import (
    _acceptance_script,
    _post_deploy_evidence_script,
)
from strategy_validator.cli.single_tenant_deployment_bundle_template_commands import (
    _api_smoke_python_script,
    _api_smoke_script,
    _backup_ledger_script,
    _compose_down_script,
    _compose_up_script,
    _preflight_script,
    _restore_ledger_script,
    _verify_ledger_script,
)
from strategy_validator.cli.single_tenant_deployment_bundle_template_readme import _readme
from strategy_validator.cli.single_tenant_deployment_bundle_template_runtime import (
    _bundle_gitignore,
    _compose_template,
    _systemd_template,
)

__all__ = (
    "_acceptance_script",
    "_api_smoke_python_script",
    "_api_smoke_script",
    "_backup_ledger_script",
    "_bundle_gitignore",
    "_compose_down_script",
    "_compose_template",
    "_compose_up_script",
    "_post_deploy_evidence_script",
    "_preflight_script",
    "_readme",
    "_restore_ledger_script",
    "_systemd_template",
    "_verify_ledger_script",
)
