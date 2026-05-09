from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_coverage_board_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-evidence-matrix", "clearance-coverage-board"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_coverage_board_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_coverage_board_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_coverage_board_latest_payload" in source
    assert "coverage_status: list[str] = Query(default=[])" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-coverage-board')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-coverage-board/latest')", 1)[0]
    assert "coverage_assertion_authority" not in segment
    assert "operator_approval_authority" not in segment
