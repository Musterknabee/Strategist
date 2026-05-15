#!/usr/bin/env python3
"""CLI for public surface dashboard checks and JSON report emission (local_certify / CI parity)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.public_surface_dashboard import (  # noqa: E402
    NO_HEADROOM_RULE,
    PublicSurfaceDashboard,
    build_public_surface_dashboard,
)


def _render_dashboard_markdown(dashboard: PublicSurfaceDashboard) -> str:
    payload = dashboard.to_payload()
    metrics = payload["metrics"]
    lines = [
        "# Public Surface Dashboard",
        "",
        "Generated from `python scripts/public_surface_dashboard.py --json`.",
        "",
        "| Metric | Actual | Budget | Headroom | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name in sorted(metrics.keys()):
        m = metrics[name]
        lines.append(
            f"| `{name}` | {m['actual']} | {m['budget']} | {m['headroom']} | {m['status']} |",
        )
    no_head = payload.get("no_headroom") or []
    if no_head:
        lines.extend(["", f"No-headroom categories: {', '.join(no_head)}.", ""])
    else:
        lines.extend(["", "No-headroom categories: none.", ""])
    lines.append(NO_HEADROOM_RULE)
    lines.append("")
    return "\n".join(lines)


def validate_public_surface_ratchet(dashboard: dict[str, object], ratchet_path: Path) -> dict[str, object]:
    """Validate *dashboard* payload against the machine-readable budget ratchet file."""
    blockers: list[str] = []
    try:
        ratchet = json.loads(ratchet_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "schema_version": "public_surface_ratchet_validation/v1",
            "status": "FAIL",
            "blockers": [f"PUBLIC_SURFACE_RATCHET_FILE_INVALID:{exc}"],
        }
    if not isinstance(ratchet, dict):
        return {
            "schema_version": "public_surface_ratchet_validation/v1",
            "status": "FAIL",
            "blockers": ["PUBLIC_SURFACE_RATCHET_NOT_OBJECT"],
        }
    baselines = ratchet.get("baselines")
    if not isinstance(baselines, dict):
        blockers.append("PUBLIC_SURFACE_RATCHET_BASELINES_MISSING")
        baselines = {}
    approved_growth = ratchet.get("approved_surface_growth") or []
    approved_budget = ratchet.get("approved_budget_increases") or []
    metrics = dashboard.get("metrics")
    if not isinstance(metrics, dict):
        blockers.append("PUBLIC_SURFACE_RATCHET_DASHBOARD_METRICS_INVALID")

    def _growth_approved(metric: str, old_actual: int, new_actual: int) -> bool:
        if not isinstance(approved_growth, list):
            return False
        for item in approved_growth:
            if not isinstance(item, dict):
                continue
            if (
                str(item.get("metric")) == metric
                and int(item.get("old_actual", -1)) == old_actual
                and int(item.get("new_actual", -1)) == new_actual
            ):
                return True
        return False

    def _budget_increase_approved(metric: str, old_budget: int, new_budget: int) -> bool:
        if not isinstance(approved_budget, list):
            return False
        for item in approved_budget:
            if not isinstance(item, dict):
                continue
            if (
                str(item.get("metric")) == metric
                and int(item.get("old_budget", -1)) == old_budget
                and int(item.get("new_budget", -1)) == new_budget
            ):
                return True
        return False

    if isinstance(metrics, dict):
        for metric_name, metric in metrics.items():
            if not isinstance(metric, dict):
                continue
            current_actual = int(metric["actual"])
            current_budget = int(metric["budget"])
            base = baselines.get(metric_name)
            if not isinstance(base, dict):
                blockers.append(f"PUBLIC_SURFACE_RATCHET_BASELINE_MISSING:{metric_name}")
                continue
            baseline_actual = int(base.get("actual", -1))
            baseline_budget = int(base.get("budget", -1))
            if current_actual > baseline_actual and not _growth_approved(metric_name, baseline_actual, current_actual):
                blockers.append(f"PUBLIC_SURFACE_GROWTH_REQUIRES_RATIONALE:{metric_name}")
            if current_budget > baseline_budget and not _budget_increase_approved(
                metric_name, baseline_budget, current_budget
            ):
                blockers.append(f"PUBLIC_SURFACE_BUDGET_INCREASE_REQUIRES_RATIONALE:{metric_name}")

    status = "PASS" if not blockers else "FAIL"
    return {"schema_version": "public_surface_ratchet_validation/v1", "status": status, "blockers": blockers}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-doc", type=Path, help="Verify the dashboard markdown doc matches current metrics.")
    parser.add_argument("--check-ratchet", type=Path, help="Path to public_surface_budget_ratchet.json.")
    parser.add_argument("--output-json", type=Path, help="Write the sealed dashboard JSON report.")
    parser.add_argument("--json", action="store_true", help="Print a short machine-readable summary to stdout.")
    ns = parser.parse_args(argv)

    dashboard = build_public_surface_dashboard(REPO_ROOT)

    if ns.check_doc is not None and ns.check_ratchet is None and ns.output_json is None:
        rendered = _render_dashboard_markdown(dashboard)
        existing = ns.check_doc.read_text(encoding="utf-8")
        if rendered.strip() != existing.strip():
            print("public_surface_dashboard_doc: stale", file=sys.stderr)
            return 1
        print("public_surface_dashboard_doc: current")
        return 0

    ratchet_path = ns.check_ratchet
    if ratchet_path is None:
        ratchet_path = REPO_ROOT / "docs" / "governance" / "public_surface_budget_ratchet.json"

    payload = dashboard.to_payload()
    payload["repo_root"] = str(REPO_ROOT)
    payload["generated_at"] = datetime.now(timezone.utc).isoformat()

    ratchet_validation = validate_public_surface_ratchet(payload, ratchet_path)
    payload["ratchet_validation"] = ratchet_validation

    if ns.check_doc is not None:
        rendered = _render_dashboard_markdown(dashboard)
        existing = ns.check_doc.read_text(encoding="utf-8")
        if rendered.strip() != existing.strip():
            print("public_surface_dashboard_doc: stale", file=sys.stderr)
            return 1
        print("public_surface_dashboard_doc: current")

    if ratchet_validation.get("status") != "PASS":
        print("public_surface_dashboard: ratchet validation failed", file=sys.stderr)
        return 1

    if not payload.get("ok", False):
        print("public_surface_dashboard: dashboard not ok (over budget)", file=sys.stderr)
        return 1

    # Top-level status matches other proof JSON artifacts for closure/evidence-bundle validators.
    payload["status"] = "PASS"

    if ns.output_json is not None:
        ns.output_json.parent.mkdir(parents=True, exist_ok=True)
        ns.output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if ns.json:
        print(
            json.dumps(
                {
                    "schema_version": payload.get("schema_version"),
                    "ok": payload.get("ok"),
                    "ratchet_status": ratchet_validation.get("status"),
                    "output_json": str(ns.output_json) if ns.output_json else None,
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
