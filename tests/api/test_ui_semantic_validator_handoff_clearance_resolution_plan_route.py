from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_resolution_plan_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-action-register", "clearance-resolution-plan"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_resolution_plan_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_resolution_plan_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_resolution_plan_latest_payload" in source
    assert "phase: list[str] = Query(default=[])" in source
    assert "step_state: list[str] = Query(default=[])" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-resolution-plan')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-resolution-plan/latest')", 1)[0]
    assert "repair_execution_authority" not in segment
    assert "operator_approval_authority" not in segment
    assert "signoff_authority" not in segment
