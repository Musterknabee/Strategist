#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.research_os_paths import resolve_artifact_output_dir, safe_relative_artifact_path

REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class BranchAuditRow:
    branch_name: str
    scope: str
    classification: str
    merged_into_main: bool
    has_open_pr: bool | None
    has_common_ancestor_with_main: bool
    note: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _run_git(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _local_branches() -> list[str]:
    proc = _run_git(["for-each-ref", "--format=%(refname:short)", "refs/heads"])
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _remote_branches() -> list[str]:
    proc = _run_git(["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"])
    return [
        line.strip()
        for line in proc.stdout.splitlines()
        if line.strip() and line.strip() not in {"origin/HEAD", "origin"}
    ]


def _merged_local_branches() -> set[str]:
    proc = _run_git(["branch", "--merged", "main", "--format=%(refname:short)"])
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def _has_common_ancestor(branch: str, main_ref: str = "origin/main") -> bool:
    proc = _run_git(["merge-base", branch, main_ref])
    return proc.returncode == 0 and bool(proc.stdout.strip())


def _open_pr_map() -> dict[str, bool] | None:
    if shutil.which("gh") is None:
        return None
    proc = subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--json", "headRefName"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return None
    try:
        payload = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError:
        return None
    rows: dict[str, bool] = {}
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                ref = item.get("headRefName")
                if isinstance(ref, str) and ref:
                    rows[ref] = True
    return rows


def classify_branch(
    *,
    branch_name: str,
    merged_into_main: bool,
    has_open_pr: bool | None,
    has_common_ancestor_with_main: bool,
) -> tuple[str, str]:
    if branch_name in {"main", "origin/main"}:
        return "KEEP_MAIN", "main branch is never deletable"
    if has_open_pr is True:
        return "OPEN_PR_DO_NOT_DELETE", "branch has an open pull request"
    if not has_common_ancestor_with_main:
        return "NO_COMMON_ANCESTOR_DO_NOT_DELETE", "branch has no common ancestor with origin/main"
    if has_open_pr is None:
        return "UNKNOWN_DO_NOT_DELETE", "open PR state unknown (gh unavailable or failed)"
    if merged_into_main:
        return "MERGED_SAFE_TO_DELETE", "branch is merged into main and has no open PR"
    return "STALE_NEEDS_MANUAL_REVIEW", "branch is not merged and has no open PR"


def _suggested_delete_commands(rows: list[BranchAuditRow]) -> list[str]:
    commands: list[str] = []
    for row in rows:
        if row.scope == "local" and row.classification == "MERGED_SAFE_TO_DELETE":
            commands.append(f"git branch -d {row.branch_name}")
    return commands


def build_branch_cleanup_audit() -> dict[str, object]:
    locals_ = _local_branches()
    remotes = _remote_branches()
    merged_local = _merged_local_branches()
    open_prs = _open_pr_map()

    rows: list[BranchAuditRow] = []
    for branch in locals_:
        has_open_pr = None if open_prs is None else bool(open_prs.get(branch, False))
        common = _has_common_ancestor(branch)
        classification, note = classify_branch(
            branch_name=branch,
            merged_into_main=branch in merged_local,
            has_open_pr=has_open_pr,
            has_common_ancestor_with_main=common,
        )
        rows.append(
            BranchAuditRow(
                branch_name=branch,
                scope="local",
                classification=classification,
                merged_into_main=branch in merged_local,
                has_open_pr=has_open_pr,
                has_common_ancestor_with_main=common,
                note=note,
            )
        )

    for branch in remotes:
        short = branch.replace("origin/", "", 1)
        has_open_pr = None if open_prs is None else bool(open_prs.get(short, False))
        common = _has_common_ancestor(branch)
        classification, note = classify_branch(
            branch_name=short,
            merged_into_main=False,
            has_open_pr=has_open_pr,
            has_common_ancestor_with_main=common,
        )
        rows.append(
            BranchAuditRow(
                branch_name=short,
                scope="remote",
                classification=classification,
                merged_into_main=False,
                has_open_pr=has_open_pr,
                has_common_ancestor_with_main=common,
                note=note,
            )
        )

    return {
        "schema_version": "branch_cleanup_audit/v1",
        "generated_at_utc": _utc_now(),
        "rows": [asdict(row) for row in sorted(rows, key=lambda item: (item.scope, item.branch_name))],
        "suggested_local_delete_commands": _suggested_delete_commands(rows),
        "safety_notice": "Audit only. No branch deletion performed.",
    }


def _markdown_summary(payload: dict[str, object]) -> str:
    lines = [
        "# Branch Cleanup Audit",
        "",
        f"- Generated at: `{payload.get('generated_at_utc', 'UNKNOWN')}`",
        "- Audit only. No branch deletion performed.",
        "",
        "| Scope | Branch | Classification | Open PR | Merged Into Main | Note |",
        "|---|---|---|---|---|---|",
    ]
    rows = payload.get("rows", [])
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            lines.append(
                f"| {row.get('scope')} | `{row.get('branch_name')}` | `{row.get('classification')}` | {row.get('has_open_pr')} | {row.get('merged_into_main')} | {row.get('note')} |"
            )
    commands = payload.get("suggested_local_delete_commands", [])
    if isinstance(commands, list) and commands:
        lines.extend(["", "## Suggested Local Cleanup Commands", ""])
        for command in commands:
            lines.append(f"- `{command}`")
    return "\n".join(lines) + "\n"


def _resolve_output_path(raw_path: str, *, artifact_root: Path) -> Path:
    raw = Path(raw_path).expanduser()
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        resolved = (artifact_root / safe_relative_artifact_path(raw)).resolve()
    if resolved != artifact_root and artifact_root not in resolved.parents:
        raise ValueError("ARTIFACT_OUTPUT_OUTSIDE_ROOT")
    return resolved


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit local/remote branches for safe manual cleanup.")
    parser.add_argument("--output-json-path", default="")
    parser.add_argument("--output-markdown-path", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        artifact_root = resolve_artifact_output_dir(
            output_dir=None,
            default_subdir=None,
            repo_root=REPO_ROOT,
            create=False,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    payload = build_branch_cleanup_audit()

    if args.output_json_path:
        try:
            out = _resolve_output_path(args.output_json_path, artifact_root=artifact_root)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.output_markdown_path:
        try:
            out_md = _resolve_output_path(args.output_markdown_path, artifact_root=artifact_root)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(_markdown_summary(payload), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"branch_cleanup_audit: rows={len(payload.get('rows', []))}")
        print(payload["safety_notice"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
