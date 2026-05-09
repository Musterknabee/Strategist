from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_release_packet_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-release-readiness-board", "clearance-release-packet"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_release_packet_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_release_packet_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_release_packet_latest_payload" in source
    assert "release_packet_status: list[str] = Query(default=[])" in source
    assert "release_packet_readiness: list[str] = Query(default=[])" in source
    assert "ready_for_human_release_observation: bool | None = None" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-release-packet')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-release-packet/latest')", 1)[0]
    assert "release_packet_write_authority" not in segment
    assert "release_record_write_authority" not in segment
    assert "handoff_release_authority" not in segment
    assert "operator_approval_authority" not in segment
