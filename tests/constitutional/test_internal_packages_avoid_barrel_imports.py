from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _scan_python_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob('*.py') if '__pycache__' not in path.parts)


def _barrel_import_violations(root: Path, forbidden_import: str) -> list[str]:
    violations: list[str] = []
    needle = f'from {forbidden_import} import'
    for path in _scan_python_files(root):
        text = path.read_text(encoding='utf-8')
        if needle in text:
            violations.append(str(path.relative_to(REPO_ROOT)))
    return violations


def test_validator_modules_do_not_depend_on_control_plane_barrel() -> None:
    violations = _barrel_import_violations(
        REPO_ROOT / 'strategy_validator' / 'validator',
        'strategy_validator.control_plane',
    )
    assert violations == []


def test_internal_application_modules_do_not_depend_on_application_barrel() -> None:
    root = REPO_ROOT / 'strategy_validator' / 'application'
    violations = [
        path for path in _barrel_import_violations(root, 'strategy_validator.application')
        if not path.endswith('strategy_validator/application/__init__.py')
    ]
    assert violations == []


def test_internal_cli_modules_do_not_depend_on_control_plane_barrels() -> None:
    root = REPO_ROOT / 'strategy_validator' / 'cli'
    control_plane_violations = _barrel_import_violations(root, 'strategy_validator.control_plane')
    application_violations = _barrel_import_violations(root, 'strategy_validator.application')
    assert control_plane_violations == []
    assert application_violations == []

