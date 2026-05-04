"""Research OS briefing pack builder.

Builds a daily/read-plane operator briefing from closure, attestation, provider,
paper, memory, thesis, and shadow-book evidence artifacts. This module is deliberately
read-only and offline: no network, no broker orders, no ledger mutation.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_attestation_ops import (
    research_os_operator_attestation_latest_path,
    research_os_verification_latest_path,
)
from strategy_validator.application.research_os_paths import (
    artifact_root_directory,
    paper_broker_status_artifact_path,
    provider_historical_snapshot_run_path,
    provider_paper_loop_manifest_path,
    research_os_runtime_manifest_path,
)
from strategy_validator.contracts.research_os_briefing import (
    ResearchOsBriefingActionItem,
    ResearchOsBriefingPack,
    ResearchOsBriefingSection,
    ResearchOsBriefingSeverity,
    ResearchOsBriefingStatus,
)
from strategy_validator.contracts.research_os_closure import ResearchOsTrustBanner
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_SCHEMA = "ui_research_os_briefing/v1"

_SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_API_SECRET",
    "ALPACA_SECRET_KEY",
    "POLYGON_API_KEY",
    "TIINGO_API_KEY",
    "TWELVE_DATA_API_KEY",
    "SECRET_KEY",
    "PRIVATE_KEY",
    "BEARER ",
)


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_os_briefing_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_briefings").resolve()


def research_os_briefing_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_briefing_root(repo_root, artifact_root) / "latest" / "research_os_briefing_pack.json").resolve()


def _research_os_closure_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_closure" / "latest" / "research_os_closure_manifest.json").resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _as_list(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw if x is not None]
    if raw in (None, ""):
        return []
    return [str(raw)]


def _status_from(raw: dict[str, Any] | None, *, default: str = "NOT_PRESENT") -> str:
    if raw is None:
        return default
    for key in ("status", "policy_status", "provider_status", "decision", "verification_status"):
        val = raw.get(key)
        if val not in (None, ""):
            return str(val)
    if isinstance(raw.get("ok"), bool):
        return "OK" if raw.get("ok") else "NOT_OK"
    return "PRESENT"


def _digest_from(raw: dict[str, Any] | None, path: Path) -> str | None:
    if raw is not None:
        for key in ("briefing_sha256", "attestation_sha256", "result_sha256", "manifest_sha256", "evidence_sha256"):
            val = raw.get(key)
            if isinstance(val, str) and val:
                return val
        digests = raw.get("digests")
        if isinstance(digests, dict):
            for key in ("evidence_spine_sha256", "manifest_sha256", "full_manifest_sha256"):
                val = digests.get(key)
                if isinstance(val, str) and val:
                    return val
    return _sha256_file(path) if path.is_file() else None


def _secret_warnings(raw: dict[str, Any] | None, section_id: str) -> list[str]:
    if raw is None:
        return []
    body = json.dumps(raw, sort_keys=True)
    hits = [marker for marker in _SECRET_MARKERS if marker in body]
    return [f"{section_id}:SECRET_MARKER_PRESENT:{marker}" for marker in hits]


def _section(section_id: str, title: str, path: Path, *, required: bool = False, field_keys: tuple[str, ...] = ()) -> ResearchOsBriefingSection:
    raw = _read_json(path) if path.is_file() else None
    warnings: list[str] = []
    blockers: list[str] = []
    if not path.is_file():
        warnings.append("ARTIFACT_NOT_PRESENT")
        if required:
            blockers.append("REQUIRED_ARTIFACT_NOT_PRESENT")
    elif raw is None:
        blockers.append("ARTIFACT_UNREADABLE")
    if raw is not None:
        warnings.extend(_as_list(raw.get("warnings")))
        blockers.extend(_as_list(raw.get("blockers")))
        warnings.extend(_secret_warnings(raw, section_id))
    key_fields: dict[str, Any] = {}
    if raw is not None:
        for key in field_keys:
            value = raw.get(key)
            if value not in (None, ""):
                key_fields[key] = value
    status = _status_from(raw)
    if raw is not None and raw.get("schema_version"):
        key_fields.setdefault("schema_version", raw.get("schema_version"))
    digest = _digest_from(raw, path)
    summary = _summary_for(section_id, status, key_fields, warnings, blockers)
    return ResearchOsBriefingSection(
        section_id=section_id,
        title=title,
        status=status,
        summary=summary,
        artifact_path=str(path),
        digest=digest,
        key_fields=key_fields,
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
    )


def _summary_for(section_id: str, status: str, fields: dict[str, Any], warnings: list[str], blockers: list[str]) -> str:
    if blockers:
        return f"{section_id} is blocked/degraded by {len(blockers)} blocker(s)."
    if warnings:
        return f"{section_id} is present with {len(warnings)} warning(s)."
    if status == "NOT_PRESENT":
        return f"{section_id} has no artifact yet."
    if fields:
        bits = []
        for key in ("closure_id", "verification_id", "attestation_id", "run_id", "book_id", "provider_id", "policy_status", "trust_banner"):
            if key in fields:
                bits.append(f"{key}={fields[key]}")
        if bits:
            return "; ".join(bits)
    return f"{section_id} status is {status}."


def _memory_latest_path(root: Path) -> Path:
    return (root / "strategy_memory" / "latest" / "memory_index.json").resolve()


def _thesis_latest_path(root: Path) -> Path:
    return (root / "strategy_theses" / "latest" / "thesis_evaluation.json").resolve()


def _shadow_book_latest_path(root: Path) -> Path:
    return (root / "shadow_books" / "latest" / "shadow_book_manifest.json").resolve()


def _shadow_book_risk_latest_path(root: Path) -> Path:
    return (root / "shadow_books" / "latest" / "latest_risk_summary.json").resolve()


def _latest_batch_summary_path(root: Path) -> Path:
    candidates = sorted(root.glob("strategy_batches/*/batch_summary.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return candidates[0].resolve() if candidates else (root / "strategy_batches" / "latest" / "batch_summary.json").resolve()


def _sections(root: Path, *, repo_root: Path | None = None, artifact_root: Path | None = None) -> list[ResearchOsBriefingSection]:
    return [
        _section(
            "closure",
            "Research OS closure",
            _research_os_closure_latest_path(repo_root, artifact_root),
            required=True,
            field_keys=("closure_id", "status", "trust_banner", "present_artifact_count", "manifest_sha256"),
        ),
        _section(
            "closure_verification",
            "Closure verification",
            research_os_verification_latest_path(repo_root, artifact_root),
            required=True,
            field_keys=("verification_id", "closure_id", "status", "trust_banner", "result_sha256"),
        ),
        _section(
            "operator_attestation",
            "Operator attestation",
            research_os_operator_attestation_latest_path(repo_root, artifact_root),
            required=True,
            field_keys=("attestation_id", "closure_id", "operator_id", "decision", "attestation_sha256"),
        ),
        _section(
            "provider_paper_loop",
            "Provider-backed paper loop",
            provider_paper_loop_manifest_path(repo_root),
            field_keys=("run_id", "ok", "generated_at_utc", "manifest_sha256"),
        ),
        _section(
            "provider_historical_snapshot",
            "Provider historical snapshot",
            provider_historical_snapshot_run_path(repo_root),
            field_keys=("ok", "network_used", "manifest_sha256"),
        ),
        _section(
            "paper_broker_policy",
            "Paper broker policy",
            paper_broker_status_artifact_path(repo_root),
            field_keys=("broker_id", "mode", "policy_status", "paper_trading_only", "manifest_sha256"),
        ),
        _section(
            "strategy_batch",
            "Latest strategy batch",
            _latest_batch_summary_path(root),
            field_keys=("run_id", "batch_id", "ok", "manifest_sha256"),
        ),
        _section(
            "strategy_memory",
            "Strategy memory / graveyard",
            _memory_latest_path(root),
            field_keys=("active_count", "killed_count", "rejected_count", "memory_index_sha256"),
        ),
        _section(
            "strategy_thesis",
            "Strategy thesis / falsification",
            _thesis_latest_path(root),
            field_keys=("strategy_id", "thesis_id", "support_status", "evaluation_sha256"),
        ),
        _section(
            "shadow_book",
            "Shadow book",
            _shadow_book_latest_path(root),
            field_keys=("book_id", "status", "manifest_sha256"),
        ),
        _section(
            "shadow_book_risk",
            "Shadow book risk",
            _shadow_book_risk_latest_path(root),
            field_keys=("book_id", "status", "max_drawdown", "gross_exposure", "risk_summary_sha256"),
        ),
        _section(
            "runtime_demo",
            "Research OS runtime demo",
            research_os_runtime_manifest_path(repo_root),
            field_keys=("run_id", "ok", "generated_at_utc", "manifest_sha256"),
        ),
    ]


def _action_items(sections: list[ResearchOsBriefingSection]) -> list[ResearchOsBriefingActionItem]:
    items: list[ResearchOsBriefingActionItem] = []
    by_id = {s.section_id: s for s in sections}
    for s in sections:
        if s.blockers:
            items.append(
                ResearchOsBriefingActionItem(
                    action_id=f"resolve-{s.section_id}-blockers",
                    severity=ResearchOsBriefingSeverity.BLOCKER,
                    title=f"Resolve blockers in {s.title}",
                    detail="; ".join(s.blockers[:5]),
                    related_section_id=s.section_id,
                )
            )
        elif s.warnings and s.status == "NOT_PRESENT":
            cmd = _suggested_command_for_missing(s.section_id)
            items.append(
                ResearchOsBriefingActionItem(
                    action_id=f"produce-{s.section_id}",
                    severity=ResearchOsBriefingSeverity.WARNING,
                    title=f"Produce {s.title} artifact",
                    detail="Artifact is missing; cockpit will remain degraded until this evidence exists.",
                    suggested_command=cmd,
                    related_section_id=s.section_id,
                )
            )
    verification = by_id.get("closure_verification")
    attestation = by_id.get("operator_attestation")
    if verification and verification.status != "VERIFIED":
        items.append(
            ResearchOsBriefingActionItem(
                action_id="verify-closure",
                severity=ResearchOsBriefingSeverity.BLOCKER if verification.blockers else ResearchOsBriefingSeverity.WARNING,
                title="Verify Research OS closure evidence",
                detail="Closure verification is not VERIFIED.",
                suggested_command="strategy-validator-research-os-attestation verify --write --overwrite --json",
                related_section_id="closure_verification",
            )
        )
    if attestation and attestation.status not in {"ACKNOWLEDGED", "ACCEPTED_WITH_RESTRICTIONS"}:
        items.append(
            ResearchOsBriefingActionItem(
                action_id="attest-closure",
                severity=ResearchOsBriefingSeverity.WARNING,
                title="Record operator attestation",
                detail="Operator attestation is absent or blocked.",
                suggested_command=(
                    "strategy-validator-research-os-attestation attest --operator-id local-operator "
                    "--decision ACCEPTED_WITH_RESTRICTIONS --rationale \"Paper-only evidence acknowledged\" --overwrite --json"
                ),
                related_section_id="operator_attestation",
            )
        )
    return _dedupe_actions(items)


def _suggested_command_for_missing(section_id: str) -> str | None:
    return {
        "closure": "strategy-validator-research-os-closure build --overwrite --json",
        "closure_verification": "strategy-validator-research-os-attestation verify --write --overwrite --json",
        "operator_attestation": "strategy-validator-research-os-attestation attest --operator-id local-operator --decision ACCEPTED_WITH_RESTRICTIONS --overwrite --json",
        "provider_paper_loop": "python scripts/run_provider_paper_loop.py --no-network --overwrite --json",
        "paper_broker_policy": "strategy-validator-paper-broker status --json",
        "shadow_book": "python scripts/run_shadow_book_demo.py --overwrite --json",
    }.get(section_id)


def _dedupe_actions(items: list[ResearchOsBriefingActionItem]) -> list[ResearchOsBriefingActionItem]:
    seen: set[str] = set()
    out: list[ResearchOsBriefingActionItem] = []
    for item in items:
        if item.action_id in seen:
            continue
        seen.add(item.action_id)
        out.append(item)
    return out


def _derive_status(sections: list[ResearchOsBriefingSection], action_items: list[ResearchOsBriefingActionItem]) -> tuple[ResearchOsBriefingStatus, ResearchOsTrustBanner, str]:
    present = [s for s in sections if s.status != "NOT_PRESENT"]
    blocker_count = sum(len(s.blockers) for s in sections)
    required_missing = [s for s in sections if "REQUIRED_ARTIFACT_NOT_PRESENT" in s.blockers]
    action_blockers = [a for a in action_items if a.severity == ResearchOsBriefingSeverity.BLOCKER]
    closure = next((s for s in sections if s.section_id == "closure"), None)
    verification = next((s for s in sections if s.section_id == "closure_verification"), None)
    attestation = next((s for s in sections if s.section_id == "operator_attestation"), None)
    if not present:
        return ResearchOsBriefingStatus.EMPTY, ResearchOsTrustBanner.UNTRUSTED, "No Research OS evidence artifacts are present."
    if blocker_count or required_missing or action_blockers:
        return ResearchOsBriefingStatus.BLOCKED, ResearchOsTrustBanner.UNTRUSTED, "Research OS briefing is blocked by missing or invalid required evidence."
    if verification and verification.status == "VERIFIED" and attestation and attestation.status in {"ACKNOWLEDGED", "ACCEPTED_WITH_RESTRICTIONS"}:
        banner = ResearchOsTrustBanner.TRUST_RESTRICTED
        if closure and closure.key_fields.get("trust_banner") == "TRUSTED" and attestation.status == "ACKNOWLEDGED":
            banner = ResearchOsTrustBanner.TRUSTED
        return ResearchOsBriefingStatus.READY, banner, "Research OS closure is verified and operator attestation is present."
    return ResearchOsBriefingStatus.RESTRICTED, ResearchOsTrustBanner.TRUST_RESTRICTED, "Research OS evidence exists but requires review before operator use."


def _pack_with_digest(pack: ResearchOsBriefingPack) -> ResearchOsBriefingPack:
    body = pack.model_dump(mode="json", exclude={"briefing_sha256"})
    digests = dict(pack.digests)
    digests["sections_sha256"] = canonical_json_sha256([s.model_dump(mode="json") for s in pack.sections])
    digests["action_items_sha256"] = canonical_json_sha256([a.model_dump(mode="json") for a in pack.action_items])
    body["digests"] = digests
    sha = canonical_json_sha256(body)
    return pack.model_copy(update={"digests": digests, "briefing_sha256": sha})


def build_research_os_briefing_pack(
    *,
    briefing_id: str = "daily-research-briefing",
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
) -> ResearchOsBriefingPack:
    root = _artifact_root(repo_root, artifact_root)
    sections = _sections(root, repo_root=repo_root, artifact_root=artifact_root)
    actions = _action_items(sections)
    status, banner, headline = _derive_status(sections, actions)
    warnings: list[str] = []
    blockers: list[str] = []
    for s in sections:
        warnings.extend(f"{s.section_id}:{w}" for w in s.warnings)
        blockers.extend(f"{s.section_id}:{b}" for b in s.blockers)
    pack = ResearchOsBriefingPack(
        briefing_id=briefing_id,
        artifact_root=str(root),
        status=status,
        trust_banner=banner,
        headline=headline,
        sections=sections,
        action_items=actions,
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
    )
    return _pack_with_digest(pack)


def write_research_os_briefing_pack(
    pack: ResearchOsBriefingPack,
    *,
    repo_root: Path | None = None,
    artifact_root: Path | None = None,
    overwrite: bool = False,
) -> Path:
    root = research_os_briefing_root(repo_root, artifact_root)
    bdir = root / "briefings" / pack.briefing_id
    if bdir.exists():
        if not overwrite:
            raise FileExistsError(f"RESEARCH_OS_BRIEFING_EXISTS:{pack.briefing_id}")
        shutil.rmtree(bdir)
    path = bdir / "research_os_briefing_pack.json"
    payload = pack.model_dump(mode="json")
    _write_json(path, payload)
    _write_json(root / "latest" / "research_os_briefing_pack.json", payload)
    return path.resolve()


def load_latest_research_os_briefing_pack(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> ResearchOsBriefingPack | None:
    raw = _read_json(research_os_briefing_latest_path(repo_root, artifact_root))
    if raw is None:
        return None
    return ResearchOsBriefingPack.model_validate(raw)


def build_ui_research_os_briefing_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    pack = load_latest_research_os_briefing_pack(repo_root=repo_root)
    degraded: list[str] = []
    if pack is None:
        degraded.append("NO_RESEARCH_OS_BRIEFING_PACK")
    elif pack.status in {ResearchOsBriefingStatus.BLOCKED, ResearchOsBriefingStatus.EMPTY}:
        degraded.append(f"BRIEFING_{pack.status.value}")
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_broker_orders": True,
        "no_order_controls": True,
        "status": "PRESENT" if pack else "NOT_PRESENT",
        "artifact_path": str(research_os_briefing_latest_path(repo_root)),
        "latest_briefing": pack.model_dump(mode="json") if pack else None,
        "degraded": sorted(set(degraded)),
    }


__all__ = [
    "build_research_os_briefing_pack",
    "build_ui_research_os_briefing_latest_payload",
    "load_latest_research_os_briefing_pack",
    "research_os_briefing_latest_path",
    "research_os_briefing_root",
    "write_research_os_briefing_pack",
]
