from __future__ import annotations

import argparse
import json
import os
import sys
import zipfile
import hashlib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

# Clean handoff archives should contain repository source/config/docs/tests, not
# generated release packets, scratch experiments, bytecode caches, local virtual
# environments, or dependency/build outputs.  This mirrors the release-candidate
# no-git manifest fallback but is intentionally exposed as a first-class tool for
# full-repo ZIP handoffs.
EXCLUDED_TOP_LEVEL = {".git", "artifacts", "scratch"}
EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".import_linter_cache",
    ".strategy_validator",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip", ".tar", ".gz", ".tgz", ".sqlite", ".sqlite3", ".db", ".db-wal", ".db-shm", ".log", ".jsonl"}


class UnsafeArchiveOutputError(ValueError):
    """Raised when an archive output path would be included in future archives."""


@dataclass(frozen=True)
class PackageRepoReport:
    schema_version: str
    status: str
    repo_root: str
    output_path: str | None
    generated_at: str
    included_file_count: int
    skipped_file_count: int
    skipped_generated_roots: tuple[str, ...]
    archive_sha256: str | None = None

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalise(path: Path) -> str:
    return path.as_posix()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def include_in_clean_repo_archive(path: Path, *, repo_root: Path) -> bool:
    try:
        rel = path.relative_to(repo_root)
    except ValueError:
        return False
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in EXCLUDED_TOP_LEVEL:
        return False
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return False
    if path.suffix in EXCLUDED_SUFFIXES:
        return False
    if path.is_symlink():
        return False
    return path.is_file()


def _would_include_output_path(output: Path, *, repo_root: Path) -> bool:
    """Return true if ``output`` would become an archive member by name.

    ``include_in_clean_repo_archive`` intentionally requires an existing file,
    but archive outputs are validated before they are written.  This name-based
    guard prevents a caller from writing ``repo/handoff.bin`` and making that
    generated file part of the next clean archive or verification pass.
    """
    try:
        rel = output.resolve().relative_to(repo_root)
    except ValueError:
        return False
    parts = rel.parts
    if not parts:
        return False
    if parts[0] in EXCLUDED_TOP_LEVEL:
        return False
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return False
    if output.suffix in EXCLUDED_SUFFIXES:
        return False
    return True


def _validate_output_path(output: Path | None, *, repo_root: Path) -> None:
    if output is None:
        return
    if _would_include_output_path(output, repo_root=repo_root):
        rel = output.resolve().relative_to(repo_root).as_posix()
        raise UnsafeArchiveOutputError(
            f"archive output would be included in future clean archives: {rel}. "
            "Write outside the repository or use an excluded archive suffix such as .zip."
        )


def _iter_paths_pruned(base: Path, *, repo_root: Path) -> Iterable[Path]:
    """Yield paths under ``base`` while pruning excluded directories early.

    ``Path.rglob`` still descends into excluded generated trees before the
    later include filter rejects them.  That is acceptable for tiny repos but
    brittle for source-archive handoffs that may contain bulky local artifacts.
    This walker keeps the clean archive path deterministic while avoiding work
    in directories that can never be included.
    """
    if base.is_file():
        yield base
        return

    for current, dirnames, filenames in os.walk(base):
        current_path = Path(current)
        try:
            rel_parts = current_path.relative_to(repo_root).parts
        except ValueError:
            rel_parts = ()
        if rel_parts and rel_parts[0] in EXCLUDED_TOP_LEVEL:
            dirnames[:] = []
            continue
        dirnames[:] = sorted(
            dirname
            for dirname in dirnames
            if dirname not in EXCLUDED_DIR_NAMES
            and not ((current_path == repo_root) and dirname in EXCLUDED_TOP_LEVEL)
        )
        for filename in sorted(filenames):
            yield current_path / filename


