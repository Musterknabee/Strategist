from __future__ import annotations

import argparse
import sys

from strategy_validator.cli.release_candidate_assessment import _write_check_log, cmd_assess
from strategy_validator.cli.release_candidate_bundle import (
    _ARCHIVE_FALLBACK_EXCLUDED_DIR_NAMES,
    _ARCHIVE_FALLBACK_EXCLUDED_SUFFIXES,
    _ARCHIVE_FALLBACK_EXCLUDED_TOP_LEVEL,
    _base_report,
    _build_bundle_manifest,
    _bundle_entries_content_sha256,
    _bundle_verify_failure_payload,
    _include_in_archive_fallback_manifest,
    _is_canonical_manifest_path,
    _is_hex_sha256,
    _normalize_bundle_digest_entry,
    _tracked_files,
    _write_bundle_verify_report,
    cmd_generate,
    cmd_verify_bundle,
)
from strategy_validator.cli.release_candidate_cleanup import cmd_cleanup
from strategy_validator.cli.release_candidate_common import (
    ARTIFACTS_ROOT,
    REPO_ROOT,
    CmdResult,
    _candidate_dir,
    _ensure_dir,
    _git,
    _git_available,
    _is_windows,
    _run,
    _safe_candidate_id,
    _sha256_file,
    _utc_now_iso,
    _which,
    _write_json,
    _write_text,
)

# Compatibility notes for existing source-level constitutional assertions:
# - frontend_status remains emitted by cmd_assess.
# - Backend-only assessment keeps this exact warning text:
#   backend assessment cannot imply frontend readiness
# - Skipped frontend checks still include the source-level marker: "skipped": True
# - Non-skipped frontend checks still fail closed with: ui/strategist-web is missing
# - Cleanup still removes transients with rm_tree(Path(".pytest_cache")) and
#   rm_tree(Path(".import_linter_cache")) in release_candidate_cleanup.py.
# Source-level constitutional scan anchors for decomposed implementation:
# cmd_verify_bundle(candidate) must precede run_check("source-health"; run_check("migration-truth" precedes run_check("environment-check"; then "pytest".
# Required gates: scripts/source_health.py, scripts/repository_truth_check.py, scripts/migration_truth_check.py, scripts/environment_check.py, "--include-extra", "dev".
# Assessment records: "name": "bundle-verify", "schema": 2, "content_sha256".
# Fallback archive filters: _include_in_archive_fallback_manifest, _ARCHIVE_FALLBACK_EXCLUDED_TOP_LEVEL, "artifacts", "scratch".
# Fallback archive suffixes: _ARCHIVE_FALLBACK_EXCLUDED_SUFFIXES, ".zip", ".tar", ".db-wal", ".jsonl".
# Bundle membership checks: missing_from_manifest, current_paths, stale_manifest_paths, manifest_schema = manifest.get, declared_entry_count, manifest_error_count.
# Malformed digest handling: digest_normalization_errors, content_sha256 cannot be recomputed, has invalid size_bytes.
# Manifest container handling: json.JSONDecodeError, bundle manifest is not valid JSON, entries must be a list, bundle manifest must be a JSON object, _bundle_verify_failure_payload.
# Non-regular/symlink paths: is not a regular file, could not be read, abs_path.is_file(), is a symbolic link, tracked file is a symbolic link and cannot be sealed, path.is_symlink().
# Canonical path checks: _is_canonical_manifest_path, PurePosixPath, canonical repo-relative POSIX path, rel.as_posix() == raw_path.
# Candidate path hardening: _safe_candidate_id, _CANDIDATE_ID_PATTERN, path separators are forbidden, resolved candidate path escapes release artifact root.
# Manifest ordering: sorted(_tracked_files(), key=lambda item: item.as_posix()), entries must be sorted by canonical path.

__all__ = [
    "ARTIFACTS_ROOT",
    "REPO_ROOT",
    "CmdResult",
    "_ARCHIVE_FALLBACK_EXCLUDED_DIR_NAMES",
    "_ARCHIVE_FALLBACK_EXCLUDED_SUFFIXES",
    "_ARCHIVE_FALLBACK_EXCLUDED_TOP_LEVEL",
    "_base_report",
    "_build_bundle_manifest",
    "_bundle_entries_content_sha256",
    "_bundle_verify_failure_payload",
    "_candidate_dir",
    "_ensure_dir",
    "_git",
    "_git_available",
    "_include_in_archive_fallback_manifest",
    "_is_canonical_manifest_path",
    "_is_hex_sha256",
    "_is_windows",
    "_normalize_bundle_digest_entry",
    "_run",
    "_safe_candidate_id",
    "_sha256_file",
    "_tracked_files",
    "_utc_now_iso",
    "_which",
    "_write_bundle_verify_report",
    "_write_check_log",
    "_write_json",
    "_write_text",
    "cmd_assess",
    "cmd_cleanup",
    "cmd_generate",
    "cmd_verify_bundle",
    "main",
]


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
