from __future__ import annotations

import json
from pathlib import Path

from scripts.ui_facade_contract_snapshot import collect_declared_ui_routes_static


def _load_ui_facade_snapshot() -> dict:
    root = Path(__file__).resolve().parents[2]
    path = root / "docs" / "api" / "ui-public-facade.snapshot.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_ui_facade_snapshot_mutation_auth_semantics() -> None:
    snap = _load_ui_facade_snapshot()
    routes = snap["routes"]
    for route in routes:
        method = route["method"]
        kind = route["kind"]
        auth = route["auth_required"]
        path = route["path"]
        assert str(route.get("payload_schema", "")).strip(), f"{method} {path}: payload_schema required"
        if kind == "mutation":
            assert method == "POST", f"{path}: mutation must be POST"
            assert auth is True, f"{path}: mutation must require auth"
        if auth is True:
            assert kind == "mutation" and method == "POST", f"{path}: auth only on POST mutations"

    post_mutations = [r for r in routes if r["method"] == "POST" and r["kind"] == "mutation"]
    paths = {r["path"] for r in post_mutations}
    assert "/ui/commands/{action}" in paths
    assert "/ui/strategy-intake" in paths
    assert len(post_mutations) == 2


def test_declared_post_ui_routes_match_mutation_facade_contract() -> None:
    root = Path(__file__).resolve().parents[2]
    declared = collect_declared_ui_routes_static(root)
    post_paths = {r["path"] for r in declared if r["method"] == "POST"}
    assert post_paths == {"/ui/commands/{action}", "/ui/strategy-intake"}


def test_ui_routes_mutation_wires_require_mutation_auth() -> None:
    root = Path(__file__).resolve().parents[2]
    text = (root / "strategy_validator" / "api" / "routes" / "ui_routes_mutation.py").read_text(encoding="utf-8")
    assert text.count("require_mutation_auth") >= 2
    assert "Depends(ui_root.require_mutation_auth)" in text