def iter_clean_repo_files(repo_root: str | Path, *, roots: Sequence[str] | None = None) -> Iterable[Path]:
    root = Path(repo_root).resolve()
    raw_roots = roots or (".",)
    seen: set[Path] = set()
    for raw in raw_roots:
        base = (root / raw).resolve()
        if not base.exists():
            continue
        for path in _iter_paths_pruned(base, repo_root=root):
            if path in seen:
                continue
            if include_in_clean_repo_archive(path, repo_root=root):
                seen.add(path)
                yield path


def _count_skipped(repo_root: Path) -> tuple[int, tuple[str, ...]]:
    skipped = 0
    generated_roots: list[str] = []
    for top_level in sorted(EXCLUDED_TOP_LEVEL):
        candidate = repo_root / top_level
        if candidate.exists():
            generated_roots.append(top_level)
    for path in _iter_paths_pruned(repo_root, repo_root=repo_root):
        if path.is_file() and not include_in_clean_repo_archive(path, repo_root=repo_root):
            skipped += 1
    return skipped, tuple(generated_roots)


def build_clean_repo_zip(
    *,
    repo_root: str | Path | None = None,
    output_path: str | Path | None = None,
    roots: Sequence[str] | None = None,
) -> PackageRepoReport:
    root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[1]
    output = Path(output_path).resolve() if output_path is not None else None
    _validate_output_path(output, repo_root=root)
    files = tuple(sorted(iter_clean_repo_files(root, roots=roots), key=lambda item: item.relative_to(root).as_posix()))
    skipped_count, generated_roots = _count_skipped(root)

    archive_sha256: str | None = None
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED) as archive:
            for path in files:
                rel = _normalise(path.relative_to(root))
                info = zipfile.ZipInfo(rel)
                # Keep repository handoff archives deterministic enough for
                # operator comparison: sorted entries, fixed ZIP timestamp, and
                # normalized regular-file permissions. The archive is intentionally stored rather than deflated so the build smoke remains deterministic and fast in constrained runners.
                info.date_time = (1980, 1, 1, 0, 0, 0)
                info.external_attr = 0o644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_STORED)
        archive_sha256 = _sha256_file(output)

    return PackageRepoReport(
        schema_version="clean_repo_archive/v2",
        status="PASS",
        repo_root=str(root),
        output_path=str(output) if output is not None else None,
        generated_at=_utc_now_iso(),
        included_file_count=len(files),
        skipped_file_count=skipped_count,
        skipped_generated_roots=generated_roots,
        archive_sha256=archive_sha256,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or validate a clean repository ZIP handoff archive.")
    parser.add_argument("--repo-root", default=None, help="Repository root; defaults to this script's parent repository")
    parser.add_argument("--output", default=None, help="ZIP output path. Omit with --check for a dry-run report.")
    parser.add_argument("--check", action="store_true", help="Dry-run archive selection without writing a ZIP")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    if not args.check and not args.output:
        parser.error("provide --output or --check")

    try:
        report = build_clean_repo_zip(repo_root=args.repo_root, output_path=None if args.check else args.output)
    except UnsafeArchiveOutputError as exc:
        payload = {
            "schema_version": "clean_repo_archive/v2",
            "status": "FAIL",
            "repo_root": str(Path(args.repo_root).resolve()) if args.repo_root else str(Path(__file__).resolve().parents[1]),
            "output_path": str(Path(args.output).resolve()) if args.output else None,
            "generated_at": _utc_now_iso(),
            "included_file_count": 0,
            "skipped_file_count": 0,
            "skipped_generated_roots": [],
            "archive_sha256": None,
            "error": str(exc),
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print(f"package_repo: FAIL {exc}")
        return 2
    payload = report.to_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        target = payload["output_path"] or "dry-run"
        print(
            f"package_repo: {report.status} target={target} "
            f"included={report.included_file_count} skipped={report.skipped_file_count}"
        )
        if report.archive_sha256:
            print(f"archive_sha256: {report.archive_sha256}")
        if report.skipped_generated_roots:
            print("skipped_generated_roots: " + ", ".join(report.skipped_generated_roots))
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
