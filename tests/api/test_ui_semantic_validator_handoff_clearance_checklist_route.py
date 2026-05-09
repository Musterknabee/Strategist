from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_checklist_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-dossier", "clearance-checklist"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_checklist_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_checklist_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_checklist_latest_payload" in source
    assert "check_state: list[str] = Query(default=[])" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-checklist')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-checklist/latest')", 1)[0]
    assert "check_acknowledgment_authority" not in segment
    assert "check_override_authority" not in segment
