#!/usr/bin/env python3
"""Check local operator wiring: artifact paths, API read-plane, CORS (exit 0 = ready)."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]


def _artifact_root() -> Path:
    for candidate in (
        os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", ""),
        r"C:\var\lib\strategy-validator\artifacts",
        str(_REPO / "artifacts"),
    ):
        if candidate:
            p = Path(candidate).resolve()
            if p.is_dir() or candidate.endswith("artifacts"):
                return p
    return (_REPO / "artifacts").resolve()


def _check(name: str, ok: bool, detail: str = "") -> bool:
    mark = "OK" if ok else "FAIL"
    line = f"  [{mark}] {name}"
    if detail:
        line += f" — {detail}"
    print(line, flush=True)
    return ok


def main() -> int:
    art = _artifact_root()
    print(f"artifact_root={art}\n", flush=True)
    all_ok = True

    paths = {
        "strategy_runs": art / "strategy_runs",
        "oracle_cycle": art / "oracle_cycle" / "latest" / "oracle_research_cycle_manifest.json",
        "strategy_theses/latest": art / "strategy_theses" / "latest" / "thesis_generation_report.json",
        "strategy_memory": art / "strategy_memory" / "latest" / "memory_index.json",
        "shadow_book": art / "shadow_books" / "latest" / "shadow_book_manifest.json",
        "research_os_runtime": art / "research_os_runtime" / "latest" / "runtime_demo_manifest.json",
        "provider_paper_loop": art / "provider_paper_loop" / "latest" / "provider_paper_loop_manifest.json",
        "evidence_catalog": art / "research_os_evidence_catalog" / "latest" / "research_os_evidence_catalog.json",
        "policy_gate": art / "research_os_policy_gate" / "latest" / "research_os_policy_gate_report.json",
        "operator_run": art / "research_os_operator_runs" / "latest" / "research_os_operator_run_manifest.json",
        "operator_wiring": art / "operator_wiring" / "latest" / "operator_evidence_wiring_report.json",
    }
    for label, path in paths.items():
        all_ok &= _check(label, path.is_file() if path.name.endswith(".json") else path.is_dir(), str(path))

    api = os.environ.get("STRATEGIST_VERIFY_API", "http://127.0.0.1:8000").rstrip("/")
    for route in ("/healthz", "/ui/research-os/status", "/ui/strategy-thesis/generation/latest"):
        try:
            with urllib.request.urlopen(f"{api}{route}", timeout=15) as resp:
                ok = 200 <= resp.status < 300
                all_ok &= _check(f"GET {route}", ok, f"HTTP {resp.status}")
        except urllib.error.URLError as exc:
            all_ok &= _check(f"GET {route}", False, str(exc))

    ui_origin = os.environ.get("STRATEGIST_VERIFY_UI_ORIGIN", "http://localhost:3001")
    try:
        req = urllib.request.Request(
            f"{api}/healthz",
            headers={"Origin": ui_origin},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            acao = resp.headers.get("Access-Control-Allow-Origin", "")
            cors_ok = acao == ui_origin
            all_ok &= _check(f"CORS for {ui_origin}", cors_ok, acao or "missing")
    except urllib.error.URLError as exc:
        all_ok &= _check("CORS probe", False, str(exc))

    if paths["oracle_cycle"].is_file():
        manifest = json.loads(paths["oracle_cycle"].read_text(encoding="utf-8"))
        all_ok &= _check(
            "oracle fusion",
            bool(manifest.get("fusion_posture")),
            str(manifest.get("fusion_posture", "")),
        )

    print("\n" + ("Wiring looks good." if all_ok else "Some checks failed — run run_full_operator_spine.py"), flush=True)
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
