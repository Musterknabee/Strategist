from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.public_surface import OPERATOR_COMMAND_EXEMPTIONS, OPERATOR_COMMAND_REGISTRY


ROOT = Path(__file__).resolve().parents[2]


def _project_scripts() -> dict[str, str]:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    scripts: dict[str, str] = {}
    in_scripts = False
    for raw in text.splitlines():
        line = raw.strip()
        if line == "[project.scripts]":
            in_scripts = True
            continue
        if in_scripts and line.startswith("[") and line.endswith("]"):
            break
        if in_scripts and "=" in line:
            left, right = line.split("=", 1)
            scripts[left.strip()] = right.strip()
    return scripts


def test_operator_registry_or_exemption_covers_all_console_scripts() -> None:
    scripts = _project_scripts()
    operator_scripts = sorted(name for name in scripts if name.startswith("strategy-validator-"))
    missing = [name for name in operator_scripts if name not in OPERATOR_COMMAND_REGISTRY and name not in OPERATOR_COMMAND_EXEMPTIONS]
    assert missing == []


def test_operator_registry_and_exemptions_have_no_stale_names() -> None:
    scripts = _project_scripts()
    stale_registry = sorted(name for name in OPERATOR_COMMAND_REGISTRY if name not in scripts)
    stale_exemptions = sorted(name for name in OPERATOR_COMMAND_EXEMPTIONS if name not in scripts)
    assert stale_registry == []
    assert stale_exemptions == []


def test_operator_commands_doc_mentions_registry_entries() -> None:
    doc = (ROOT / "docs" / "operator" / "OPERATOR_EASE_OF_USE_COMMANDS.md").read_text(encoding="utf-8")
    missing = [name for name in OPERATOR_COMMAND_REGISTRY if name not in doc]
    assert missing == []
