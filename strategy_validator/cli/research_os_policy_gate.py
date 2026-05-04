"""CLI for Research OS policy gate reports."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.research_os_policy_gate_ops import (
    build_and_write_research_os_policy_gate_report,
    build_research_os_policy_gate_report,
    load_latest_research_os_policy_gate_report,
)


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/read Research OS policy gate evidence.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="Build a policy gate report from latest evidence artifacts.")
    b.add_argument("--gate-id", default="research-os-policy-gate-demo")
    b.add_argument("--artifact-root", default="artifacts")
    b.add_argument("--repo-root", default=".")
    b.add_argument("--overwrite", action="store_true")
    b.add_argument("--json", action="store_true")
    p = sub.add_parser("preview", help="Build and print a policy gate report without writing it.")
    p.add_argument("--gate-id", default="research-os-policy-gate-preview")
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--json", action="store_true")
    l = sub.add_parser("latest", help="Read the latest policy gate report.")
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
            report, path = build_and_write_research_os_policy_gate_report(
                gate_id=ns.gate_id,
                repo_root=repo_root,
                artifact_root=artifact_root,
                overwrite=ns.overwrite,
            )
            payload = report.model_dump(mode="json")
            payload["written_path"] = str(path)
            _print(payload)
            return 0 if report.decision.value in {"PASS", "WARN"} else 2
        if ns.cmd == "preview":
            report = build_research_os_policy_gate_report(gate_id=ns.gate_id, repo_root=repo_root, artifact_root=artifact_root)
            _print(report.model_dump(mode="json"))
            return 0 if report.decision.value in {"PASS", "WARN"} else 2
        if ns.cmd == "latest":
            report = load_latest_research_os_policy_gate_report(repo_root=repo_root, artifact_root=artifact_root)
            if report is None:
                _print({"ok": False, "status": "NOT_PRESENT", "error": "NO_RESEARCH_OS_POLICY_GATE_REPORT"})
                return 1
            _print(report.model_dump(mode="json"))
            return 0 if report.decision.value in {"PASS", "WARN"} else 2
    except Exception as exc:  # pragma: no cover - CLI guardrail
        _print({"ok": False, "error": type(exc).__name__, "message": str(exc)})
        return 1
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
