from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping
from pathlib import Path

COMPATIBILITY_FILE_MARKERS = ('_compat_', '_compat', 'compat_')
RUNTIME_COMMAND_SUFFIX = '_runtime_commands.py'
CLI_SURFACE_BUDGETS: Mapping[str, int] = {
    'cli_file_count': 193,
    'compatibility_file_count': 37,
    'runtime_command_file_count': 24,
}

PUBLIC_COMMAND_FILE_PATTERNS = (
    '*_commands.py',
    '*_public_*.py',
    'api.py',
    'calibration.py',
    'hygiene_check.py',
    'migrate.py',
    'ledger_ops.py',
    'research_preflight.py',
    'release_candidate.py',
    'rollout_ops.py',
)

@dataclass(frozen=True)
class CliPublicSurfaceInventory:
    schema_version: str
    cli_file_count: int
    command_file_count: int
    compatibility_file_count: int
    runtime_command_file_count: int
    compatibility_files: tuple[str, ...]
    runtime_command_files: tuple[str, ...]
    command_files: tuple[str, ...]
    summary_line: str

    def to_payload(self) -> dict[str, object]:
        payload = asdict(self)
        payload['compatibility_files'] = list(self.compatibility_files)
        payload['runtime_command_files'] = list(self.runtime_command_files)
        payload['command_files'] = list(self.command_files)
        return payload


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def build_cli_public_surface_inventory(repo_root: Path) -> CliPublicSurfaceInventory:
    cli_root = repo_root / 'strategy_validator' / 'cli'
    files = sorted(cli_root.glob('*.py')) if cli_root.exists() else []
    command_files = sorted({path for pattern in PUBLIC_COMMAND_FILE_PATTERNS for path in cli_root.glob(pattern)}) if cli_root.exists() else []
    compatibility_files = [path for path in files if any(marker in path.name for marker in COMPATIBILITY_FILE_MARKERS)]
    runtime_command_files = [path for path in files if path.name.endswith(RUNTIME_COMMAND_SUFFIX)]
    summary_line = (
        f"CLI public surface inventory: files={len(files)}, command_files={len(command_files)}, "
        f"compatibility_files={len(compatibility_files)}, runtime_command_files={len(runtime_command_files)}."
    )
    return CliPublicSurfaceInventory(
        schema_version='cli_public_surface_inventory/v1',
        cli_file_count=len(files),
        command_file_count=len(command_files),
        compatibility_file_count=len(compatibility_files),
        runtime_command_file_count=len(runtime_command_files),
        compatibility_files=tuple(_rel(path, repo_root) for path in compatibility_files),
        runtime_command_files=tuple(_rel(path, repo_root) for path in runtime_command_files),
        command_files=tuple(_rel(path, repo_root) for path in command_files),
        summary_line=summary_line,
    )


def check_cli_public_surface_budgets(repo_root: Path) -> dict[str, object]:
    """Return budget status for CLI sprawl guardrails.

    Budgets intentionally freeze current compatibility/runtime-command sprawl.
    They do not require immediate deletion, but they prevent accidental growth.
    """
    inventory = build_cli_public_surface_inventory(repo_root)
    actuals = inventory.to_payload()
    violations = []
    for metric, budget in CLI_SURFACE_BUDGETS.items():
        actual = int(actuals.get(metric, 0))
        if actual > budget:
            violations.append({
                'metric': metric,
                'actual': actual,
                'budget': budget,
                'excess': actual - budget,
            })
    return {
        'schema_version': 'cli_public_surface_budget/v1',
        'ok': not violations,
        'budgets': dict(CLI_SURFACE_BUDGETS),
        'violations': violations,
        'inventory': actuals,
    }


__all__ = [
    'CLI_SURFACE_BUDGETS',
    'CliPublicSurfaceInventory',
    'check_cli_public_surface_budgets',
    'build_cli_public_surface_inventory',
]
