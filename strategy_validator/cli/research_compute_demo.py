"""CLI demo runner for advisory research compute with CPU fallback."""
from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone

from strategy_validator.contracts.research_compute import ComputeBackend, ResearchComputeRequest
from strategy_validator.research_compute.monte_carlo import run_research_compute_demo


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run advisory research compute Monte Carlo demo (CPU/CUDA optional).")
    parser.add_argument("--backend", choices=["auto", "cpu", "cuda"], default="auto")
    parser.add_argument("--paths", type=int, default=100_000)
    parser.add_argument("--steps", type=int, default=252)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)

    req = ResearchComputeRequest(
        run_id=f"rc-{uuid.uuid4().hex[:12]}",
        strategy_id="demo",
        research_task_id="research_compute_demo",
        input_manifest_digest="demo-input-manifest",
        provider_evidence_digest="demo-provider-evidence",
        pit_as_of_utc=datetime.now(timezone.utc).isoformat(),
        backend_requested=ComputeBackend(ns.backend),
        deterministic_seed=ns.seed,
        paths=ns.paths,
        steps=ns.steps,
    )
    result = run_research_compute_demo(req)
    payload = result.model_dump(mode="json")
    text = json.dumps(payload, indent=2 if ns.json else None, sort_keys=True)
    print(text)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
