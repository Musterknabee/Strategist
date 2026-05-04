from __future__ import annotations

from pathlib import Path


def test_strategic_dead_zone_quarantine_names_deferred_surfaces() -> None:
    text = Path("docs/architecture/STRATEGIC_DEAD_ZONE_QUARANTINE.md").read_text(encoding="utf-8")
    for phrase in ("Frontend operator UI", "Workflow engine integration", "Multi-tenant operation", "Oracle/advisory expansion"):
        assert phrase in text
