"""Lineage chain construction and filtering for semantic validator handoff read-plane."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from strategy_validator.application.ui_semantic_validator_handoff_lineage_common import (
    _CHAIN_KIND_ORDER,
    _READY_ACTION,
    _REPAIR_ACTION,
    _as_list,
    _component_id,
    _contains,
    _entry_ref,
    _find_first,
    _find_first_by_any,
    _link_digest,
    _s,
)


def _link_check(
    *,
    source: dict[str, Any] | None,
    target: dict[str, Any] | None,
    source_ref_field: str,
    target_id_field: str,
    source_checksum_field: str | None = None,
    issue_prefix: str,
) -> tuple[list[str], list[dict[str, Any]]]:
    issues: list[str] = []
    checks: list[dict[str, Any]] = []
    if source is None:
        return issues, checks

    expected_id = _s(source.get(source_ref_field))
    actual_id = _s(None if target is None else target.get(target_id_field))
    id_ok = bool(expected_id and target is not None and expected_id == actual_id)
    if not id_ok:
        issues.append(f"{issue_prefix}_ID_LINK_BROKEN")
    checks.append(
        {
            "link": f"{source.get('artifact_kind')}->{None if target is None else target.get('artifact_kind')}",
            "source_ref_field": source_ref_field,
            "target_id_field": target_id_field,
            "expected_id": expected_id or None,
            "actual_id": actual_id or None,
            "id_ok": id_ok,
        }
    )

    if source_checksum_field is not None:
        expected_checksum = _s(source.get(source_checksum_field))
        actual_checksum = _s(None if target is None else target.get("payload_checksum"))
        checksum_ok = bool(expected_checksum and target is not None and expected_checksum == actual_checksum)
        if not checksum_ok:
            issues.append(f"{issue_prefix}_PAYLOAD_CHECKSUM_MISMATCH")
        checks[-1].update(
            {
                "source_checksum_field": source_checksum_field,
                "expected_payload_checksum": expected_checksum or None,
                "actual_payload_checksum": actual_checksum or None,
                "checksum_ok": checksum_ok,
            }
        )
    return issues, checks


def _select_chain_from_anchor(
    anchor: dict[str, Any],
    *,
    ledgers: list[dict[str, Any]],
    certificates: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    ingresses: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None, dict[str, Any] | None]:
    kind = _s(anchor.get("artifact_kind"))
    ledger: dict[str, Any] | None = None
    certificate: dict[str, Any] | None = None
    packet: dict[str, Any] | None = None
    ingress: dict[str, Any] | None = None

    if kind == "validator_packet":
        packet = anchor
        certificate = _find_first(certificates, "certificate_id", packet.get("certificate_id"))
        ingress = _find_first(ingresses, "packet_id", packet.get("packet_id")) or _find_first(
            ingresses, "packet_id", packet.get("artifact_id")
        )
        if certificate is not None:
            ledger = _find_first(ledgers, "ledger_id", certificate.get("ledger_id"))
    elif kind == "ingress_certificate":
        ingress = anchor
        packet = _find_first_by_any(
            packets, (("packet_id", ingress.get("packet_id")), ("artifact_id", ingress.get("packet_id")))
        )
        if packet is not None:
            certificate = _find_first(certificates, "certificate_id", packet.get("certificate_id"))
        if certificate is not None:
            ledger = _find_first(ledgers, "ledger_id", certificate.get("ledger_id"))
    elif kind == "handoff_certificate":
        certificate = anchor
        ledger = _find_first(ledgers, "ledger_id", certificate.get("ledger_id"))
        packet = _find_first(packets, "certificate_id", certificate.get("certificate_id"))
        if packet is not None:
            ingress = _find_first_by_any(
                ingresses, (("packet_id", packet.get("packet_id")), ("packet_id", packet.get("artifact_id")))
            )
    elif kind == "decision_ledger":
        ledger = anchor
        certificate = _find_first(certificates, "ledger_id", ledger.get("ledger_id"))
        if certificate is not None:
            packet = _find_first(packets, "certificate_id", certificate.get("certificate_id"))
        if packet is not None:
            ingress = _find_first_by_any(
                ingresses, (("packet_id", packet.get("packet_id")), ("packet_id", packet.get("artifact_id")))
            )

    return ledger, certificate, packet, ingress


def _chain_entry(
    *,
    experiment_id: str,
    ledger: dict[str, Any] | None,
    certificate: dict[str, Any] | None,
    packet: dict[str, Any] | None,
    ingress: dict[str, Any] | None,
) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    checks: list[dict[str, Any]] = []
    components = {
        "decision_ledger": _entry_ref(ledger),
        "handoff_certificate": _entry_ref(certificate),
        "validator_packet": _entry_ref(packet),
        "ingress_certificate": _entry_ref(ingress),
    }

    for kind, entry in (
        ("DECISION_LEDGER", ledger),
        ("HANDOFF_CERTIFICATE", certificate),
        ("VALIDATOR_PACKET", packet),
        ("INGRESS_CERTIFICATE", ingress),
    ):
        if entry is None:
            issues.append(f"MISSING_{kind}")

    for link_issues, link_checks in (
        _link_check(
            source=certificate,
            target=ledger,
            source_ref_field="ledger_id",
            target_id_field="ledger_id",
            source_checksum_field="ledger_payload_checksum",
            issue_prefix="CERTIFICATE_TO_LEDGER",
        ),
        _link_check(
            source=packet,
            target=certificate,
            source_ref_field="certificate_id",
            target_id_field="certificate_id",
            source_checksum_field="certificate_payload_checksum",
            issue_prefix="PACKET_TO_CERTIFICATE",
        ),
        _link_check(
            source=ingress,
            target=packet,
            source_ref_field="packet_id",
            target_id_field="packet_id",
            source_checksum_field="packet_payload_checksum",
            issue_prefix="INGRESS_TO_PACKET",
        ),
    ):
        issues.extend(link_issues)
        checks.extend(link_checks)

    present = [entry for entry in (ledger, certificate, packet, ingress) if entry is not None]
    component_blockers = sorted({code for entry in present for code in _as_list(entry.get("blocker_codes"))})
    component_warnings = sorted({code for entry in present for code in _as_list(entry.get("warning_codes"))})
    component_issues = sorted({code for entry in present for code in _as_list(entry.get("issue_codes"))})
    if component_blockers:
        issues.append("COMPONENT_BLOCKERS_PRESENT")
    if component_issues:
        issues.append("COMPONENT_SELF_VERIFICATION_ISSUES_PRESENT")
    if any(not bool(entry.get("verified")) for entry in present):
        issues.append("UNVERIFIED_COMPONENTS_PRESENT")
    if any(not bool(entry.get("handoff_allowed")) for entry in present):
        issues.append("HANDOFF_NOT_ALLOWED_FOR_ALL_PRESENT_COMPONENTS")
    if ingress is not None and not bool(ingress.get("ready_for_validator_ingress")):
        issues.append("INGRESS_CERTIFICATE_NOT_READY_FOR_VALIDATOR_INGRESS")
    if not component_warnings and all(entry is not None for entry in (ledger, certificate, packet, ingress)):
        warnings = []
    else:
        warnings.extend(component_warnings)

    issue_codes = sorted(dict.fromkeys(issues + component_issues))
    warning_codes = sorted(dict.fromkeys(warnings))
    complete = all(entry is not None for entry in (ledger, certificate, packet, ingress))
    link_ok = not any(code.endswith("_ID_LINK_BROKEN") or code.endswith("_PAYLOAD_CHECKSUM_MISMATCH") for code in issue_codes)
    ready = complete and link_ok and not issue_codes and ingress is not None and bool(ingress.get("ready_for_validator_ingress"))
    status = "READY" if ready else ("BROKEN" if any("LINK_BROKEN" in code or "CHECKSUM_MISMATCH" in code for code in issue_codes) else "INCOMPLETE")
    recommended_action = _READY_ACTION if ready else _REPAIR_ACTION
    component_ids = {
        "decision_ledger_id": _component_id(ledger),
        "handoff_certificate_id": _component_id(certificate),
        "validator_packet_id": _component_id(packet),
        "ingress_certificate_id": _component_id(ingress),
    }
    chain_id = "semantic-validator-lineage-" + _link_digest([experiment_id, *component_ids.values()])[:20]
    chain_digest = _link_digest(
        [
            experiment_id,
            *(None if entry is None else entry.get("payload_checksum") for entry in (ledger, certificate, packet, ingress)),
            *(None if entry is None else entry.get("artifact_sha256") for entry in (ledger, certificate, packet, ingress)),
        ]
    )
    return {
        "chain_id": chain_id,
        "experiment_id": experiment_id,
        "status": status,
        "complete_chain": complete,
        "link_integrity_ok": link_ok,
        "ready_for_operator_review": ready,
        "ready_for_validator_ingress": bool(ingress.get("ready_for_validator_ingress")) if ingress is not None else False,
        "recommended_action": recommended_action,
        "chain_digest": chain_digest,
        **component_ids,
        "component_count_present": len(present),
        "component_count_expected": len(_CHAIN_KIND_ORDER),
        "issue_count": len(issue_codes),
        "issue_codes": issue_codes,
        "warning_codes": warning_codes,
        "component_blocker_codes": component_blockers,
        "component_warning_codes": component_warnings,
        "component_issue_codes": component_issues,
        "link_checks": checks,
        "components": components,
        "summary_line": f"{experiment_id} · {status} · components={len(present)}/4 · issues={len(issue_codes)}",
    }


def _chain_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        _s(row.get("experiment_id")),
        _s(row.get("decision_ledger_id")),
        _s(row.get("handoff_certificate_id")),
        _s(row.get("validator_packet_id")),
        _s(row.get("ingress_certificate_id")),
    )


def _build_chains(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_experiment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries:
        by_experiment[_s(entry.get("experiment_id")) or "UNKNOWN"].append(entry)

    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str, str]] = set()
    for experiment_id, experiment_entries in by_experiment.items():
        by_kind = {kind: [entry for entry in experiment_entries if entry.get("artifact_kind") == kind] for kind in _CHAIN_KIND_ORDER}
        anchors = by_kind["validator_packet"] or by_kind["ingress_certificate"] or by_kind["handoff_certificate"] or by_kind["decision_ledger"]
        for anchor in anchors:
            ledger, certificate, packet, ingress = _select_chain_from_anchor(
                anchor,
                ledgers=by_kind["decision_ledger"],
                certificates=by_kind["handoff_certificate"],
                packets=by_kind["validator_packet"],
                ingresses=by_kind["ingress_certificate"],
            )
            row = _chain_entry(experiment_id=experiment_id, ledger=ledger, certificate=certificate, packet=packet, ingress=ingress)
            key = _chain_key(row)
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    rows.sort(key=lambda row: (_s(row.get("experiment_id")), _s(row.get("status")), _s(row.get("chain_id"))), reverse=True)
    return rows


def _issue_haystack(row: dict[str, Any]) -> str:
    parts = [str(row.get("status") or ""), str(row.get("recommended_action") or ""), str(row.get("summary_line") or "")]
    parts.extend(_as_list(row.get("issue_codes")))
    parts.extend(_as_list(row.get("warning_codes")))
    parts.extend(_as_list(row.get("component_blocker_codes")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    chain_status: set[str],
    ready_for_operator_review: bool | None,
    require_broken_links: bool | None,
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_issue_haystack(row), issue_contains):
        return False
    if chain_status and _s(row.get("status")).upper() not in chain_status:
        return False
    if ready_for_operator_review is not None and bool(row.get("ready_for_operator_review")) is not ready_for_operator_review:
        return False
    broken = not bool(row.get("link_integrity_ok"))
    if require_broken_links is not None and broken is not require_broken_links:
        return False
    return True
