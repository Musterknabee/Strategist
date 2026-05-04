from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_attestation_ops import (
    build_operator_attestation,
    verify_research_os_closure_manifest,
    write_operator_attestation,
    write_research_os_closure_verification,
)
from strategy_validator.application.research_os_briefing_ops import (
    build_research_os_briefing_pack,
    build_ui_research_os_briefing_latest_payload,
    write_research_os_briefing_pack,
)
from strategy_validator.application.research_os_closure_ops import (
    build_research_os_closure_manifest,
    write_research_os_closure_manifest,
)


def _seed_verified_closure(art: Path) -> None:
    p = art / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json"
    p.parent.mkdir(parents=True)
    p.write_text(json.dumps({"schema_version": "provider_paper_loop_manifest/v1", "ok": True}, sort_keys=True), encoding="utf-8")
    closure = build_research_os_closure_manifest(closure_id="briefing-closure", artifact_root=art)
    cpath = write_research_os_closure_manifest(closure, artifact_root=art, overwrite=True)
    verification = verify_research_os_closure_manifest(verification_id="briefing-verify", manifest_path=cpath, artifact_root=art)
    write_research_os_closure_verification(verification, artifact_root=art, overwrite=True)
    attestation = build_operator_attestation(
        attestation_id="briefing-attestation",
        operator_id="local-operator",
        decision="ACCEPTED_WITH_RESTRICTIONS",
        rationale="paper-only evidence acknowledged",
        verification=verification,
        artifact_root=art,
    )
    write_operator_attestation(attestation, artifact_root=art, overwrite=True)


def test_research_os_briefing_pack_builds_from_attested_closure(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))
    _seed_verified_closure(art)

    pack = build_research_os_briefing_pack(briefing_id="briefing-demo", artifact_root=art)
    path = write_research_os_briefing_pack(pack, artifact_root=art, overwrite=True)
    payload = build_ui_research_os_briefing_latest_payload(repo_root=tmp_path)

    assert path.is_file()
    assert pack.schema_version == "research_os_briefing_pack/v1"
    assert pack.briefing_sha256
    assert pack.read_plane_only is True
    assert pack.no_live_trading is True
    assert pack.no_broker_orders is True
    assert any(s.section_id == "closure" for s in pack.sections)
    assert any(s.section_id == "operator_attestation" for s in pack.sections)
    assert payload["schema_version"] == "ui_research_os_briefing/v1"
    assert payload["status"] == "PRESENT"
    assert payload["no_order_controls"] is True
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(payload)


def test_research_os_briefing_empty_root_is_blocked_or_empty(monkeypatch, tmp_path: Path) -> None:
    art = tmp_path / "artifacts"
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(art))

    pack = build_research_os_briefing_pack(briefing_id="empty-briefing", artifact_root=art)

    assert pack.status.value in {"BLOCKED", "EMPTY"}
    assert pack.trust_banner.value == "UNTRUSTED"
    assert any(a.action_id for a in pack.action_items)
    assert pack.no_profitability_claim is True
