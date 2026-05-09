from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_operations_board_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-coverage-board", "clearance-operations-board"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_operations_board_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_operations_board_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_operations_board_latest_payload" in source
    assert "operation_state: list[str] = Query(default=[])" in source
    assert "action_group: list[str] = Query(default=[])" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-operations-board')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-operations-board/latest')", 1)[0]
    assert "operator_approval_authority" not in segment
    assert "signoff_authority" not in segment
