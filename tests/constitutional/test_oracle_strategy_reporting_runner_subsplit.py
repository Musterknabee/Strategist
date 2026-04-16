from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_oracle_strategy_reporting_runners_is_compatibility_surface() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_strategy_reporting_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_strategy_advisory_runners import (' in helper
    assert 'from strategy_validator.cli.oracle_strategy_domain_runners import (' in helper
    assert 'def cmd_oracle_advisory(' not in helper
    assert 'def cmd_oracle_strategic_briefing(' not in helper
    assert 'def cmd_oracle_evidence(' not in helper


def test_strategy_runner_clusters_live_in_bounded_modules() -> None:
    advisory = (PKG_ROOT / 'cli' / 'oracle_strategy_advisory_runners.py').read_text(encoding='utf-8')
    domain = (PKG_ROOT / 'cli' / 'oracle_strategy_domain_runners.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_advisory(' in advisory
    assert 'def cmd_oracle_signal_fusion(' in advisory
    assert 'def cmd_oracle_evidence(' in advisory
    assert 'def cmd_oracle_opportunity_queue(' in domain
    assert 'def cmd_oracle_strategic_briefing(' in domain
    assert 'def cmd_oracle_research_planner(' in domain
