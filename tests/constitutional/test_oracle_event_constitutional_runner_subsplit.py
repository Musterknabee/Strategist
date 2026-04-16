from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_oracle_event_constitutional_runners_is_compatibility_surface() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_event_constitutional_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_event_review_runners import *' in helper
    assert 'from strategy_validator.cli.oracle_event_diagnostic_runners import *' in helper
    for symbol in [
        'def cmd_oracle_transition(',
        'def cmd_oracle_weekly_digest(',
        'def cmd_oracle_constitutional_digest(',
        'def cmd_oracle_diagnose(',
        'def cmd_oracle_briefing_pack(',
    ]:
        assert symbol not in helper


def test_event_review_and_diagnostic_submodules_own_split_runner_clusters() -> None:
    review = (PKG_ROOT / 'cli' / 'oracle_event_review_runners.py').read_text(encoding='utf-8')
    diagnostic = (PKG_ROOT / 'cli' / 'oracle_event_diagnostic_runners.py').read_text(encoding='utf-8')
    common = (PKG_ROOT / 'cli' / 'oracle_event_constitutional_runner_common.py').read_text(encoding='utf-8')
    for symbol in [
        'from strategy_validator.cli.oracle_event_transition_memory_runners import *',
        'from strategy_validator.cli.oracle_event_digest_constitutional_runners import *',
    ]:
        assert symbol in review
    for symbol in [
        'def cmd_oracle_diagnose(',
        'def cmd_oracle_status_pack(',
        'def cmd_oracle_incident_pack(',
        'def cmd_oracle_briefing_pack(',
        'def cmd_oracle_replay_audit(',
    ]:
        assert symbol in diagnostic
    for symbol in [
        'def _legacy_banner(',
        '_run_verify_and_append_manifest',
        '_legacy_banner_with_trust',
    ]:
        assert symbol in common
