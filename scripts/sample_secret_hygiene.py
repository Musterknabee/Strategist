"""Scan committed deployment/env samples and operator-facing docs for plausible secrets.

Fail-closed for public-repo hygiene: Alpaca-style paper key IDs, long
random-looking provider secrets, opaque ``STRATEGY_VALIDATOR_*_API_TOKEN``
values, and PEM/private-key blobs must not appear in tracked samples, docs, or
script snippets unless they are clearly impossible placeholders (CHANGEME /
NOT_REAL / etc.) or live under ``tests/**/fixtures/**`` (embedded fixture
material only).
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Lines like ``KEY=value`` or ``# KEY=value`` (commented examples in samples).
_ENV_ASSIGN_RE = re.compile(r"^\s*(?:#\s*)?([A-Z][A-Z0-9_]*)\s*=\s*(.*?)\s*$")

_ALPACA_KEY_NAMES = frozenset({"ALPACA_API_KEY", "APCA_API_KEY_ID"})
_ALPACA_SECRET_NAMES = frozenset({"ALPACA_API_SECRET", "APCA_API_SECRET_KEY"})

# Committed samples must never ship opaque operator tokens; real values belong in deployment.env (gitignored).
_DEPLOYMENT_SAMPLE_TOKEN_KEYS = frozenset(
    {
        "STRATEGY_VALIDATOR_API_TOKEN",
        "STRATEGY_VALIDATOR_RESEARCH_API_TOKEN",
    }
)

# Alpaca paper/live API key IDs are ``PK`` + alphanumeric (length varies).
_ALPACA_KEY_ID_RE = re.compile(r"^PK[A-Z0-9]{10,}$")

# Long opaque ASCII secrets (Alpaca secrets are typically 40 chars, alphanumeric).
_OPAQUE_SECRET_RE = re.compile(r"^[A-Za-z0-9]{28,}$")

_PLACEHOLDER_MARKERS = (
    "CHANGEME",
    "REPLACE",
    "NOT_REAL",
    "NOT_A_REAL",
    "INVALID",
    "PLACEHOLDER",
    "EXAMPLE",
    "DUMMY",
    "FAKE",
    "YOUR_",
    "TODO",
)

# Assembled from hex so this gate module does not embed literal PEM headers (avoids self-match).
_PRIVATE_KEY_MARKERS = tuple(
    bytes.fromhex(raw).decode("ascii")
    for raw in (
        "2d2d2d2d2d424547494e205253412050524956415445204b45592d2d2d2d2d",
        "2d2d2d2d2d424547494e204f50454e5353482050524956415445204b45592d2d2d2d2d",
        "2d2d2d2d2d424547494e2045432050524956415445204b45592d2d2d2d2d",
        "2d2d2d2d2d424547494e2050524956415445204b45592d2d2d2d2d",
    )
)

_SKIP_WALK_DIR_NAMES = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "node_modules",
        ".next",
        "dist",
        "build",
        ".venv",
        "venv",
    }
)


def _strip_inline_comment(value: str) -> str:
    if " #" in value:
        value = value.split(" #", 1)[0].strip()
    return value.strip().strip("'\"")


def _is_explicit_placeholder(value: str) -> bool:
    u = value.upper()
    return any(marker in u for marker in _PLACEHOLDER_MARKERS)


def evaluate_env_assignment_line(*, key: str, val: str, lineno: int, label: str) -> tuple[str, ...]:
    """Apply env-line secret heuristics; return violation strings."""
    if not val:
        return ()
    ku = key.upper()
    if ku in _ALPACA_KEY_NAMES:
        if _ALPACA_KEY_ID_RE.fullmatch(val) and not _is_explicit_placeholder(val):
            return (f"{label}:{lineno}: {key} looks like a real Alpaca-style API key id",)
    if ku in _ALPACA_SECRET_NAMES:
        if _OPAQUE_SECRET_RE.fullmatch(val) and not _is_explicit_placeholder(val):
            return (f"{label}:{lineno}: {key} looks like a real provider secret material",)
    if ku in _DEPLOYMENT_SAMPLE_TOKEN_KEYS:
        if _OPAQUE_SECRET_RE.fullmatch(val) and not _is_explicit_placeholder(val):
            return (
                f"{label}:{lineno}: {key} looks like a committed opaque API token "
                "(use an impossible CHANGEME/NOT_REAL placeholder)",
            )
    return ()


def scan_sample_env_text(text: str, *, label: str = "deployment.env.sample") -> tuple[str, ...]:
    """Scan env sample text; return human-readable violation strings."""
    violations: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if (not stripped) or (stripped.startswith("#") and "=" not in stripped):
            continue
        m = _ENV_ASSIGN_RE.match(line)
        if not m:
            continue
        key, raw_val = m.group(1), m.group(2)
        val = _strip_inline_comment(raw_val)
        violations.extend(evaluate_env_assignment_line(key=key, val=val, lineno=lineno, label=label))
    return tuple(violations)


def scan_private_key_material(text: str, *, label: str) -> tuple[str, ...]:
    """Flag PEM / private-key blobs in committed operator-facing text."""
    violations: list[str] = []
    for marker in _PRIVATE_KEY_MARKERS:
        if marker in text:
            short = marker.removeprefix("-----BEGIN ").removesuffix("-----").strip()
            violations.append(f"{label}: contains private key material ({short})")
    return tuple(violations)


def _is_allowed_private_key_fixture_path(path: Path, repo_root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return False
    parts = rel.parts
    if not parts or parts[0] != "tests":
        return False
    return any(p in {"fixtures", "fixture_data", "golden", "_fixtures"} for p in parts)


def _should_prune_walk_dir(dir_path: Path, repo_root: Path) -> bool:
    name = dir_path.name
    if name in _SKIP_WALK_DIR_NAMES:
        return True
    try:
        rel = dir_path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return True
    if len(rel.parts) >= 2 and rel.parts[0] == "docs" and rel.parts[1] == "artifacts":
        return True
    return False


def _iter_markdown_under_docs(repo_root: Path) -> tuple[Path, ...]:
    docs_root = repo_root / "docs"
    if not docs_root.is_dir() or docs_root.is_symlink():
        return ()
    paths: list[Path] = []
    for current, dirnames, filenames in os.walk(docs_root):
        current_path = Path(current)
        if _should_prune_walk_dir(current_path, repo_root):
            dirnames[:] = []
            continue
        dirnames[:] = sorted(
            d for d in dirnames if not (current_path / d).is_symlink() and d not in _SKIP_WALK_DIR_NAMES
        )
        for filename in sorted(filenames):
            path = current_path / filename
            if path.suffix == ".md" and path.is_file() and not path.is_symlink():
                paths.append(path)
    return tuple(paths)


def _iter_python_under_scripts(repo_root: Path) -> tuple[Path, ...]:
    scripts_root = repo_root / "scripts"
    if not scripts_root.is_dir() or scripts_root.is_symlink():
        return ()
    paths: list[Path] = []
    for current, dirnames, filenames in os.walk(scripts_root):
        current_path = Path(current)
        dirnames[:] = sorted(
            d for d in dirnames if not (current_path / d).is_symlink() and d not in _SKIP_WALK_DIR_NAMES
        )
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = current_path / filename
            if path.is_file() and not path.is_symlink():
                paths.append(path)
    return tuple(paths)


def _iter_env_sample_files(repo_root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for current, dirnames, filenames in os.walk(repo_root):
        current_path = Path(current)
        if _should_prune_walk_dir(current_path, repo_root):
            dirnames[:] = []
            continue
        dirnames[:] = sorted(
            d for d in dirnames if not (current_path / d).is_symlink() and d not in _SKIP_WALK_DIR_NAMES
        )
        for filename in sorted(filenames):
            if not filename.endswith(".env.sample"):
                continue
            path = current_path / filename
            if path.is_file() and not path.is_symlink():
                paths.append(path)
    return tuple(sorted(paths))


def _scan_text_payload(*, text: str, path: Path, repo_root: Path) -> tuple[str, ...]:
    label = path.resolve().relative_to(repo_root.resolve()).as_posix()
    violations = list(scan_sample_env_text(text, label=label))
    if not _is_allowed_private_key_fixture_path(path, repo_root):
        violations.extend(scan_private_key_material(text, label=label))
    return tuple(violations)


def collect_sample_secret_hygiene_violations(repo_root: Path) -> tuple[str, ...]:
    """Return human-readable violation strings (empty tuple when clean)."""
    root = repo_root.resolve()
    sample = root / "deployment.env.sample"
    if not sample.exists():
        return ("deployment.env.sample is missing",)

    violations: list[str] = []

    for path in _iter_env_sample_files(root):
        text = path.read_text(encoding="utf-8")
        violations.extend(_scan_text_payload(text=text, path=path, repo_root=root))

    for path in _iter_markdown_under_docs(root):
        text = path.read_text(encoding="utf-8")
        violations.extend(_scan_text_payload(text=text, path=path, repo_root=root))

    for path in _iter_python_under_scripts(root):
        text = path.read_text(encoding="utf-8")
        violations.extend(_scan_text_payload(text=text, path=path, repo_root=root))

    return tuple(violations)


__all__ = [
    "collect_sample_secret_hygiene_violations",
    "evaluate_env_assignment_line",
    "scan_private_key_material",
    "scan_sample_env_text",
]
