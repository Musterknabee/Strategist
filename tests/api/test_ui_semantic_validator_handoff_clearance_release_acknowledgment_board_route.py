from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_release_acknowledgment_board_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-release-receipt-board", "clearance-release-acknowledgment-board"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_release_acknowledgment_board_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_release_acknowledgment_board_payload" in source
    assert "release_acknowledgment_status: list[str] = Query(default=[])" in source
    assert "ready_for_human_acknowledgment_observation: bool | None = None" in source
    assert "requires_release_receipt_review: bool | None = None" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-release-acknowledgment-board/latest')", 1)[0]
    assert "release_acknowledgment_write_authority" not in segment
    assert "release_receipt_write_authority" not in segment
    assert "custody_receipt_record_authority" not in segment
    assert "release_custody_write_authority" not in segment
    assert "custody_transfer_authority" not in segment
