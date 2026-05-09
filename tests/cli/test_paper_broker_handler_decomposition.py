from __future__ import annotations

import re
from pathlib import Path
from types import SimpleNamespace

from strategy_validator.cli import paper_broker
from strategy_validator.cli_support import (
    paper_broker_custody_archive_commands,
    paper_broker_custody_chain_commands,
    paper_broker_custody_commands,
    paper_broker_custody_renewal_commands,
    paper_broker_evidence_bundle_commands,
    paper_broker_order_commands,
    paper_broker_retention_commands,
)
from strategy_validator.cli_support.paper_broker_parser import build_paper_broker_parser


_PUBLIC_HANDLER_MODULE_PATHS = [
    Path("strategy_validator/cli_support/paper_broker_order_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_evidence_bundle_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_retention_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_custody_commands.py"),
]

_ORDER_PHASE_HANDLER_MODULE_PATHS = [
    Path("strategy_validator/cli_support/paper_broker_order_read_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_order_lifecycle_commands.py"),
]

_EVIDENCE_BUNDLE_PHASE_HANDLER_MODULE_PATHS = [
    Path("strategy_validator/cli_support/paper_broker_evidence_bundle_seal_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_evidence_bundle_rotation_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_evidence_bundle_attestation_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_evidence_bundle_closure_export_commands.py"),
]

_RETENTION_PHASE_HANDLER_MODULE_PATHS = [
    Path("strategy_validator/cli_support/paper_broker_retention_receipt_signoff_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_retention_handoff_commands.py"),
]

_CUSTODY_PHASE_HANDLER_MODULE_PATHS = [
    Path("strategy_validator/cli_support/paper_broker_custody_chain_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_custody_renewal_commands.py"),
    Path("strategy_validator/cli_support/paper_broker_custody_archive_commands.py"),
]

_PHASE_HANDLER_MODULE_PATHS = [
    *_ORDER_PHASE_HANDLER_MODULE_PATHS,
    *_EVIDENCE_BUNDLE_PHASE_HANDLER_MODULE_PATHS,
    *_RETENTION_PHASE_HANDLER_MODULE_PATHS,
    *_CUSTODY_PHASE_HANDLER_MODULE_PATHS,
]

_HANDLER_MODULE_PATHS = _PHASE_HANDLER_MODULE_PATHS


def _parser_command_names() -> set[str]:
    parser = build_paper_broker_parser()
    for action in parser._actions:  # argparse exposes subparser choices here.
        choices = getattr(action, "choices", None)
        if choices:
            return set(choices)
    raise AssertionError("paper broker parser has no subcommands")


def _handler_command_names(path: Path) -> list[str]:
    return re.findall(r'if ns\.cmd == "([^"]+)"', path.read_text())


def test_paper_broker_dispatcher_is_thin_after_handler_decomposition() -> None:
    dispatcher_source = Path("strategy_validator/cli/paper_broker.py").read_text()

    assert "sub.add_parser(" not in dispatcher_source
    assert "if ns.cmd ==" not in dispatcher_source
    assert "paper_broker_order_commands" in dispatcher_source
    assert "paper_broker_evidence_bundle_commands" in dispatcher_source
    assert "paper_broker_retention_commands" in dispatcher_source
    assert "paper_broker_custody_commands" in dispatcher_source
    assert len(dispatcher_source.splitlines()) < 250


def test_every_parser_command_is_owned_by_exactly_one_handler() -> None:
    parser_commands = _parser_command_names()
    owned_commands: list[str] = []
    for path in _HANDLER_MODULE_PATHS:
        owned_commands.extend(_handler_command_names(path))

    assert set(owned_commands) == parser_commands
    duplicates = sorted({command for command in owned_commands if owned_commands.count(command) > 1})
    assert duplicates == []


def test_handler_modules_preserve_legacy_monkeypatch_surface() -> None:
    for path in [*_PUBLIC_HANDLER_MODULE_PATHS, *_PHASE_HANDLER_MODULE_PATHS]:
        source = path.read_text()
        assert "from strategy_validator.cli import paper_broker as _paper_broker" in source
        assert "_paper_broker" in source
        assert "sub.add_parser(" not in source


def test_paper_broker_custody_handler_is_phase_decomposed() -> None:
    custody_source = Path("strategy_validator/cli_support/paper_broker_custody_commands.py").read_text()

    assert "paper_broker_custody_chain_commands" in custody_source
    assert "paper_broker_custody_renewal_commands" in custody_source
    assert "paper_broker_custody_archive_commands" in custody_source
    assert "if ns.cmd ==" not in custody_source
    assert len(custody_source.splitlines()) < 80

    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_custody_chain_commands.py"))) >= 8
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_custody_renewal_commands.py"))) >= 8
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_custody_archive_commands.py"))) >= 8


def test_paper_broker_non_custody_handlers_are_phase_decomposed() -> None:
    expected_modules = {
        Path("strategy_validator/cli_support/paper_broker_order_commands.py"): [
            "paper_broker_order_read_commands",
            "paper_broker_order_lifecycle_commands",
        ],
        Path("strategy_validator/cli_support/paper_broker_evidence_bundle_commands.py"): [
            "paper_broker_evidence_bundle_seal_commands",
            "paper_broker_evidence_bundle_rotation_commands",
            "paper_broker_evidence_bundle_attestation_commands",
            "paper_broker_evidence_bundle_closure_export_commands",
        ],
        Path("strategy_validator/cli_support/paper_broker_retention_commands.py"): [
            "paper_broker_retention_receipt_signoff_commands",
            "paper_broker_retention_handoff_commands",
        ],
    }

    for path, module_names in expected_modules.items():
        source = path.read_text()
        for module_name in module_names:
            assert module_name in source
        assert "if ns.cmd ==" not in source
        assert len(source.splitlines()) < 80

    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_order_read_commands.py"))) >= 3
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_order_lifecycle_commands.py"))) >= 5
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_evidence_bundle_seal_commands.py"))) >= 3
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_evidence_bundle_rotation_commands.py"))) >= 2
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_evidence_bundle_attestation_commands.py"))) >= 2
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_evidence_bundle_closure_export_commands.py"))) >= 4
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_retention_receipt_signoff_commands.py"))) >= 4
    assert len(_handler_command_names(Path("strategy_validator/cli_support/paper_broker_retention_handoff_commands.py"))) >= 4


def test_main_short_circuits_through_decomposed_handler_families(monkeypatch) -> None:
    calls: list[str] = []

    def _order_handle(ns: SimpleNamespace, env: dict[str, str]) -> int | None:
        calls.append(f"order:{ns.cmd}")
        return None

    def _evidence_handle(ns: SimpleNamespace, env: dict[str, str]) -> int | None:
        calls.append(f"evidence:{ns.cmd}")
        return 17

    def _unexpected_handle(ns: SimpleNamespace, env: dict[str, str]) -> int | None:
        calls.append(f"unexpected:{ns.cmd}")
        return 99

    monkeypatch.setattr(paper_broker_order_commands, "handle", _order_handle)
    monkeypatch.setattr(paper_broker_evidence_bundle_commands, "handle", _evidence_handle)
    monkeypatch.setattr(paper_broker_retention_commands, "handle", _unexpected_handle)
    monkeypatch.setattr(paper_broker_custody_commands, "handle", _unexpected_handle)

    assert paper_broker.main(["status", "--json"]) == 17
    assert calls == ["order:status", "evidence:status"]
