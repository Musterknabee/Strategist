"""CLI for read-only evidence bundle index discovery."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.evidence_bundle_index import build_evidence_bundle_index
from strategy_validator.application.research_os_paths import resolve_artifact_output_dir, resolve_artifact_root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a read-only local evidence bundle index.")
    parser.add_argument("--artifact-root", default="", help="Artifact root override (default: governed root)")
    parser.add_argument("--output-path", default="", help="Optional JSON output path under artifact root")
    parser.add_argument("--include-digests", action="store_true", help="Compute SHA-256 for discovered files")
    parser.add_argument("--json", action="store_true", help="Emit JSON to stdout")
    args = parser.parse_args(argv)

    repo_root = Path.cwd().resolve()
    if args.artifact_root:
        root_input = Path(args.artifact_root).expanduser()
        artifact_root = root_input.resolve() if root_input.is_absolute() else (repo_root / root_input).resolve()
    else:
        artifact_root = resolve_artifact_root(repo_root)

    payload = build_evidence_bundle_index(
        repo_root=repo_root,
        artifact_root=artifact_root,
        include_digests=args.include_digests,
    )

    if args.output_path:
        try:
            output_root = resolve_artifact_output_dir(output_dir=None, default_subdir=None, repo_root=repo_root, create=False)
            out_raw = Path(args.output_path).expanduser()
            output_path = out_raw.resolve() if out_raw.is_absolute() else (output_root / out_raw).resolve()
            if output_path != output_root and output_root not in output_path.parents:
                raise ValueError("ARTIFACT_OUTPUT_OUTSIDE_ROOT")
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            "evidence_bundle_index: "
            f"entries={len(payload.get('entries', []))} "
            f"warnings={len(payload.get('warnings', []))} "
            f"blockers={len(payload.get('blockers', []))}"
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
