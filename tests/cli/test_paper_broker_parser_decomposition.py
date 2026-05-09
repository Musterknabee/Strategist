from __future__ import annotations

import re
from pathlib import Path

from strategy_validator.cli import paper_broker
from strategy_validator.cli_support.paper_broker_parser import build_paper_broker_parser

_PARSER_MODULE_PATHS = [
    Path("strategy_validator/cli_support/paper_broker_order_parser.py"),
    Path("strategy_validator/cli_support/paper_broker_evidence_bundle_parser.py"),
    Path("strategy_validator/cli_support/paper_broker_retention_parser.py"),
    Path("strategy_validator/cli_support/paper_broker_custody_chain_parser.py"),
    Path("strategy_validator/cli_support/paper_broker_custody_renewal_parser.py"),
    Path("strategy_validator/cli_support/paper_broker_custody_archive_parser.py"),
]


def _parser_command_names() -> set[str]:
    parser = build_paper_broker_parser()
    for action in parser._actions:  # argparse keeps subparsers here; stable enough for CLI contract tests.
        choices = getattr(action, "choices", None)
        if choices:
            return set(choices)
    raise AssertionError("paper broker parser has no subcommands")


def _module_command_names(path: Path) -> list[str]:
    return re.findall(r'sub\.add_parser\(\s*"([^"]+)"', path.read_text())


def test_paper_broker_parser_is_structurally_decomposed_from_dispatcher() -> None:
    dispatcher_source = Path("strategy_validator/cli/paper_broker.py").read_text()
    parser_source = Path("strategy_validator/cli_support/paper_broker_parser.py").read_text()

    assert "build_paper_broker_parser()" in dispatcher_source
    assert "sub.add_parser(" not in dispatcher_source
    assert "register_order_parsers(sub)" in parser_source
    assert "register_evidence_bundle_parsers(sub)" in parser_source
    assert "register_retention_parsers(sub)" in parser_source
    assert "register_custody_parsers(sub)" in parser_source
    assert "sub.add_parser(" not in parser_source
    assert len(parser_source.splitlines()) < 80


def test_decomposed_parser_modules_preserve_full_command_contract() -> None:
    parser_commands = _parser_command_names()
    registered_commands: list[str] = []
    for path in _PARSER_MODULE_PATHS:
        source = path.read_text()
        assert "def register_" in source
        assert "build_paper_broker_parser" not in source
        registered_commands.extend(_module_command_names(path))

    assert len(parser_commands) >= 60
    assert set(registered_commands) == parser_commands
    duplicates = sorted({command for command in registered_commands if registered_commands.count(command) > 1})
    assert duplicates == []


def test_custody_parser_is_phase_decomposed_like_custody_handlers() -> None:
    custody_source = Path("strategy_validator/cli_support/paper_broker_custody_parser.py").read_text()

    assert "register_custody_chain_parsers(sub)" in custody_source
    assert "register_custody_renewal_parsers(sub)" in custody_source
    assert "register_custody_archive_parsers(sub)" in custody_source
    assert "sub.add_parser(" not in custody_source
    assert len(custody_source.splitlines()) < 60

    assert len(_module_command_names(Path("strategy_validator/cli_support/paper_broker_custody_chain_parser.py"))) >= 8
    assert len(_module_command_names(Path("strategy_validator/cli_support/paper_broker_custody_renewal_parser.py"))) >= 8
    assert len(_module_command_names(Path("strategy_validator/cli_support/paper_broker_custody_archive_parser.py"))) >= 8


def test_decomposed_parser_preserves_representative_command_contracts() -> None:
    commands = _parser_command_names()

    expected = {
        "status",
        "positions",
        "select-intent",
        "dry-run-order",
        "submit-paper-order",
        "refresh-order-status",
        "seal-evidence-bundle",
        "run-evidence-bundle-rotation",
        "verify-evidence-bundle-retention-custody-attestation",
    }
    assert expected <= commands

    ns = build_paper_broker_parser().parse_args([
        "select-intent",
        "--tracking-id",
        "track-12345678",
        "--symbol",
        "SPY",
        "--qty",
        "2",
        "--side",
        "buy",
    ])
    assert ns.cmd == "select-intent"
    assert ns.tracking_id == "track-12345678"
    assert ns.symbol == "SPY"
    assert ns.qty == 2
    assert ns.side == "buy"


def test_dispatcher_still_uses_decomposed_parser(monkeypatch, tmp_path: Path) -> None:
    calls: list[str] = []
    real_builder = paper_broker.build_paper_broker_parser

    def _wrapped():
        calls.append("called")
        return real_builder()

    monkeypatch.setattr(paper_broker, "build_paper_broker_parser", _wrapped)
    rc = paper_broker.main([
        "select-intent",
        "--tracking-id",
        "track-12345678",
        "--output-root",
        str(tmp_path / "paper_broker"),
    ])

    assert rc == 0
    assert calls == ["called"]
