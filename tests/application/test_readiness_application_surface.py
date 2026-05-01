from __future__ import annotations

from strategy_validator.application.readiness import get_readiness_health_payload


class _FakeMutationSafety:
    def model_dump(self, mode: str = 'json'):
        return {'authorization_mode': 'TOKEN_PROTECTED'}


class _FakeReadiness:
    status = 'READY'
    adjudication_allowed = True
    blockers = []
    warnings = []
    mutation_safety = _FakeMutationSafety()


def test_readiness_payload_is_transport_neutral(monkeypatch) -> None:
    monkeypatch.setattr('strategy_validator.application.readiness.get_current_readiness', lambda: _FakeReadiness())
    payload = get_readiness_health_payload()
    assert payload['surface'] == 'readiness'
    assert payload['ok'] is True
    assert payload['status'] == 'READY'
    assert payload['mutation_safety']['authorization_mode'] == 'TOKEN_PROTECTED'
    spine = payload.get('provider_research_spine')
    assert isinstance(spine, dict)
    assert spine.get('schema_version') == 'provider_research_spine_addon/v1'
    assert 'summary' in spine
