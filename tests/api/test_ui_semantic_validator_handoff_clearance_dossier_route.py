from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_dossier_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-gate", "clearance-dossier"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_dossier_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_dossier_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_dossier_latest_payload" in source
    assert "review_posture: list[str] = Query(default=[])" in source
    assert "clearance_decision_authority" not in source.split("@router.get('/semantic-validator-handoff/clearance-dossier')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-dossier/latest')", 1)[0]
