from pathlib import Path


def test_oracle_pack_index_runners_own_discovery_cluster() -> None:
    text = Path('strategy_validator/cli/oracle_pack_index_runners.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_operator_pack_query(' in text
    assert 'def cmd_oracle_operator_pack_assignment(' in text


def test_oracle_pack_lifecycle_runners_own_lifecycle_cluster() -> None:
    text = Path('strategy_validator/cli/oracle_pack_lifecycle_runners.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_operator_pack_claim_lease(' in text
    assert 'def cmd_oracle_operator_pack_terminal_record_publish(' in text


def test_oracle_pack_runner_common_owns_shared_helper_wall() -> None:
    text = Path('strategy_validator/cli/oracle_pack_runner_common.py').read_text(encoding='utf-8')
    assert 'def _emit_payload(' in text
