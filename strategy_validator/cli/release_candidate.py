from __future__ import annotations

import argparse
import sys

from strategy_validator.cli.release_candidate_assessment import cmd_assess
from strategy_validator.cli.release_candidate_bundle import (
    _bundle_entries_content_sha256,
    cmd_generate,
    cmd_verify_bundle,
)
from strategy_validator.cli.release_candidate_cleanup import cmd_cleanup
from strategy_validator.cli.release_candidate_common import CmdResult, _candidate_dir, _safe_candidate_id


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    parser = argparse.ArgumentParser(description="Repo-native release candidate tooling (fail-closed).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_gen = sub.add_parser("generate", help="Generate release candidate packet (report + manifest + handoff).")
    p_gen.add_argument("--candidate", help="Candidate id (defaults to timestamp + short sha).")

    p_assess = sub.add_parser("assess", help="Assess production candidate readiness (fails closed).")
    p_assess.add_argument("--candidate", required=True, help="Candidate id (must already be generated).")
    p_assess.add_argument("--skip-frontend", action="store_true", help="Skip ui/strategist-web validation.")
    p_assess.add_argument("--full-suite", action="store_true", help="Run the complete pytest suite during candidate assessment.")

    p_verify = sub.add_parser("verify-bundle", help="Verify candidate bundle manifest against worktree.")
    p_verify.add_argument("--candidate", required=True, help="Candidate id (must already be generated).")

    p_clean = sub.add_parser("cleanup", help="Remove transient/generated artifacts from the worktree.")
    p_clean.add_argument("--aggressive-frontend", action="store_true", help="Also remove ui build caches and node_modules.")

    args = parser.parse_args(argv)

    if args.cmd == "generate":
        out_dir = cmd_generate(args.candidate)
        print(str(out_dir))
        return 0
    if args.cmd == "assess":
        cmd_assess(args.candidate, skip_frontend=bool(args.skip_frontend), full_suite=bool(args.full_suite))
        print("assessment passed")
        return 0
    if args.cmd == "verify-bundle":
        cmd_verify_bundle(args.candidate)
        print("bundle verification passed")
        return 0
    if args.cmd == "cleanup":
        cmd_cleanup(aggressive_frontend=bool(args.aggressive_frontend))
        print("cleanup complete")
        return 0

    raise SystemExit("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
