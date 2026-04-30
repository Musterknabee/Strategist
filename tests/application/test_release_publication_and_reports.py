from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from strategy_validator.application.adjudication import build_decision_record, build_kernel_report, build_operator_governance_report
from strategy_validator.application.release_publication import publish_release_readiness_bundle
from strategy_validator.contracts.experiments import GateResult
from strategy_validator.core.enums import RuntimeMode


class _FakeReadiness:
    def __init__(self) -> None:
        self.status = 'READY'
        self.adjudication_allowed = True
        self.blockers = []
        self.config_fingerprint = 'abc123'

    def model_dump(self, mode: str = 'json') -> dict[str, object]:
        return {
            'status': self.status,
            'adjudication_allowed': self.adjudication_allowed,
            'blockers': [],
            'config_fingerprint': self.config_fingerprint,
        }


class _FakeBundle:
    def model_dump(self, mode: str = 'json') -> dict[str, object]:
        return {'scope': 'FULL', 'provider_source_policy_summary': 'stable'}


def _decision() -> SimpleNamespace:
    return SimpleNamespace(
        decided_at=datetime(2026, 4, 15, 10, 0, tzinfo=timezone.utc),
        new_state='APPROVED',
        gate_results=[GateResult(gate_name='capacity', passed=False, reason='insufficient capacity')],
        summary_notes=['note-a'],
        benchmark_report=None,
        execution_report={'impact': 'moderate'},
        runtime_mode=RuntimeMode.TEST,
        config_fingerprint='abc123',
    )


def test_kernel_and_operator_reports_are_derived_from_decision_record() -> None:
    decision = _decision()
    record = build_decision_record(experiment_id='exp-1', strategy_id='strat-1', decision=decision)
    kernel_report = build_kernel_report(experiment_id='exp-1', strategy_id='strat-1', decision=decision)
    operator_report = build_operator_governance_report(decision_record=record)

    assert kernel_report.experiment_id == 'exp-1'
    assert 'insufficient capacity' in kernel_report.gate_failures
    assert operator_report.decision_record_id == record.record_id
    assert operator_report.queue_priority >= 0
    assert operator_report.blocking_reasons == ['insufficient capacity']


def test_release_publication_bundle_writes_artifact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policy_path = tmp_path / 'policy.json'
    policy_path.write_text('{}', encoding='utf-8')
    fingerprint_path = tmp_path / 'fingerprint.json'
    fingerprint_path.write_text('{}', encoding='utf-8')
    burnin_path = tmp_path / 'burnin.jsonl'
    burnin_path.write_text(json.dumps({'round': 1, 'status': 'SUCCESS', 'symbol': 'SPY'}) + '\n', encoding='utf-8')
    publication_path = tmp_path / 'release_bundle.json'

    monkeypatch.setattr('strategy_validator.application.release_publication.get_current_readiness', lambda: _FakeReadiness())
    monkeypatch.setattr('strategy_validator.application.release_publication.build_rollout_bundle', lambda **kwargs: _FakeBundle())

    payload = publish_release_readiness_bundle(
        policy_path=policy_path,
        keyed_host_fingerprint_path=fingerprint_path,
        burnin_artifact_paths=[burnin_path],
        scope='FULL',
        publication_path=publication_path,
    )

    assert publication_path.exists()
    written = json.loads(publication_path.read_text(encoding='utf-8'))
    assert written['readiness']['status'] == 'READY'
    assert payload['release_report']['readiness_status'] == 'READY'
    assert payload['payload']['burnin_summary']['total_round_count'] == 1
