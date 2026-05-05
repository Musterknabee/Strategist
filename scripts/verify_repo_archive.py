from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path

# Archive verification is part of the fast release/handoff path and must not
# leave bytecode behind when run from a source archive.
sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.package_repo import UnsafeArchiveOutputError, _safe_repo_root, iter_clean_repo_files
from scripts._path_integrity import absolute_path_preserving_symlink, symlink_components_preserving_path

EXPECTED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXPECTED_FILE_MODE = 0o644
EXPECTED_COMPRESSION_TYPE = zipfile.ZIP_STORED


@dataclass(frozen=True)
class ArchiveVerificationFailure:
    name: str
    detail: str


@dataclass(frozen=True)
class ArchiveVerificationReport:
    schema_version: str
    status: str
    repo_root: str
    archive_path: str
    expected_file_count: int
    archive_file_count: int
    archive_sha256: str | None
    archive_size_bytes: int
    failure_count: int
    warnings: tuple[str, ...]
    blockers: tuple[str, ...]
    failures: tuple[ArchiveVerificationFailure, ...]

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def verify_clean_repo_archive(
    archive_path: str | Path,
    *,
    repo_root: str | Path | None = None,
) -> ArchiveVerificationReport:
    archive = absolute_path_preserving_symlink(archive_path)
    failures: list[ArchiveVerificationFailure] = []
    try:
        root = _safe_repo_root(repo_root) if repo_root is not None else REPO_ROOT
    except UnsafeArchiveOutputError as exc:
        failures.append(ArchiveVerificationFailure(name="repo_root_path_integrity", detail=str(exc)))
        return ArchiveVerificationReport(
            schema_version="repo_archive_verify/v1",
            status="FAIL",
            repo_root=str(absolute_path_preserving_symlink(repo_root)) if repo_root is not None else str(REPO_ROOT),
            archive_path=str(archive),
            expected_file_count=0,
            archive_file_count=0,
            archive_sha256=None,
            archive_size_bytes=0,
            failure_count=len(failures),
            warnings=(),
            blockers=("REPO_ROOT_PATH_INTEGRITY",),
            failures=tuple(failures),
        )

    expected_files = {
        path.relative_to(root).as_posix(): path
        for path in iter_clean_repo_files(root)
    }

    archive_names: list[str] = []
    archive_sha256: str | None = None
    symlinks = symlink_components_preserving_path(archive)
    if symlinks:
        failures.append(
            ArchiveVerificationFailure(
                name="archive_path_integrity",
                detail="archive path uses symlinked components: " + ", ".join(str(item) for item in symlinks),
            )
        )
        return ArchiveVerificationReport(
            schema_version="repo_archive_verify/v1",
            status="FAIL",
            repo_root=str(root),
            archive_path=str(archive),
            expected_file_count=len(expected_files),
            archive_file_count=0,
            archive_sha256=None,
            archive_size_bytes=0,
            failure_count=len(failures),
            warnings=(),
            blockers=("ARCHIVE_PATH_INTEGRITY",),
            failures=tuple(failures),
        )
    if not archive.exists():
        failures.append(ArchiveVerificationFailure(name="archive_exists", detail=f"archive is missing: {archive}"))
        return ArchiveVerificationReport(
            schema_version="repo_archive_verify/v1",
            status="FAIL",
            repo_root=str(root),
            archive_path=str(archive),
            expected_file_count=len(expected_files),
            archive_file_count=0,
            archive_sha256=None,
            archive_size_bytes=0,
            failure_count=len(failures),
            warnings=(),
            blockers=("ARCHIVE_MISSING",),
            failures=tuple(failures),
        )
    if not archive.is_file():
        failures.append(ArchiveVerificationFailure(name="archive_regular_file", detail=f"archive path is not a regular file: {archive}"))
        return ArchiveVerificationReport(
            schema_version="repo_archive_verify/v1",
            status="FAIL",
            repo_root=str(root),
            archive_path=str(archive),
            expected_file_count=len(expected_files),
            archive_file_count=0,
            archive_sha256=None,
            archive_size_bytes=0,
            failure_count=len(failures),
            warnings=(),
            blockers=("ARCHIVE_NOT_REGULAR_FILE",),
            failures=tuple(failures),
        )

    archive_sha256 = _sha256_file(archive)
    archive_size_bytes = archive.stat().st_size
    warnings: list[str] = []
    try:
        with zipfile.ZipFile(archive) as handle:
            infos = handle.infolist()
            archive_names = [info.filename for info in infos]
            if archive_size_bytes > 2 * 1024 * 1024 * 1024:
                warnings.append("ARCHIVE_SIZE_OVER_2GB")
            if archive_names != sorted(archive_names):
                failures.append(ArchiveVerificationFailure(name="entry_order", detail="archive entries are not lexicographically sorted"))
            duplicate_names = sorted({name for name in archive_names if archive_names.count(name) > 1})
            if duplicate_names:
                failures.append(ArchiveVerificationFailure(name="duplicate_entries", detail=", ".join(duplicate_names)))

            expected_names = sorted(expected_files)
            archive_name_set = set(archive_names)
            missing = sorted(set(expected_names) - archive_name_set)
            extra = sorted(archive_name_set - set(expected_names))
            if missing:
                failures.append(ArchiveVerificationFailure(name="missing_entries", detail=", ".join(missing[:20])))
            if extra:
                failures.append(ArchiveVerificationFailure(name="extra_entries", detail=", ".join(extra[:20])))

            for info in infos:
                name = info.filename
                normalized = Path(name)
                if name.startswith("/") or name.startswith("\\") or normalized.is_absolute():
                    failures.append(ArchiveVerificationFailure(name="entry_absolute_path", detail=name))
                    break
                if ".." in normalized.parts:
                    failures.append(ArchiveVerificationFailure(name="entry_path_traversal", detail=name))
                    break
                if info.date_time != EXPECTED_ZIP_TIMESTAMP:
                    failures.append(
                        ArchiveVerificationFailure(
                            name="entry_timestamp",
                            detail=f"{info.filename} timestamp={info.date_time!r}",
                        )
                    )
                    break
                mode = (info.external_attr >> 16) & 0o777
                if mode != EXPECTED_FILE_MODE:
                    failures.append(
                        ArchiveVerificationFailure(
                            name="entry_mode",
                            detail=f"{info.filename} mode={oct(mode)}",
                        )
                    )
                    break
                if info.compress_type != EXPECTED_COMPRESSION_TYPE:
                    failures.append(
                        ArchiveVerificationFailure(
                            name="entry_compression",
                            detail=f"{info.filename} compress_type={info.compress_type}",
                        )
                    )
                    break
                source_path = expected_files.get(info.filename)
                if source_path is None:
                    continue
                source_digest = _sha256_file(source_path)
                archive_digest = _sha256_bytes(handle.read(info.filename))
                if source_digest != archive_digest:
                    failures.append(
                        ArchiveVerificationFailure(
                            name="entry_digest",
                            detail=f"{info.filename} source={source_digest} archive={archive_digest}",
                        )
                    )
                    break
    except zipfile.BadZipFile as exc:
        failures.append(ArchiveVerificationFailure(name="zip_readable", detail=f"bad ZIP file: {exc}"))

    blockers = tuple(sorted({failure.name.upper() for failure in failures}))
    return ArchiveVerificationReport(
        schema_version="repo_archive_verify/v1",
        status="PASS" if not failures else "FAIL",
        repo_root=str(root),
        archive_path=str(archive),
        expected_file_count=len(expected_files),
        archive_file_count=len(archive_names),
        archive_sha256=archive_sha256,
        archive_size_bytes=archive_size_bytes,
        failure_count=len(failures),
        warnings=tuple(sorted(set(warnings))),
        blockers=blockers,
        failures=tuple(failures),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a clean repository ZIP handoff against the current source tree.")
    parser.add_argument("archive", help="ZIP archive produced by scripts/package_repo.py")
    parser.add_argument("--repo-root", default=None, help="Repository root; defaults to this script's parent repository")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    report = verify_clean_repo_archive(args.archive, repo_root=args.repo_root)
    payload = report.to_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"repo_archive_verify: {report.status} archive={report.archive_path} "
            f"expected={report.expected_file_count} actual={report.archive_file_count}"
        )
        if report.archive_sha256:
            print(f"archive_sha256: {report.archive_sha256}")
        for failure in report.failures:
            print(f"{failure.name}: {failure.detail}")
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
