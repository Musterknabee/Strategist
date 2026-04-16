from __future__ import annotations

from pathlib import Path


def test_queue_cli_uses_application_facades() -> None:
    text = Path('strategy_validator/cli/oracle_queue_commands.py').read_text(encoding='utf-8')
    assert 'strategy_validator.application.operator_queue_commands' in text
    assert 'strategy_validator.application.governance_surface' in text


def test_pack_cli_uses_application_facades() -> None:
    commands_text = Path('strategy_validator/cli/oracle_pack_commands.py').read_text(encoding='utf-8')
    compat_text = Path('strategy_validator/cli/oracle_pack_runners.py').read_text(encoding='utf-8')
    common_text = Path('strategy_validator/cli/oracle_pack_runner_common.py').read_text(encoding='utf-8')
    index_text = Path('strategy_validator/cli/oracle_pack_index_runners.py').read_text(encoding='utf-8')
    lifecycle_text = Path('strategy_validator/cli/oracle_pack_lifecycle_runners.py').read_text(encoding='utf-8')
    assert 'strategy_validator.cli.oracle_pack_runners' in commands_text
    assert 'strategy_validator.cli.oracle_pack_index_runners' in compat_text
    assert 'strategy_validator.cli.oracle_pack_lifecycle_runners' in compat_text
    assert 'strategy_validator.application.operator_pack_queries' in common_text
    assert 'strategy_validator.application.operator_pack_assembly' in common_text
    assert 'strategy_validator.cli.oracle_pack_runner_common' in index_text
    assert 'strategy_validator.cli.oracle_pack_runner_common' in lifecycle_text
