from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_ui_workboard_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_workboard_payload',
        lambda **_: {'schema_version': 'ui_workboard_dashboard/v1', 'board_label': 'operator', 'stats': {'active_count': 3}},
    )
    client = TestClient(app)
    response = client.get('/ui/workboard')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_workboard_dashboard/v1'
    assert payload['stats']['active_count'] == 3


def test_ui_burnin_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_burnin_payload',
        lambda **_: {'schema_version': 'ui_burnin_dashboard/v1', 'metrics': {'providerPaths': []}},
    )
    client = TestClient(app)
    response = client.get('/ui/burnin')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_burnin_dashboard/v1'
    assert payload['metrics']['providerPaths'] == []


def test_ui_pack_detail_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_pack_detail_payload',
        lambda **_: {'schema_version': 'ui_pack_detail/v1', 'pack': {'pack_kind': 'status_pack'}},
    )
    client = TestClient(app)
    response = client.get('/ui/packs/detail')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_pack_detail/v1'
    assert payload['pack']['pack_kind'] == 'status_pack'


def test_ui_command_route_returns_receipt(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_operator_command_receipt_payload',
        lambda **_: {'schema_version': 'ui_operator_command_receipt/v1', 'accepted': True, 'action': 'claim-item'},
    )
    client = TestClient(app)
    response = client.post('/ui/commands/claim-item', json={'operator_id': 'jp', 'work_item_key': 'w1'})
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_operator_command_receipt/v1'
    assert payload['accepted'] is True
    assert payload['action'] == 'claim-item'


def test_ui_tribunal_route_is_blindness_safe(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_tribunal_payload',
        lambda **_: {
            'schema_version': 'ui_tribunal_workspace/v1',
            'blindness': {'quantitative_payloads_present': False},
            'doctrine_stats': {'active_doctrine_count': 2},
            'section_provenance': {'thesis_graph': {'projection_family': 'tribunal'}},
            'prompt_evaluations': [],
            'falsification_checks': [],
            'operator_lines': ['Validator quantitative metrics are intentionally excluded.'],
        },
    )
    client = TestClient(app)
    response = client.get('/ui/tribunal')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_tribunal_workspace/v1'
    assert payload['blindness']['quantitative_payloads_present'] is False
    serialized = str(payload).lower()
    for forbidden in ('cpcv', 'slippagebps', 'borrowcostbps', 'calibrationcurve'):
        assert forbidden not in serialized


def test_ui_evidence_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_evidence_payload',
        lambda **_: {'schema_version': 'ui_evidence_dashboard/v1', 'verification': {'trust_status': 'TRUST_RESTRICTED'}, 'registry': {'source_artifact_count': 2}, 'section_provenance': {'registry': {'projection_family': 'ui'}}},
    )
    client = TestClient(app)
    response = client.get('/ui/evidence')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_evidence_dashboard/v1'
    assert payload['verification']['trust_status'] == 'TRUST_RESTRICTED'
    assert payload['registry']['source_artifact_count'] == 2


def test_ui_runtime_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_runtime_status_payload',
        lambda **_: {'schema_version': 'ui_runtime_status/v1', 'environment': 'TEST', 'backend': {'status': 'CONFIGURED'}},
    )
    client = TestClient(app)
    response = client.get('/ui/runtime')
    assert response.status_code == 200
    payload = response.json()
    assert payload['schema_version'] == 'ui_runtime_status/v1'
    assert payload['environment'] == 'TEST'
    assert payload['backend']['status'] == 'CONFIGURED'


def test_ui_runtime_route_honors_role_query(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_runtime_status_payload',
        lambda **kwargs: {'schema_version': 'ui_runtime_status/v1', 'persona': {'active_role': kwargs.get('role', 'operator')}, 'policy': {'allowed_domains': ['tribunal'], 'allowed_actions': []}},
    )
    client = TestClient(app)
    response = client.get('/ui/runtime?role=tribunal')
    assert response.status_code == 200
    payload = response.json()
    assert payload['persona']['active_role'] == 'tribunal'
    assert payload['policy']['allowed_domains'] == ['tribunal']
