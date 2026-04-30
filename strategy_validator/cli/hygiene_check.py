from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _git_available() -> bool:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0 and result.stdout.strip() == 'true'


REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_ls_files() -> list[str]:
    if not _git_available():
        return []
    out = subprocess.check_output(["git", "ls-files"], cwd=REPO_ROOT, text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def _git_is_ignored(rel_path: Path) -> bool:
    if not _git_available():
        return False
    # git check-ignore exits 0 if ignored, 1 if not ignored
    try:
        subprocess.check_output(
            ["git", "check-ignore", "-q", str(rel_path)],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
        )
        return True
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            return False
        raise


def _is_under(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _matches_suffix(path: Path, suffixes: tuple[str, ...]) -> bool:
    return any(str(path).lower().endswith(sfx) for sfx in suffixes)


def _find_worktree_violations(allow_scratch_logs: bool) -> list[str]:
    """
    Fail-closed, but keep it fast:
    - only checks a small set of high-signal leak patterns
    - skips known large/transient dirs
    """
    skip_dir_names = {
        ".git",
        ".venv",
        "venv",
        "node_modules",
        "dist",
        "build",
        ".eggs",
    }

    forbidden_dir_names_anywhere = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".import_linter_cache",
        ".strategy_validator",
    }

    forbidden_file_suffixes = (".log", ".sqlite3", ".db", ".pyc", ".pyo", ".tsbuildinfo")
    forbidden_file_suffixes_in_repo = (".jsonl",)
    private_key_suffixes = (".pem", ".key")
    private_key_markers = (
        b"-----BEGIN PRIVATE KEY-----",
        b"-----BEGIN RSA PRIVATE KEY-----",
        b"-----BEGIN EC PRIVATE KEY-----",
        b"-----BEGIN OPENSSH PRIVATE KEY-----",
    )

    violations: list[str] = []
    for root, dirs, files in os.walk(REPO_ROOT):
        root_path = Path(root)

        dirs[:] = [d for d in dirs if d not in skip_dir_names]
        for d in list(dirs):
            if d in forbidden_dir_names_anywhere:
                rel_dir = (root_path / d).relative_to(REPO_ROOT)
                if not _git_is_ignored(rel_dir):
                    violations.append(f"forbidden transient directory present: {root_path / d}")

        for f in files:
            p = root_path / f
            rel = p.relative_to(REPO_ROOT)

            if _matches_suffix(rel, forbidden_file_suffixes_in_repo):
                if _is_under(rel, Path("scratch")):
                    continue
                if not _git_is_ignored(rel):
                    violations.append(f"forbidden artifact present: {rel}")
                continue

            if _matches_suffix(rel, forbidden_file_suffixes):
                if allow_scratch_logs and _is_under(rel, Path("scratch")):
                    continue
                if not _git_is_ignored(rel):
                    violations.append(f"forbidden artifact present: {rel}")

            if rel.name.endswith(".egg-info") or ".egg-info" in rel.parts:
                if not _git_is_ignored(rel):
                    violations.append(f"forbidden generated packaging metadata present: {rel}")

            if _matches_suffix(rel, private_key_suffixes):
                try:
                    head = p.read_bytes()[:4096]
                except OSError:
                    head = b""
                if any(marker in head for marker in private_key_markers):
                    if not _git_is_ignored(rel):
                        violations.append(f"forbidden private key material present: {rel}")

    return sorted(set(violations))


def _find_index_violations() -> list[str]:
    tracked = _git_ls_files()

    violations: list[str] = []

    # 1) Tracked transient artifacts should never land in git.
    forbidden_tracked_suffixes = (".log", ".sqlite3", ".db", ".pyc", ".pyo", ".jsonl", ".tsbuildinfo")
    private_key_suffixes = (".pem", ".key")
    private_key_markers = (
        b"-----BEGIN PRIVATE KEY-----",
        b"-----BEGIN RSA PRIVATE KEY-----",
        b"-----BEGIN EC PRIVATE KEY-----",
        b"-----BEGIN OPENSSH PRIVATE KEY-----",
    )
    forbidden_tracked_parts = {
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".import_linter_cache",
        ".strategy_validator",
    }

    for f in tracked:
        p = Path(f)
        if _matches_suffix(p, forbidden_tracked_suffixes):
            violations.append(f"tracked forbidden artifact: {f}")
        if any(part in forbidden_tracked_parts for part in p.parts):
            violations.append(f"tracked forbidden transient path: {f}")
        if ".egg-info" in p.parts or str(p).endswith(".egg-info"):
            violations.append(f"tracked forbidden packaging metadata: {f}")
        if _matches_suffix(p, private_key_suffixes):
            try:
                head = (REPO_ROOT / p).read_bytes()[:4096]
            except OSError:
                head = b""
            if any(marker in head for marker in private_key_markers):
                violations.append(f"tracked forbidden private key material: {f}")

    # 2) Scratch leakage into product paths (keep scratch in one place).
    for f in tracked:
        p = Path(f)
        if "scratch" in p.parts and not _is_under(p, Path("scratch")):
            violations.append(f"tracked scratch leakage outside top-level scratch/: {f}")

    # 3) Duplicate top-level roots via dot-shadowing (e.g. .foo + foo).
    top_dirs = [p for p in REPO_ROOT.iterdir() if p.is_dir()]
    names = {p.name for p in top_dirs}
    for name in sorted(names):
        if name.startswith("."):
            undotted = name[1:]
            if undotted and undotted in names:
                violations.append(f"duplicate root via dot-shadowing: {name!r} and {undotted!r} both exist at repo root")

    return sorted(set(violations))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description="Fail-closed repo hygiene checks (no transient/scratch leakage).")
    parser.add_argument(
        "--allow-scratch-logs",
        action="store_true",
        help="Allow *.log artifacts under top-level scratch/ only (still forbidden elsewhere).",
    )
    args = parser.parse_args(argv)

    git_available = _git_available()
    index_violations = _find_index_violations() if git_available else []
    worktree_violations = _find_worktree_violations(allow_scratch_logs=args.allow_scratch_logs)

    violations = index_violations + worktree_violations
    if violations:
        print("HYGIENE CHECK FAILED")
        for v in violations:
            print(f"- {v}")
        return 2

    if not git_available:
        print('hygiene check passed (limited mode: git metadata unavailable)')
        return 0

    print("hygiene check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

