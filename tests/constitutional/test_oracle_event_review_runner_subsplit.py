from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_oracle_event_review_runners_is_compatibility_surface() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_event_review_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_event_transition_memory_runners import *' in helper
    assert 'from strategy_validator.cli.oracle_event_digest_constitutional_runners import *' in helper
    for symbol in [
        'def cmd_oracle_transition(',
        'def cmd_oracle_memory_review(',
        'def cmd_oracle_weekly_digest(',
        'def cmd_oracle_constitutional_digest(',
        'def cmd_oracle_explain(',
    ]:
        assert symbol not in helper


def test_transition_memory_and_digest_submodules_own_split_runner_clusters() -> None:
    transition = (PKG_ROOT / 'cli' / 'oracle_event_transition_memory_runners.py').read_text(encoding='utf-8')
    digest = (PKG_ROOT / 'cli' / 'oracle_event_digest_constitutional_runners.py').read_text(encoding='utf-8')
    for symbol in [
        'def cmd_oracle_transition(',
        'def cmd_oracle_memory_append(',
        'def cmd_oracle_memory_review(',
        'def cmd_oracle_review_lane_append(',
    ]:
        assert symbol in transition
    for symbol in [
        'def cmd_oracle_weekly_digest(',
        'def cmd_oracle_doctrine_drift(',
        'def cmd_oracle_constitutional_digest(',
        'def cmd_oracle_doctrine_lineage_verify(',
        'def cmd_oracle_constitutional_gate(',
        'def cmd_oracle_explain(',
    ]:
        assert symbol in digest
