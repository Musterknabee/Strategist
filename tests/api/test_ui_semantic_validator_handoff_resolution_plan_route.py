from __future__ import annotations
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_routes_registered():
    s=(ROOT/'strategy_validator/api/routes/ui_routes_detail_runtime.py').read_text(encoding='utf-8')
    for name in ('action-queue','escalation-board','resolution-plan','clearance-gate','clearance-dossier'):
        assert f"'/semantic-validator-handoff/{name}'" in s
        assert f"'/semantic-validator-handoff/{name}/latest'" in s
