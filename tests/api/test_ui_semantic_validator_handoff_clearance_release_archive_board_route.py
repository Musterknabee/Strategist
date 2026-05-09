from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_release_archive_board_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-release-closure-board", "clearance-release-archive-board"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_release_archive_board_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_release_archive_board_payload" in source
    assert "release_archive_status: list[str] = Query(default=[])" in source
    assert "ready_for_human_archive_observation: bool | None = None" in source
    assert "requires_release_closure_review: bool | None = None" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-release-archive-board')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-release-archive-board/latest')", 1)[0]
    assert "release_archive_write_authority" not in segment
    assert "release_closure_write_authority" not in segment
    assert "release_completion_write_authority" not in segment
    assert "release_confirmation_write_authority" not in segment
    assert "release_acknowledgment_write_authority" not in segment
    assert "release_receipt_write_authority" not in segment
    assert "custody_transfer_authority" not in segment
