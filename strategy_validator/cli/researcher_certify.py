"""Certification-only fixture: write deterministic researcher_certification + paper evidence artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_certification_tree(artifact_root: Path) -> None:
    certification_path = artifact_root / "researcher_certification" / "latest" / "researcher_certification_report.json"
    certification_path.parent.mkdir(parents=True, exist_ok=True)
    certification_path.write_text(
        json.dumps(
            {
                "schema_version": "researcher_certification_report/v1",
                "decision": "CERTIFIED",
                "blockers": [],
                "checks": {
                    "source_policy_present": "PASS",
                    "research_capsule_verified": "PASS",
                    "paper_evidence_consequences_complete": "PASS",
                    "paper_pass_does_not_imply_live_readiness": "PASS",
                    "no_live_broker_authority": "PASS",
                },
                "no_live_broker_authority": True,
                "read_plane_only": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    release_path = artifact_root / "research_os_release_readiness" / "latest" / "research_os_release_readiness_report.json"
    release_path.parent.mkdir(parents=True, exist_ok=True)
    release_path.write_text(
        json.dumps({"schema_version": "research_os_release_readiness_report/v1", "status": "PASS"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paper_path = artifact_root / "paper_evidence" / "latest" / "candidate_paper_evidence_evaluation.json"
    paper_path.parent.mkdir(parents=True, exist_ok=True)
    paper_path.write_text(
        json.dumps({"decision": "PAPER_EVIDENCE_PASSED", "schema_version": "paper_evidence_evaluation/v1"}, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--write", action="store_true", help="Materialise fixture artifacts under artifact-root.")
    parser.add_argument("--json", action="store_true", help="Emit a short JSON line to stdout.")
    ns = parser.parse_args(argv)
    root = ns.artifact_root.resolve()
    if not ns.write:
        print("researcher_certify: --write is required for certification fixture materialisation", file=sys.stderr)
        return 2
    _write_certification_tree(root)
    if ns.json:
        print(
            json.dumps(
                {
                    "schema_version": "researcher_certify_fixture_cli/v1",
                    "status": "PASS",
                    "artifact_root": str(root),
                    "repo_root": str(REPO_ROOT),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
