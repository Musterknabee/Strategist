from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_verification_board_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-resolution-plan", "clearance-verification-board"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_verification_board_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_verification_board_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_verification_board_latest_payload" in source
    assert "verification_status: list[str] = Query(default=[])" in source
    assert "verification_result: list[str] = Query(default=[])" in source
    assert "verification_passed: bool | None = None" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-verification-board')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-verification-board/latest')", 1)[0]
    assert "verification_write_authority" not in segment
    assert "completion_assertion_authority" not in segment
    assert "operator_approval_authority" not in segment
    assert "signoff_authority" not in segment
