from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Iterable

# Architecture health is often run before hygiene and from source archives.
# Keep the report side-effect free even when callers forget PYTHONDONTWRITEBYTECODE.
sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.repository_truth_check import run_repository_truth_check
from scripts.source_health import run_source_health
from strategy_validator.cli.public_surface import (
    build_cli_public_surface_inventory,
    check_cli_public_surface_budgets,
)

PACKAGE_ROOTS = [
    'strategy_validator/application',
    'strategy_validator/api',
    'strategy_validator/cli',
    'strategy_validator/control_plane',
    'strategy_validator/contracts',
    'strategy_validator/ledger',
    'strategy_validator/projections',
    'strategy_validator/validator',
    'strategy_validator/proposers',
    'strategy_validator/feature_factory',
    'strategy_validator/tribunal',
    'strategy_validator/data_spine',
]

HOTSPOT_LINE_BUDGETS = {
    'strategy_validator/validator/oracle_briefing_pack_builders.py': 900,
    'strategy_validator/validator/oracle_briefing_sections.py': 900,
    'strategy_validator/validator/oracle_doctrine_evidence_semiannual.py': 900,
    'strategy_validator/validator/oracle_doctrine_evidence_annual.py': 900,
    'strategy_validator/validator/oracle_diagnostics_status_pack_builders.py': 900,
    'strategy_validator/application/ui_views.py': 300,
    'strategy_validator/application/ui_workboard_intelligence_policy.py': 650,
    'strategy_validator/control_plane/governance_claim_foundations.py': 500,
    'strategy_validator/control_plane/governance_plane_foundations.py': 500,
    'strategy_validator/cli/oracle_strategy_domain_runners.py': 900,
}

TRACKED_HOTSPOTS = list(HOTSPOT_LINE_BUDGETS)


def _python_files(root: Path) -> Iterable[Path]:
    if root.is_file() and root.suffix == '.py':
        yield root
        return
    if root.exists():
        yield from root.rglob('*.py')


def _application_export_count(repo_root: Path) -> int:
    exports_path = repo_root / 'strategy_validator/application/_exports.py'
    try:
        module = ast.parse(exports_path.read_text(encoding='utf-8'), filename=str(exports_path))
    except (OSError, SyntaxError):
        return -1
    for node in module.body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == '_EXPORT_MAP' for target in node.targets):
            if isinstance(node.value, ast.Dict):
                return len(node.value.keys)
    return -1


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return path.read_text(encoding='utf-8').count('\n') + 1



def _syntax_health(repo_root: Path) -> dict[str, object]:
    # Exhaustive AST parsing is side-effect free: unlike compileall, it does not
    # create __pycache__ and therefore cannot pollute release-candidate hygiene.
    report = run_source_health(repo_root=repo_root)
    payload = report.to_payload()
    payload["checked_scope"] = "high-gravity-side-effect-free-ast; run scripts/source_health.py --repo-owned for broader diagnostics"
    return payload

def build_architecture_health_report(repo_root: Path) -> dict[str, object]:
    hotspots = []
    for rel in TRACKED_HOTSPOTS:
        path = repo_root / rel
        lines = _line_count(path)
        budget = HOTSPOT_LINE_BUDGETS.get(rel)
        hotspots.append(
            {
                'path': rel,
                'lines': lines,
                'exists': path.exists(),
                'line_budget': budget,
                'over_budget': bool(budget is not None and lines > budget),
            }
        )

    package_balance = []
    for rel in PACKAGE_ROOTS:
        package_root = repo_root / rel
        files = list(_python_files(package_root))
        package_balance.append(
            {
                'package': rel,
                'files': len(files),
                'lines': sum(_line_count(path) for path in files),
            }
        )

    all_py = list((repo_root / 'strategy_validator').rglob('*.py'))
    biggest_files = sorted(
        ({'path': str(path.relative_to(repo_root)), 'lines': _line_count(path)} for path in all_py),
        key=lambda item: item['lines'],
        reverse=True,
    )[:15]

    contracts_oracle_lines = sum(
        _line_count(path)
        for path in (repo_root / 'strategy_validator/contracts').glob('oracle*.py')
    )
    syntax_health = _syntax_health(repo_root)
    repository_truth = run_repository_truth_check(repo_root=repo_root).to_payload()
    cli_inventory = build_cli_public_surface_inventory(repo_root).to_payload()
    cli_budget = check_cli_public_surface_budgets(repo_root)

    report = {
        'repo_root': str(repo_root),
        'hotspots': hotspots,
        'hotspot_budget': {
            'tracked_count': len(hotspots),
            'over_budget_count': sum(1 for item in hotspots if item.get('over_budget')),
            'over_budget_paths': [item['path'] for item in hotspots if item.get('over_budget')],
        },
        'package_balance': package_balance,
        'biggest_files': biggest_files,
        'application_public_surface_budget': {
            'export_count': _application_export_count(repo_root),
            'export_budget': 316,
            'over_budget': _application_export_count(repo_root) > 316,
            'canonical_export_map': 'strategy_validator/application/_exports.py',
        },
        'cli_public_surface': cli_inventory,
        'cli_public_surface_budget': cli_budget,
        'syntax_health': syntax_health,
        'repository_truth': repository_truth,
        'convergence_signals': {
            'application_package_present': (repo_root / 'strategy_validator/application').exists(),
            'api_routes_present': sorted(
                str(path.relative_to(repo_root))
                for path in (repo_root / 'strategy_validator/api/routes').glob('*.py')
            )
            if (repo_root / 'strategy_validator/api/routes').exists()
            else [],
            'validator_lines': sum(
                _line_count(path) for path in (repo_root / 'strategy_validator/validator').rglob('*.py')
            ),
            'control_plane_lines': sum(
                _line_count(path) for path in (repo_root / 'strategy_validator/control_plane').rglob('*.py')
            ),
            'cli_lines': sum(
                _line_count(path) for path in (repo_root / 'strategy_validator/cli').rglob('*.py')
            ),
            'contracts_oracle_lines': contracts_oracle_lines,
            'underbuilt_research_chain_lines': sum(
                _line_count(path)
                for rel in (
                    'strategy_validator/proposers',
                    'strategy_validator/tribunal',
                    'strategy_validator/feature_factory',
                    'strategy_validator/data_spine',
                )
                for path in (repo_root / rel).rglob('*.py')
            ),
        },
    }
    return report


if __name__ == '__main__':
    repo_root = REPO_ROOT
    report = build_architecture_health_report(repo_root)
    print(json.dumps(report, indent=2, sort_keys=True))
