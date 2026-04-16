from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / "strategy_validator"


def test_rollout_strategy_reporting_commands_module_owns_split_cluster() -> None:
    helper = (PKG_ROOT / "cli" / "oracle_strategy_reporting_commands.py").read_text(encoding="utf-8")
    assert "def register_oracle_strategy_reporting_commands(" in helper
    assert 'oracle-advisory' in helper
    assert 'oracle-opportunity-queue' in helper
    assert 'oracle-strategic-briefing' in helper
    assert 'oracle-strategic-memory-horizon' in helper
    assert 'oracle-contradiction-resolution' in helper
    assert 'oracle-strategic-campaign' in helper
    assert 'oracle-research-planner' in helper
    assert 'verify-oracle-evidence' in helper


def test_rollout_ops_registers_strategy_reporting_helper_module() -> None:
    rollout_ops = (PKG_ROOT / "cli" / "rollout_ops.py").read_text(encoding="utf-8")
    assert 'from strategy_validator.cli.oracle_strategy_reporting_commands import register_oracle_strategy_reporting_commands' in rollout_ops
    assert 'register_oracle_strategy_reporting_commands(' in rollout_ops
    assert 'oa = sub.add_parser("oracle-advisory"' not in rollout_ops
    assert 'ooq = sub.add_parser("oracle-opportunity-queue"' not in rollout_ops
    assert 'osb = sub.add_parser("oracle-strategic-briefing"' not in rollout_ops
    assert 'ocr = sub.add_parser("oracle-contradiction-resolution"' not in rollout_ops
    assert 'oe = sub.add_parser("oracle-evidence"' not in rollout_ops
