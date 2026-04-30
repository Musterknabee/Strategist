from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_ui_command_requires_token_when_configured(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.execute_ui_operator_command',
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


def test_readiness_publish_route_is_authenticated_post(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setattr(
        'strategy_validator.api.routes.readiness.publish_release_bundle_from_paths',
        lambda **_: {'ok': True, 'published': True},
    )
    client = TestClient(app)

    payload = {
        'artifact_root': str(tmp_path),
        'policy_path': str(tmp_path / 'policy.json'),
        'keyed_host_fingerprint_path': str(tmp_path / 'fingerprint.json'),
        'publication_path': str(tmp_path / 'publication'),
        'scope': 'FULL',
        'burnin_artifact_paths': [],
    }

    response = client.post('/readiness/publish-release-bundle', json=payload)
    assert response.status_code == 401

    response = client.post(
        '/readiness/publish-release-bundle',
        headers={'Authorization': 'Bearer secret-token'},
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()['published'] is True


def test_non_production_bypass_allows_mutation_routes_without_token(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'DEV')
    monkeypatch.setattr(
        'strategy_validator.api.routes.rebuild.backfill_all_registered_projections',
        lambda **_: {'ok': True, 'rebuilt': 1},
    )
    client = TestClient(app)

    response = client.post('/rebuild/projection-backfill', json={'search_root': str(tmp_path)})
    assert response.status_code == 200
    assert response.json()['rebuilt'] == 1


def test_ui_command_receipt_records_auth_principal(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={
            'Authorization': 'Bearer secret-token',
            'X-Strategy-Validator-Operator': 'operator-jp',
        },
        json={'operator_id': 'jp', 'work_item_key': 'w1', 'idempotency_key': 'auth-principal-smoke'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['authorization']['principal_id'] == 'operator-jp'
    assert payload['authorization']['principal_source'] == 'operator_header'
    assert payload['policy']['principal_id'] == 'operator-jp'


def test_mutation_auth_rejects_invalid_operator_principal_header(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={
            'Authorization': 'Bearer secret-token',
            'X-Strategy-Validator-Operator': 'operator with spaces',
        },
        json={'operator_id': 'jp', 'work_item_key': 'w1'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'INVALID_OPERATOR_PRINCIPAL'
