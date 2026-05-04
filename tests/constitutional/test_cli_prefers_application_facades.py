from pathlib import Path


def test_pack_command_groups_use_public_pack_surfaces() -> None:
    commands_text = Path('strategy_validator/cli/oracle_pack_commands.py').read_text(encoding='utf-8')
    compat_text = Path('strategy_validator/cli/oracle_pack_runners.py').read_text(encoding='utf-8')
    lifecycle_text = Path('strategy_validator/cli/oracle_pack_lifecycle_commands.py').read_text(encoding='utf-8')

    assert 'strategy_validator.cli.oracle_pack_public_read' in commands_text
    assert 'strategy_validator.cli.oracle_pack_public_lifecycle' in commands_text
    assert 'strategy_validator.cli.oracle_pack_public_execution' in commands_text
    assert 'strategy_validator.cli.oracle_pack_read_runners' in compat_text
    assert 'strategy_validator.cli.oracle_pack_lifecycle_runners' in compat_text
    assert 'strategy_validator.cli.oracle_pack_execution_runners' in compat_text
    assert 'strategy_validator.cli.oracle_pack_lifecycle_claim_commands' in lifecycle_text
    assert 'strategy_validator.cli.oracle_pack_lifecycle_governance_commands' in lifecycle_text
