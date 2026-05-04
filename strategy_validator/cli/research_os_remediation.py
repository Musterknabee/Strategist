"""CLI for Research OS remediation plans."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.application.research_os_remediation_ops import (
    build_and_write_research_os_remediation_plan,
    build_research_os_remediation_plan,
    load_latest_research_os_remediation_plan,
)


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/read Research OS remediation plans.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Build and write a remediation plan from latest Research OS evidence.")
    b.add_argument("--plan-id", default="research-os-remediation-demo")
    b.add_argument("--artifact-root", default="artifacts")
    b.add_argument("--repo-root", default=".")
    b.add_argument("--overwrite", action="store_true")
    b.add_argument("--json", action="store_true")
    p = sub.add_parser("preview", help="Build a remediation plan without writing it.")
    p.add_argument("--plan-id", default="research-os-remediation-preview")
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--json", action="store_true")
    l = sub.add_parser("latest", help="Read the latest remediation plan.")
    l.add_argument("--artifact-root", default="artifacts")
    l.add_argument("--repo-root", default=".")
    l.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    ns = build_parser().parse_args(argv)
    repo_root = Path(ns.repo_root).resolve()
    artifact_root = Path(ns.artifact_root).resolve()
    try:
        if ns.cmd == "build":
            plan, path = build_and_write_research_os_remediation_plan(plan_id=ns.plan_id, repo_root=repo_root, artifact_root=artifact_root, overwrite=ns.overwrite)
            payload = plan.model_dump(mode="json")
            payload["written_path"] = str(path)
            _print(payload)
            return 0 if plan.status.value in {"READY", "RESTRICTED"} else 2
        if ns.cmd == "preview":
            plan = build_research_os_remediation_plan(plan_id=ns.plan_id, repo_root=repo_root, artifact_root=artifact_root)
            _print(plan.model_dump(mode="json"))
            return 0 if plan.status.value in {"READY", "RESTRICTED"} else 2
        if ns.cmd == "latest":
            plan = load_latest_research_os_remediation_plan(repo_root=repo_root, artifact_root=artifact_root)
            if plan is None:
                _print({"ok": False, "status": "NOT_PRESENT", "error": "NO_RESEARCH_OS_REMEDIATION_PLAN"})
                return 1
            _print(plan.model_dump(mode="json"))
            return 0 if plan.status.value in {"READY", "RESTRICTED"} else 2
    except Exception as exc:  # pragma: no cover - CLI guardrail
        _print({"ok": False, "error": type(exc).__name__, "message": str(exc)})
        return 1
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
