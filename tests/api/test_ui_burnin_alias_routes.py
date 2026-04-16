from fastapi.testclient import TestClient

from strategy_validator.api.app import app

client = TestClient(app)


def test_ui_burnin_route_uses_service(monkeypatch) -> None:
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.build_ui_burnin_payload',
        lambda **_: {'schema_version': 'ui_burnin_dashboard/v1', 'metrics': {'providerPaths': []}},
    )

    for path in ('/ui/burnin', '/ui/burnin/forensic', '/ui/burnin/providers'):
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()['schema_version'] == 'ui_burnin_dashboard/v1'
