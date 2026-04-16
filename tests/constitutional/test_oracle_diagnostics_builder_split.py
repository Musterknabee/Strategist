from pathlib import Path


def test_oracle_diagnostics_imports_builders_from_dedicated_module() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.validator.oracle_diagnostics_builders import (' in source
    assert 'build_oracle_operator_diagnostic_from_report' in source
    assert 'build_oracle_status_pack' in source
    assert 'build_oracle_incident_pack' in source
    assert 'def build_oracle_operator_diagnostic_from_report(' not in source
    assert 'def build_oracle_operator_diagnostic_from_checkpoint(' not in source
    assert 'def _build_oracle_status_pack_impl(' not in source
    assert 'def _build_oracle_incident_pack_impl(' not in source
    assert 'def build_oracle_status_pack(' not in source
    assert 'def build_oracle_incident_pack(' not in source
    assert 'def materialize_oracle_status_pack(' not in source
    assert 'def materialize_oracle_incident_pack(' not in source


def test_oracle_diagnostics_builder_module_owns_moved_definitions() -> None:
    source = Path('strategy_validator/validator/oracle_diagnostics_builders.py').read_text(encoding='utf-8')
    assert 'def build_oracle_operator_diagnostic_from_report(' in source
    assert 'def build_oracle_operator_diagnostic_from_checkpoint(' in source
    assert 'def _build_oracle_status_pack_impl(' in source
    assert 'def _build_oracle_incident_pack_impl(' in source
    assert 'def build_oracle_status_pack(' in source
    assert 'def build_oracle_incident_pack(' in source
    assert 'def materialize_oracle_status_pack(' in source
    assert 'def materialize_oracle_incident_pack(' in source
