from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_single_tenant_api_smoke_covers_health_facade_and_mutation_auth_boundary():
    text=(ROOT/"strategy_validator/cli/single_tenant_api_smoke.py").read_text(); ci=(ROOT/".github/workflows/ci.yml").read_text()
    for item in [
        "single_tenant_api_http_smoke/v1",
        "/healthz",
        "/readyz",
        "/ui/facade",
        "unauthenticated_ui_command_rejected",
        "authenticated_ui_command_accepted",
    ]:
        assert item in text
    assert "python3 scripts/single_tenant_api_smoke.py" in ci
