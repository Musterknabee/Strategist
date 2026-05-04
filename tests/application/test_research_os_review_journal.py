from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_review_journal_ops import build_and_write_research_os_review_journal, build_research_os_review_journal


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = dict(payload)
    import hashlib
    body["manifest_sha256"] = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    path.write_text(json.dumps(body), encoding="utf-8")


def test_review_journal_empty_root_degrades(tmp_path: Path) -> None:
    journal = build_research_os_review_journal(journal_id="empty", artifact_root=tmp_path)
    assert journal.status.value == "EMPTY"
    assert journal.entry_count == 0
    assert journal.no_live_trading is True


def test_review_journal_indexes_policy_and_handoff_sources(tmp_path: Path) -> None:
    _write(tmp_path / "research_os_policy_gate/latest/research_os_policy_gate_report.json", {"schema_version": "x", "gate_id": "g1", "status": "WARN", "decision": "WARN", "trust_banner": "TRUST_RESTRICTED", "warnings": ["W"]})
    _write(tmp_path / "research_os_handoff_signoff/latest/research_os_handoff_reviewer_signoff.json", {"schema_version": "x", "signoff_id": "s1", "status": "STALE", "decision": "ACCEPTED_WITH_RESTRICTIONS", "trust_banner": "TRUST_RESTRICTED"})
    journal, path = build_and_write_research_os_review_journal(journal_id="demo", artifact_root=tmp_path, overwrite=True)
    assert path.exists()
    assert journal.entry_count == 2
    assert journal.status.value == "RESTRICTED"
    assert journal.manifest_sha256
    assert "POLICY_GATE" in journal.source_counts
