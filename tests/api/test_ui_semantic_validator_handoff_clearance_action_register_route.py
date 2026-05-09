from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_action_register_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-operations-board", "clearance-action-register"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_action_register_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_action_register_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_action_register_latest_payload" in source
    assert "action_state: list[str] = Query(default=[])" in source
    assert "action_type: list[str] = Query(default=[])" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-action-register')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-action-register/latest')", 1)[0]
    assert "action_execution_authority" not in segment
    assert "operator_approval_authority" not in segment
    assert "signoff_authority" not in segment
