"""Read-plane cockpit summary fields for GET /ui/evidence (no secrets; artifact-backed only)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEPLOYMENT_MANIFEST_SCHEMA = "single_tenant_deployment_evidence/v1"

_COCKPI_UNKNOWN = "UNKNOWN"
_COCKPI_DEGRADED = "DEGRADED"


def _load_json_dict(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _latest_file_under(root: Path, filename: str) -> Path | None:
    if not root.exists():
        return None
    matches = [p for p in root.rglob(filename) if p.is_file()]
    if not matches:
        return None
    matches.sort(key=lambda p: p.stat().st_mtime_ns)
    return matches[-1]


def _tri_ok_from_evidence_file_entry(entry: dict[str, Any] | None) -> bool | None:
    if entry is None:
        return None
    ok_field = entry.get("ok_field")
    if isinstance(ok_field, bool):
        return ok_field
    st = entry.get("status")
    if st == "PASS":
        return True
    if st == "FAIL":
        return False
    return None


def _line_status_from_evidence_file_entry(entry: dict[str, Any] | None) -> str:
    if entry is None:
        return _COCKPI_UNKNOWN
    st = entry.get("status")
    if isinstance(st, str) and st in {"PASS", "FAIL", "WARN"}:
        return st
    return _COCKPI_DEGRADED


def _files_index(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in manifest.get("files", ()):
        if isinstance(item, dict):
            name = item.get("name")
            if isinstance(name, str):
                out[name] = item
    return out


def _loose_report_tri_ok(path: Path | None) -> bool | None:
    if path is None:
        return None
    data = _load_json_dict(path)
    if data is None:
        return None
    for key in ("ok", "acceptance_ok", "deployment_ready", "passed"):
        if key in data and isinstance(data[key], bool):
            return bool(data[key])
    status = data.get("status")
    if isinstance(status, str):
        u = status.strip().upper()
        if u in {"PASS", "READY", "OK"}:
            return True
        if u in {"FAIL", "BLOCKED", "ERROR", "NOT_READY"}:
            return False
    return None


def _loose_report_line_status(path: Path | None) -> str:
    if path is None:
        return _COCKPI_UNKNOWN
    data = _load_json_dict(path)
    if data is None:
        return _COCKPI_DEGRADED
    st = data.get("status")
    if isinstance(st, str) and st.upper() in {"PASS", "FAIL", "WARN", "READY", "BLOCKED"}:
        if st.upper() in {"READY", "PASS"}:
            return "PASS"
        if st.upper() == "FAIL" or st.upper() == "BLOCKED":
            return "FAIL"
        return "WARN"
    ok = _loose_report_tri_ok(path)
    if ok is True:
        return "PASS"
    if ok is False:
        return "FAIL"
    return _COCKPI_DEGRADED


def build_ui_evidence_cockpit_fields(
    *,
    search_root: Path,
    projection_generated_at_utc: str,
    disk_runtime_review: dict[str, Any] | None,
) -> dict[str, Any]:
    """Stable read-plane fields for operator cockpit cards (unknown when artifacts absent)."""
    root = search_root.resolve()
    manifest_path = _latest_file_under(root, "deployment-evidence.json")
    manifest: dict[str, Any] | None = None
    if manifest_path is not None:
        candidate = _load_json_dict(manifest_path)
        if candidate and candidate.get("schema_version") == _DEPLOYMENT_MANIFEST_SCHEMA:
            manifest = candidate

    files_idx: dict[str, dict[str, Any]] = _files_index(manifest) if manifest else {}

    def _from_manifest_roles(roles: tuple[str, ...]) -> tuple[bool | None, str]:
        for role in roles:
            e = files_idx.get(role)
            if e is not None:
                return _tri_ok_from_evidence_file_entry(e), _line_status_from_evidence_file_entry(e)
        return None, _COCKPI_UNKNOWN

    api_smoke_ok, api_smoke_status = _from_manifest_roles(("api_smoke", "single_tenant_api_smoke"))
    ledger_integrity_ok, _ = _from_manifest_roles(("ledger_verify",))
    backup_restore_ok, _ = _from_manifest_roles(("ledger_backup",))
    ci_local_verify_ok, _ = _from_manifest_roles(("ci_local_verify",))

    if manifest is None:
        ap = _latest_file_under(root, "api-smoke.json")
        if api_smoke_ok is None:
            api_smoke_ok = _loose_report_tri_ok(ap)
        if api_smoke_status == _COCKPI_UNKNOWN:
            api_smoke_status = _loose_report_line_status(ap)

        lv = _latest_file_under(root, "ledger-verify.json")
        if ledger_integrity_ok is None:
            ledger_integrity_ok = _loose_report_tri_ok(lv)

        lb = _latest_file_under(root, "ledger-backup.json")
        if backup_restore_ok is None:
            backup_restore_ok = _loose_report_tri_ok(lb)

        cv = _latest_file_under(root, "ci-local-verify.json")
        if ci_local_verify_ok is None:
            ci_local_verify_ok = _loose_report_tri_ok(cv)

    if manifest is not None:
        deployment_evidence_ok = manifest.get("ok") if isinstance(manifest.get("ok"), bool) else None
        if deployment_evidence_ok is True:
            deployment_status = "PASS"
        elif deployment_evidence_ok is False:
            deployment_status = "FAIL"
        else:
            deployment_status = _COCKPI_DEGRADED
        evidence_generated_at = manifest.get("generated_at_utc")
        if not isinstance(evidence_generated_at, str) or not evidence_generated_at.strip():
            evidence_generated_at = projection_generated_at_utc
        claimed = manifest.get("frontend_readiness_claimed")
        if claimed is True:
            frontend_readiness_status = "CLAIMED"
        elif claimed is False:
            frontend_readiness_status = "NOT_CLAIMED"
        else:
            frontend_readiness_status = _COCKPI_UNKNOWN
        ck = files_idx.get("frontend_checkpoint")
        if ck is not None and ck.get("status") == "FAIL":
            frontend_readiness_status = _COCKPI_DEGRADED
    else:
        deployment_evidence_ok = None
        deployment_status = _COCKPI_UNKNOWN
        evidence_generated_at = projection_generated_at_utc
        frontend_readiness_status = _COCKPI_UNKNOWN

    if disk_runtime_review:
        decision = disk_runtime_review.get("decision")
        operator_decision = decision if isinstance(decision, str) and decision.strip() else _COCKPI_UNKNOWN
        signoff = disk_runtime_review.get("signoff_status")
        if isinstance(signoff, str):
            su = signoff.upper()
            if su == "APPROVED":
                manual_operator_signoff_present = True
            elif su in {"WITHHELD", "REJECTED", "DENIED"}:
                manual_operator_signoff_present = False
            else:
                manual_operator_signoff_present = None
        else:
            manual_operator_signoff_present = None
    else:
        operator_decision = _COCKPI_UNKNOWN
        manual_operator_signoff_present = None

    return {
        "deployment_status": deployment_status,
        "deployment_evidence_ok": deployment_evidence_ok,
        "operator_decision": operator_decision,
        "manual_operator_signoff_present": manual_operator_signoff_present,
        "api_smoke_status": api_smoke_status,
        "api_smoke_ok": api_smoke_ok,
        "backup_restore_ok": backup_restore_ok,
        "ledger_integrity_ok": ledger_integrity_ok,
        "ci_local_verify_ok": ci_local_verify_ok,
        "frontend_readiness_status": frontend_readiness_status,
        "evidence_generated_at_utc": evidence_generated_at,
    }


__all__ = ["build_ui_evidence_cockpit_fields"]
