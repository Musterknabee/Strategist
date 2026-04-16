from __future__ import annotations

from tests.constitutional.test_boundaries import PKG_ROOT, _py_files, get_imports


def test_projection_modules_do_not_import_cli() -> None:
    projections_path = PKG_ROOT / 'projections'
    forbidden_prefixes = ('strategy_validator.cli',)
    for path in _py_files(projections_path):
        imports = get_imports(path)
        for imp in imports:
            if any(imp == prefix or imp.startswith(prefix + '.') for prefix in forbidden_prefixes):
                raise AssertionError(
                    f'Constitutional violation: {path} imports forbidden module {imp}'
                )
