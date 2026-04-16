from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTING_PATH = ROOT / 'strategy_validator' / 'application' / 'oracle_reporting.py'
EVENT_PATH = ROOT / 'strategy_validator' / 'application' / 'oracle_event_surfaces.py'
ADVISORY_PATH = ROOT / 'strategy_validator' / 'application' / 'oracle_advisory_surfaces.py'


def test_oracle_reporting_is_now_a_compact_compatibility_shim() -> None:
    content = REPORTING_PATH.read_text(encoding='utf-8')
    line_count = len(content.splitlines())

    assert 'Compatibility reporting shim.' in content
    assert line_count < 260, f'oracle_reporting.py regressed to {line_count} lines'
    assert 'from strategy_validator.application.oracle_operational_surfaces import *' in content
    assert 'from strategy_validator.application.oracle_strategy_surfaces import *' in content
    assert 'from strategy_validator.application.oracle_advisory_surfaces import *' in content
    assert 'from strategy_validator.application.oracle_event_surfaces import *' in content


def test_bounded_event_and_advisory_surfaces_no_longer_delegate_back_to_reporting() -> None:
    event_content = EVENT_PATH.read_text(encoding='utf-8')
    advisory_content = ADVISORY_PATH.read_text(encoding='utf-8')

    assert 'oracle_reporting as _reporting' not in event_content
    assert 'oracle_reporting as _reporting' not in advisory_content
    assert 'from strategy_validator.validator.oracle_transition import (' in event_content
    assert 'from strategy_validator.validator.oracle_trust import (' in advisory_content
