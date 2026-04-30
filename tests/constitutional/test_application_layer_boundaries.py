from __future__ import annotations

from pathlib import Path

from tests.constitutional.test_boundaries import PKG_ROOT, _py_files, get_imports


def test_cli_may_import_application_but_application_may_not_import_cli() -> None:
    application_path = PKG_ROOT / 'application'
    forbidden_prefixes = ('strategy_validator.cli',)
    for path in _py_files(application_path):
        imports = get_imports(path)
        for imp in imports:
            if any(imp == prefix or imp.startswith(prefix + '.') for prefix in forbidden_prefixes):
                raise AssertionError(
                    f'Constitutional violation: {path} imports forbidden module {imp}'
                )


def test_api_prefers_application_surface_over_kernel_internals() -> None:
    api_path = PKG_ROOT / 'api'
    forbidden_prefixes = (
        'strategy_validator.validator',
        'strategy_validator.control_plane',
        'strategy_validator.projections',
        'strategy_validator.ledger.writer',
    )
    allowed_prefixes = ('strategy_validator.application',)
    for path in _py_files(api_path):
        imports = get_imports(path)
        for imp in imports:
            if any(imp == allowed or imp.startswith(allowed + '.') for allowed in allowed_prefixes):
                continue
            if any(imp == prefix or imp.startswith(prefix + '.') for prefix in forbidden_prefixes):
                raise AssertionError(
                    f'Constitutional violation: {path} imports forbidden module {imp}'
                )
