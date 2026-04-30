"""Build a secret-safe single-tenant deployment evidence pack.

This command collects the machine-readable reports produced during a backend-only
single-tenant deployment and emits a deterministic evidence manifest with file
hashes, schema checks, and a go/no-go status.  It never copies raw deployment
secrets; it records only report metadata and SHA-256 digests of operator evidence
files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

_SCHEMA_VERSION = "single_tenant_deployment_evidence/v1"
_FRONTEND_PACKAGE = "ui/strategist-web"
_DEPLOYMENT_MODEL = "single_tenant_backend_only"

_REQUIRED_FINAL_REPORT_SCHEMAS = {
    "acceptance": "single_tenant_deployment_acceptance/v1",
    "single_tenant_preflight": "single_tenant_deployment_preflight/v1",
    "preflight": "single_tenant_deployment_preflight/v1",
    "single_tenant_api_smoke": "single_tenant_api_http_smoke/v1",
    "api_smoke": "single_tenant_api_http_smoke/v1",
    "ledger_verify": ("ledger_ops_integrity_verify/v1", "ledger_ops_verify/v1"),
    "ledger_backup": "ledger_ops_backup/v1",
}

_OPTIONAL_REPORT_SCHEMAS = {
    "env_check": "single_tenant_deployment_env_check/v1",
    "bundle": "single_tenant_deployment_bundle/v1",
}

_SECRET_FIELD_MARKERS = ("token", "secret", "password", "api_key", "private_key")


@dataclass(frozen=True)
class EvidenceFile:
    name: str
    path: str
    exists: bool
    sha256: str | None
    size_bytes: int | None
    schema_version: str | None
    ok_field: bool | None
    status: str
    detail: str


@dataclass(frozen=True)
class DeploymentEvidenceReport:
    schema_version: str
    ok: bool
    generated_at_utc: str
    deployment_model: str
    evidence_dir: str
    frontend_expected_package: str
    frontend_package_present: bool
    frontend_readiness_claimed: bool
    final_evidence: bool
    files: tuple[EvidenceFile, ...]
    errors: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "generated_at_utc": self.generated_at_utc,
            "deployment_model": self.deployment_model,
            "evidence_dir": self.evidence_dir,
            "frontend_expected_package": self.frontend_expected_package,
            "frontend_package_present": self.frontend_package_present,
            "frontend_readiness_claimed": self.frontend_readiness_claimed,
            "final_evidence": self.final_evidence,
            "files": [asdict(item) for item in self.files],
            "errors": list(self.errors),
        }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _contains_plaintext_secret_like_value(value: object, *, parent_key: str = "") -> bool:
    if isinstance(value, dict):
        for key, child in value.items():
            if _contains_plaintext_secret_like_value(child, parent_key=str(key)):
                return True
    elif isinstance(value, list):
        return any(_contains_plaintext_secret_like_value(child, parent_key=parent_key) for child in value)
    elif isinstance(value, str):
        lowered_key = parent_key.lower()
        if any(marker in lowered_key for marker in _SECRET_FIELD_MARKERS):
            stripped = value.strip()
            if stripped and not stripped.startswith("<redacted:") and len(stripped) >= 8:
                return True
    return False


def _load_json_report(path: Path) -> tuple[dict[str, object] | None, str | None]:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive operator diagnostic.
        return None, f"invalid JSON: {exc}"
    if not isinstance(loaded, dict):
        return None, "report is not a JSON object"
    return loaded, None


def _status_from_ok_field(payload: dict[str, object]) -> bool | None:
    for key in ("ok", "acceptance_ok", "deployment_ready", "passed"):
        if key in payload and isinstance(payload[key], bool):
            return bool(payload[key])
    status = payload.get("status")
    if isinstance(status, str):
        normalized = status.strip().upper()
        if normalized in {"PASS", "READY", "OK"}:
            return True
        if normalized in {"FAIL", "BLOCKED", "ERROR", "NOT_READY"}:
            return False
    return None


def _schema_label(expected_schema: str | tuple[str, ...] | None) -> str | None:
    if expected_schema is None:
        return None
    if isinstance(expected_schema, tuple):
        return " or ".join(repr(item) for item in expected_schema)
    return repr(expected_schema)


def _schema_matches(schema: str | None, expected_schema: str | tuple[str, ...] | None) -> bool:
    if expected_schema is None:
        return True
    if isinstance(expected_schema, tuple):
        return schema in expected_schema
    return schema == expected_schema


def _evaluate_report(name: str, path: Path, expected_schema: str | tuple[str, ...] | None, *, required: bool) -> EvidenceFile:
    if not path.exists():
        status = "FAIL" if required else "WARN"
        return EvidenceFile(
            name=name,
            path=str(path),
            exists=False,
            sha256=None,
            size_bytes=None,
            schema_version=None,
            ok_field=None,
            status=status,
            detail="required evidence report is missing" if required else "optional evidence report is missing",
        )

    payload, error = _load_json_report(path)
    digest = _sha256_file(path)
    size = path.stat().st_size
    if payload is None:
        return EvidenceFile(name, str(path), True, digest, size, None, None, "FAIL", error or "invalid JSON")

    schema = payload.get("schema_version") if isinstance(payload.get("schema_version"), str) else None
    if expected_schema and not _schema_matches(schema, expected_schema):
        return EvidenceFile(
            name,
            str(path),
            True,
            digest,
            size,
            schema,
            _status_from_ok_field(payload),
            "FAIL" if required else "WARN",
            f"schema_version must be {_schema_label(expected_schema)}; found {schema!r}",
        )

    if _contains_plaintext_secret_like_value(payload):
        # The evidence pack accepts redacted secret metadata in deployment env
        # reports, but it should not include raw secret-bearing fields in final
        # go-live reports.  The redacted env report remains optional context.
        if name not in {"env_check", "bundle"}:
            return EvidenceFile(
                name,
                str(path),
                True,
                digest,
                size,
                schema,
                _status_from_ok_field(payload),
                "FAIL",
                "report contains secret-like field names; do not include raw secret material in deployment evidence",
            )

    ok_field = _status_from_ok_field(payload)
    if required and ok_field is False:
        return EvidenceFile(name, str(path), True, digest, size, schema, ok_field, "FAIL", "report explicitly indicates failure")
    if required and ok_field is None and name not in {"ledger_verify", "ledger_backup"}:
        return EvidenceFile(name, str(path), True, digest, size, schema, ok_field, "WARN", "report has no recognized boolean ok/status field")
    return EvidenceFile(name, str(path), True, digest, size, schema, ok_field, "PASS", "report schema and digest recorded")


def _default_report_paths(evidence_dir: Path) -> dict[str, Path]:
    return {
        "env_check": evidence_dir / "deployment-env-check.json",
        "bundle": evidence_dir / "deployment-bundle.json",
        "acceptance": evidence_dir / "deployment-acceptance.json",
        "preflight": evidence_dir / "preflight.json",
        "api_smoke": evidence_dir / "api-smoke.json",
        "ledger_verify": evidence_dir / "ledger-verify.json",
        "ledger_backup": evidence_dir / "ledger-backup.json",
    }


def build_single_tenant_deployment_evidence(
    *,
    evidence_dir: str | Path,
    repo_root: str | Path = ".",
    final: bool = False,
    report_overrides: dict[str, str | Path] | None = None,
) -> DeploymentEvidenceReport:
    evidence_root = Path(evidence_dir).expanduser().resolve()
    repo = Path(repo_root).expanduser().resolve()
    overrides = report_overrides or {}
    paths = _default_report_paths(evidence_root)
    for name, override in overrides.items():
        if override:
            paths[name] = Path(override).expanduser().resolve()

    files: list[EvidenceFile] = []
    for name, expected in _OPTIONAL_REPORT_SCHEMAS.items():
        files.append(_evaluate_report(name, paths[name], expected, required=False))
    for name, expected in _REQUIRED_FINAL_REPORT_SCHEMAS.items():
        files.append(_evaluate_report(name, paths[name], expected, required=final))

    errors = [f"{item.name}: {item.detail}" for item in files if item.status == "FAIL"]
    if final:
        missing_required = [name for name in _REQUIRED_FINAL_REPORT_SCHEMAS if not paths[name].exists()]
        if missing_required:
            errors.append("missing final evidence reports: " + ", ".join(sorted(missing_required)))

    frontend_present = (repo / _FRONTEND_PACKAGE / "package.json").exists()
    ok = not errors and (not final or all(item.status == "PASS" for item in files if item.name in _REQUIRED_FINAL_REPORT_SCHEMAS))
    return DeploymentEvidenceReport(
        schema_version=_SCHEMA_VERSION,
        ok=ok,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        deployment_model=_DEPLOYMENT_MODEL,
        evidence_dir=str(evidence_root),
        frontend_expected_package=_FRONTEND_PACKAGE,
        frontend_package_present=frontend_present,
        frontend_readiness_claimed=False,
        final_evidence=bool(final),
        files=tuple(files),
        errors=tuple(errors),
    )


def write_evidence_outputs(report: DeploymentEvidenceReport, *, manifest_path: str | Path, markdown_path: str | Path = "") -> None:
    manifest = Path(manifest_path).expanduser().resolve()
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if markdown_path:
        markdown = Path(markdown_path).expanduser().resolve()
        markdown.parent.mkdir(parents=True, exist_ok=True)
        rows = "\n".join(
            f"| {item.status} | `{item.name}` | `{item.schema_version or '-'}` | `{item.sha256 or '-'}` | {item.detail} |"
            for item in report.files
        )
        markdown.write_text(
            f"""# Strategy Validator single-tenant deployment evidence\n\nSchema: `{report.schema_version}`  \nStatus: **{'PASS' if report.ok else 'FAIL'}**  \nDeployment model: `{report.deployment_model}`  \nFinal evidence: `{str(report.final_evidence).lower()}`  \nFrontend readiness claimed: `{str(report.frontend_readiness_claimed).lower()}`\n\n| Status | Evidence | Schema | SHA-256 | Detail |\n|---|---|---|---|---|\n{rows}\n\nThis evidence pack records report digests only. Keep raw deployment secrets out of evidence directories.\n""",
            encoding="utf-8",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or check a single-tenant backend deployment evidence pack.")
    parser.add_argument("--evidence-dir", default="scratch/single-tenant-deployment-evidence", help="Directory containing deployment report JSON files.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for frontend scope checks.")
    parser.add_argument("--manifest-output-path", default="", help="Optional path to write the evidence manifest JSON.")
    parser.add_argument("--summary-markdown-output-path", default="", help="Optional path to write a markdown evidence summary.")
    parser.add_argument("--final", action="store_true", help="Require post-deploy final evidence reports: preflight, API smoke, ledger verification, and backup.")
    parser.add_argument("--require-pass", action="store_true", help="Exit non-zero unless evidence status is PASS.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. Plain output is JSON too for stable automation.")
    for name in sorted({*list(_REQUIRED_FINAL_REPORT_SCHEMAS), *list(_OPTIONAL_REPORT_SCHEMAS)}):
        parser.add_argument(f"--{name.replace('_', '-')}-report", default="", help=f"Override path for {name} report JSON.")
    ns = parser.parse_args(argv)
    overrides = {
        name: getattr(ns, f"{name}_report")
        for name in {*list(_REQUIRED_FINAL_REPORT_SCHEMAS), *list(_OPTIONAL_REPORT_SCHEMAS)}
        if getattr(ns, f"{name}_report")
    }
    report = build_single_tenant_deployment_evidence(
        evidence_dir=ns.evidence_dir,
        repo_root=ns.repo_root,
        final=ns.final,
        report_overrides=overrides,
    )
    if ns.manifest_output_path or ns.summary_markdown_output_path:
        manifest_path = ns.manifest_output_path or str(Path(ns.evidence_dir) / "deployment-evidence.json")
        write_evidence_outputs(report, manifest_path=manifest_path, markdown_path=ns.summary_markdown_output_path)
    sys.stdout.write(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n")
    return 2 if ns.require_pass and not report.ok else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
