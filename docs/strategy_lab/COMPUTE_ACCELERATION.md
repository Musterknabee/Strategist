# Compute acceleration (optional GPU / process pool)

**Scope:** Advisory research throughput. **Backend boots without torch.** **No heavy compute inside FastAPI request paths.**

## GPU probe CLI

```bash
strategy-validator-gpu-probe --json
```

## Batch worker model

`strategy-validator-strategy-batch-run` accepts `--worker-model thread_pool|process_pool` (default `thread_pool`). Process pool is for CPU-heavy evaluation; adjudication hooks are disallowed in that mode (see runner).

## Benchmark script

```bash
python scripts/benchmark_research_compute.py --json
```

Writes `artifacts/research_compute/benchmark.json` for `GET /ui/research-compute`.

## Docker / PyTorch

Optional `[gpu]` extra installs `torch`. For NVIDIA hosts, follow PyTorch’s official install matrix; Docker may use `--gpus all` when appropriate.

## Limitations

GPU metrics are evidence only. CPU fallback remains the compliance baseline.

## Next graduation step

Treat benchmark artifacts as historical telemetry, not SLO proof.
