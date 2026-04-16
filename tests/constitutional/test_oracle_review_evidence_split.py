from pathlib import Path


def test_oracle_review_engine_imports_evidence_functions_from_bounded_module() -> None:
    source = Path('strategy_validator/validator/oracle_review_engine.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_review_evidence import (' in source
    assert 'def build_oracle_transition_evidence_bundle(' not in source
    assert 'def verify_oracle_transition_evidence_bundle(' not in source
    assert 'def append_oracle_transition_to_lane(' not in source
    assert 'def build_oracle_memory_review_evidence_bundle(' not in source
    assert 'def verify_oracle_memory_review_evidence_bundle(' not in source
    assert 'def append_oracle_memory_review_to_lane(' not in source
    assert 'def build_oracle_weekly_digest_evidence_bundle(' not in source
    assert 'def verify_oracle_weekly_digest_evidence_bundle(' not in source


def test_oracle_review_evidence_module_owns_moved_definitions() -> None:
    source = Path('strategy_validator/validator/oracle_review_evidence.py').read_text(encoding='utf-8')
    for name in [
        'build_oracle_transition_evidence_bundle',
        'verify_oracle_transition_evidence_bundle',
        'append_oracle_transition_to_lane',
        'build_oracle_memory_review_evidence_bundle',
        'verify_oracle_memory_review_evidence_bundle',
        'append_oracle_memory_review_to_lane',
        'build_oracle_weekly_digest_evidence_bundle',
        'verify_oracle_weekly_digest_evidence_bundle',
    ]:
        assert f'def {name}(' in source
