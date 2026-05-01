# Optional GPU Acceleration (Advisory Research Only)

GPU acceleration in this repo is **optional** and **advisory-only**:

- Backend/API startup must work without GPU and without `torch`.
- CUDA compute is not required for deployment approval.
- Research compute outputs are evidence artifacts, not authoritative decisions.
- Ledger authority remains with validator orchestrator boundaries.

## Install policy

Base install stays CPU-safe:

```bash
pip install -e .
```

Optional GPU extra:

```bash
pip install -e .[gpu]
```

`torch` wheels are platform-specific. If the generic install does not provide CUDA, use the official selector: [https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)

## Host checks

### Native Linux / WSL

```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available(), torch.version.cuda)"
```

### Docker

```bash
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

## Repo probes and demo commands

GPU capability probe:

```bash
python -m strategy_validator.cli.gpu_probe --json
```

Advisory compute demo (CPU/CUDA selection):

```bash
python -m strategy_validator.cli.research_compute_demo --backend auto --paths 100000 --json
```

Benchmark artifact:

```bash
python scripts/benchmark_research_compute.py --json
```

Writes:

- `artifacts/research_compute/<run_id>.result.json`
- `artifacts/research_compute/<run_id>.evidence.json`
- `artifacts/research_compute/benchmark.json`

## CPU fallback policy

- `backend_requested=auto` uses CUDA only when probe reports available.
- No silent GPU claim: if CUDA unavailable, payload includes explicit reason (`TORCH_NOT_INSTALLED` or `CUDA_UNAVAILABLE`).
- CPU fallback must still produce deterministic, PIT-tagged evidence artifacts.

## Governance boundary reminders

- Do **not** run heavy GPU compute inside request handlers.
- Do **not** let research compute write authoritative ledger decisions.
- PIT/as-of metadata is required in request/result/evidence records.
