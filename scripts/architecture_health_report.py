from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

HOTSPOT_FILES = [
    'strategy_validator/cli/rollout_ops.py',
    'strategy_validator/cli/oracle_queue_commands.py',
    'strategy_validator/contracts/oracle.py',
    'strategy_validator/control_plane/__init__.py',
    'strategy_validator/validator/orchestrator/__init__.py',
]
PACKAGE_ROOTS = [
    'strategy_validator/application',
    'strategy_validator/api',
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


def _python_files(root: Path) -> Iterable[Path]:
    if root.is_file() and root.suffix == '.py':
        yield root
        return
    if root.exists():
        yield from root.rglob('*.py')


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    return path.read_text(encoding='utf-8').count('\n') + 1


def build_architecture_health_report(repo_root: Path) -> dict[str, object]:
    hotspots = []
    for rel in HOTSPOT_FILES:
        path = repo_root / rel
        hotspots.append({'path': rel, 'lines': _line_count(path), 'exists': path.exists()})

    package_balance = []
    for rel in PACKAGE_ROOTS:
        root = repo_root / rel
        files = list(_python_files(root))
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
    )[:10]

    report = {
        'repo_root': str(repo_root),
        'hotspots': hotspots,
        'package_balance': package_balance,
        'biggest_files': biggest_files,
        'convergence_signals': {
            'application_package_present': (repo_root / 'strategy_validator/application').exists(),
            'api_routes_present': sorted(
                str(path.relative_to(repo_root))
                for path in (repo_root / 'strategy_validator/api/routes').glob('*.py')
            )
            if (repo_root / 'strategy_validator/api/routes').exists()
            else [],
            'contracts_oracle_lines': _line_count(repo_root / 'strategy_validator/contracts/oracle.py'),
            'control_plane_init_lines': _line_count(repo_root / 'strategy_validator/control_plane/__init__.py'),
            'validator_orchestrator_lines': _line_count(repo_root / 'strategy_validator/validator/orchestrator/__init__.py'),
        },
    }
    return report


if __name__ == '__main__':
    repo_root = Path(__file__).resolve().parents[1]
    report = build_architecture_health_report(repo_root)
    print(json.dumps(report, indent=2, sort_keys=True))
