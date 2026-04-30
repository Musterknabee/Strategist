from pathlib import Path


def test_governance_plane_prefers_foundation_module_for_helpers() -> None:
    plane_text = Path("strategy_validator/control_plane/governance_plane.py").read_text(encoding="utf-8")
    foundations_text = Path("strategy_validator/control_plane/governance_plane_foundations.py").read_text(encoding="utf-8")

    assert "from strategy_validator.control_plane.governance_plane_foundations import (" in plane_text
    assert "def _governance_priority(" not in plane_text
    assert "def _governance_priority(" in foundations_text
    assert "def _governance_dispatch_posture(" in foundations_text


def test_pack_cli_prefers_canonical_modules() -> None:
    commands_text = Path("strategy_validator/cli/oracle_pack_read_commands.py").read_text(encoding="utf-8")
    lifecycle_text = Path("strategy_validator/cli/oracle_pack_lifecycle_commands.py").read_text(encoding="utf-8")
    execution_text = Path("strategy_validator/cli/oracle_pack_execution_commands.py").read_text(encoding="utf-8")
    runners_text = Path("strategy_validator/cli/oracle_pack_runners.py").read_text(encoding="utf-8")
    public_read_text = Path("strategy_validator/cli/oracle_pack_public_read.py").read_text(encoding="utf-8")

    assert "oracle_pack_read_dashboard_commands" in commands_text
    assert "oracle_pack_command_compat_read_dashboard" not in commands_text
    assert "oracle_pack_lifecycle_claim_commands" in lifecycle_text
    assert "oracle_pack_command_compat_lifecycle_claim" not in lifecycle_text
    assert "oracle_pack_execution_flow_commands" in execution_text
    assert "oracle_pack_command_compat_execution_flow" not in execution_text
    assert "oracle_pack_read_runners" in runners_text
    assert "oracle_pack_runner_compat_read" not in runners_text
    assert "oracle_pack_command_configs" in public_read_text
    assert "oracle_pack_compat_configs" not in public_read_text
