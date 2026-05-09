from __future__ import annotations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_clearance_evidence_matrix_routes_registered() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    for name in ("clearance-checklist", "clearance-evidence-matrix"):
        assert f"'/semantic-validator-handoff/{name}'" in source
        assert f"'/semantic-validator-handoff/{name}/latest'" in source


def test_clearance_evidence_matrix_route_uses_read_plane_builder() -> None:
    source = (ROOT / "strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8")
    assert "build_ui_semantic_validator_handoff_clearance_evidence_matrix_payload" in source
    assert "build_ui_semantic_validator_handoff_clearance_evidence_matrix_latest_payload" in source
    assert "evidence_lane: list[str] = Query(default=[])" in source
    assert "evidence_state: list[str] = Query(default=[])" in source
    segment = source.split("@router.get('/semantic-validator-handoff/clearance-evidence-matrix')", 1)[1].split("@router.get('/semantic-validator-handoff/clearance-evidence-matrix/latest')", 1)[0]
    assert "evidence_attestation_authority" not in segment
    assert "evidence_override_authority" not in segment
