from __future__ import annotations

from pathlib import Path

from scripts.ui_route_mutation_auth_ast import (
    collect_ui_mutation_post_auth_violations,
    collect_ui_read_plane_mutation_auth_violations,
)


def test_ui_mutation_post_handlers_pass_ast_require_mutation_auth_gate() -> None:
    root = Path(__file__).resolve().parents[2]
    assert collect_ui_mutation_post_auth_violations(root) == ()


def test_ui_read_plane_handlers_pass_ast_no_mutation_auth_gate() -> None:
    root = Path(__file__).resolve().parents[2]
    assert collect_ui_read_plane_mutation_auth_violations(root) == ()
