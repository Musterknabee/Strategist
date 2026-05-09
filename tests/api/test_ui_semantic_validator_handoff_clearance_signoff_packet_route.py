from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_signoff_packet_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-review-docket", "clearance-signoff-packet"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_signoff_packet_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_signoff_packet_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_signoff_packet_latest_payload" in source
    assert "signoff_status: list[str] = Query(default=[])" in source
    assert "signoff_readiness: list[str] = Query(default=[])" in source
    assert "ready_for_human_signoff_observation: bool | None = None" in source
    assert "requires_authorized_review: bool | None = None" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-signoff-packet')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-signoff-packet/latest')", 1)[0]
    assert "signoff_packet_write_authority" not in segment
    assert "signoff_record_write_authority" not in segment
    assert "operator_signoff_authority" not in segment
    assert "operator_approval_authority" not in segment
    assert "clearance_decision_authority" not in segment
