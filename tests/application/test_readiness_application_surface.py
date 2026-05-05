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
    monkeypatch.setattr(
        'strategy_validator.application.readiness.build_provider_research_spine_addon',
        lambda env, repo_root: {"summary": {"sample_manifest_present": True, "pending_or_stub_count": 0, "non_ok_checked_count": 0}},
    )
    monkeypatch.setattr(
        'strategy_validator.application.readiness.latest_replay_verification_summary',
        lambda repo_root=None: {"status": "OK", "missing_artifact_count": 0, "digest_mismatch_count": 0},
    )
    monkeypatch.setattr(
        'strategy_validator.application.readiness._frontend_readiness_status',
        lambda repo_root=None: ("OPTIONAL_NOT_CONFIGURED", False),
    )
    payload = get_readiness_health_payload()
    assert payload['surface'] == 'readiness'
    assert payload['ok'] is True
    assert payload['status'] == 'READY'
    assert payload['canonical_status'] == 'OK'
    assert payload['provider_readiness_status'] == 'OK'
    assert payload['replay_readiness_status'] == 'OK'
    assert payload['frontend_readiness_status'] == 'OPTIONAL_NOT_CONFIGURED'
    assert payload['mutation_safety']['authorization_mode'] == 'TOKEN_PROTECTED'
    spine = payload.get('provider_research_spine')
    assert isinstance(spine, dict)
    assert 'summary' in spine
