from pathlib import Path


def test_rollout_ops_imports_evidence_functions_from_bounded_module() -> None:
    source = Path('strategy_validator/validator/rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.rollout_ops_evidence import (' in source
    for name in [
        'generate_snapshot_signing_keypair',
        'build_closure_snapshot',
        'verify_closure_snapshot',
        'generate_host_fingerprint',
        'build_rollout_bundle',
        'build_daily_checklist',
        'review_runtime_evidence',
        'parse_analyze_summary',
    ]:
        assert f'    {name},' in source


def test_rollout_ops_no_longer_defines_split_evidence_functions_inline() -> None:
    source = Path('strategy_validator/validator/rollout_ops.py').read_text(encoding='utf-8')
    for name in [
        'generate_snapshot_signing_keypair',
        'build_closure_snapshot',
        'verify_closure_snapshot',
        'generate_host_fingerprint',
        'build_rollout_bundle',
        'build_daily_checklist',
        'review_runtime_evidence',
        'parse_analyze_summary',
    ]:
        assert f'def {name}(' not in source


def test_bounded_evidence_module_owns_split_functions() -> None:
    source = Path('strategy_validator/validator/rollout_ops_evidence.py').read_text(encoding='utf-8')
    for name in [
        'generate_snapshot_signing_keypair',
        'build_closure_snapshot',
        'verify_closure_snapshot',
        'generate_host_fingerprint',
        'build_rollout_bundle',
        'build_daily_checklist',
        'review_runtime_evidence',
        'parse_analyze_summary',
    ]:
        assert f'def {name}(' in source
