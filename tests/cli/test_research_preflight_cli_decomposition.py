from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "strategy_validator" / "cli"


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_research_preflight_entrypoint_is_thin_facade() -> None:
    facade = CLI / "research_preflight.py"
    source = facade.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 90
    assert _function_names(facade) == {"main"}
    assert "add_argument" not in source
    assert "run_semantic_research_preflight" not in source


def test_research_preflight_parser_and_dispatch_are_separated() -> None:
    parser_source = (CLI / "research_preflight_parser.py").read_text(encoding="utf-8")
    dispatch_source = (CLI / "research_preflight_dispatch.py").read_text(encoding="utf-8")

    assert _function_names(CLI / "research_preflight_parser.py") == {"build_research_preflight_parser"}
    assert "add_argument" in parser_source
    assert "parse_args" not in parser_source

    assert _function_names(CLI / "research_preflight_dispatch.py") == {"dispatch_research_preflight"}
    assert "parse_args" not in dispatch_source
    assert "run_semantic_research_preflight" in dispatch_source


def test_research_preflight_mode_families_own_expected_modes() -> None:
    assert {
        "_run_integrity_mode",
        "_run_bundle_release_index_verification_mode",
    }.issubset(_function_names(CLI / "research_preflight_integrity_modes.py"))
    assert {
        "_run_release_capsule_mode",
        "_run_release_decision_record_mode",
        "_run_release_handoff_certificate_evidence_summary_mode",
    }.issubset(_function_names(CLI / "research_preflight_release_modes.py"))
    assert {
        "_run_validator_handoff_packet_mode",
        "_run_validator_ingress_acceptance_ledger_summary_mode",
        "_run_validator_submission_readiness_summary_mode",
    }.issubset(_function_names(CLI / "research_preflight_validator_modes.py"))
    assert _function_names(CLI / "research_preflight_validation.py") == {"_require_preflight_args"}


def test_research_preflight_legacy_private_import_surface_is_preserved() -> None:
    from strategy_validator.cli.research_preflight import (  # noqa: PLC0415
        _read_json,
        _require_preflight_args,
        _run_integrity_mode,
        _run_release_capsule_mode,
        _run_validator_submission_packet_mode,
        _write_json,
        build_research_preflight_parser,
        dispatch_research_preflight,
        main,
    )

    assert callable(main)
    assert callable(build_research_preflight_parser)
    assert callable(dispatch_research_preflight)
    assert callable(_read_json)
    assert callable(_write_json)
    assert callable(_require_preflight_args)
    assert callable(_run_integrity_mode)
    assert callable(_run_release_capsule_mode)
    assert callable(_run_validator_submission_packet_mode)
