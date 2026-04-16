from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_ui_command_requires_token_when_configured(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_operator_command_receipt_payload',
        lambda **_: {'schema_version': 'ui_operator_command_receipt/v1', 'accepted': True, 'action': 'claim-item'},
    )
    client = TestClient(app)

    unauthorized = client.post('/ui/commands/claim-item', json={'operator_id': 'jp', 'work_item_key': 'w1'})
    assert unauthorized.status_code == 401

    authorized = client.post(
        '/ui/commands/claim-item',
        headers={'Authorization': 'Bearer secret-token'},
        json={'operator_id': 'jp', 'work_item_key': 'w1'},
    )
    assert authorized.status_code == 200
    assert authorized.json()['accepted'] is True


def test_rebuild_route_is_authenticated_post(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setattr(
        'strategy_validator.api.routes.rebuild.backfill_all_registered_projections',
        lambda **_: {'ok': True, 'rebuilt': 3},
    )
    client = TestClient(app)

    response = client.post('/rebuild/projection-backfill', json={'search_root': str(tmp_path)})
    assert response.status_code == 401

    response = client.post(
        '/rebuild/projection-backfill',
        headers={'X-Strategy-Validator-Token': 'secret-token'},
        json={'search_root': str(tmp_path)},
    )
    assert response.status_code == 200
    assert response.json()['rebuilt'] == 3
