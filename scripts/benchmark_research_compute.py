"""Benchmark CPU process-pool vs sequential work; optional torch/CUDA timing (research evidence)."""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from multiprocessing import cpu_count
from pathlib import Path

from strategy_validator.contracts.research_compute import ResearchComputeBenchmarkRecord
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.research_compute.gpu_probe import probe_gpu_capability


def _work(n: int) -> int:
    return sum(i * i for i in range(n))


def _pool_chunk(args: tuple[int, int]) -> int:
    start, end = args
    return sum(i * i for i in range(start, end))


def main() -> None:
    parser = argparse.ArgumentParser(description="Research compute benchmark (evidence only; no live trading).")
    parser.add_argument("--iterations", type=int, default=40_000)
    parser.add_argument("--chunks", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    n = int(args.iterations)
    t0 = time.perf_counter()
    _work(n)
    cpu_ms = int((time.perf_counter() - t0) * 1000)

    workers = min(int(args.chunks), max(1, cpu_count()))
    step = max(1, n // workers)
    ranges = [(i * step, min(n, (i + 1) * step)) for i in range(workers)]
    t1 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as ex:
        list(ex.map(_pool_chunk, ranges))
    pool_ms = int((time.perf_counter() - t1) * 1000)

    probe = probe_gpu_capability()
    gpu_ok = bool(probe.get("gpu_available"))
    torch_ok = bool(probe.get("torch_available"))
    gpu_bench_ms: int | None = None
    if gpu_ok and torch_ok:
        try:
            import importlib

            torch = importlib.import_module("torch")
            t2 = time.perf_counter()
            x = torch.randn(1024, 1024, device="cuda")
            y = torch.matmul(x, x)
            _ = float(torch.sum(y))
            gpu_bench_ms = int((time.perf_counter() - t2) * 1000)
        except Exception:
            gpu_bench_ms = None

    generated = ResearchComputeBenchmarkRecord(
        generated_at_utc=datetime.now(timezone.utc),
        cpu_duration_ms=cpu_ms,
        process_pool_duration_ms=pool_ms,
        process_pool_workers=workers,
        gpu_available=gpu_ok,
        gpu_benchmark_duration_ms=gpu_bench_ms,
        torch_available=torch_ok,
        cuda_available=bool(probe.get("cuda_available")),
        fallback_status=str(probe.get("fallback_status") or "GPU_UNAVAILABLE_CPU_FALLBACK"),
        extra={"logical_cpus": cpu_count(), "probe": probe},
    )
    body = generated.model_dump(mode="json")
    digest = canonical_json_sha256({k: v for k, v in body.items() if k != "evidence_digest"})
    record = generated.model_copy(update={"evidence_digest": digest})

    out_dir = Path.cwd() / "artifacts" / "research_compute"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "benchmark.json"
    out_path.write_text(
        json.dumps(record.model_dump(mode="json"), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = {
        "ok": True,
        "artifact": str(out_path),
        "record": record.model_dump(mode="json"),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"cpu_ms={cpu_ms} pool_ms={pool_ms} workers={workers} gpu={gpu_ok}")


if __name__ == "__main__":
    main()
