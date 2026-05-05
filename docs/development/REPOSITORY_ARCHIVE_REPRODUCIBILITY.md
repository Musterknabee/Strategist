# Repository Archive Reproducibility

## Purpose

This runbook documents how to build and verify a reproducible full-repo handoff ZIP for local operator and release workflows.

- Local packaging evidence only.
- Not production deployment approval.
- Not operator signoff.
- Not live trading authorization.
- Not profitability evidence.

## Build a clean repository archive

```bash
python scripts/package_repo.py \
  --output scratch/repo-handoff.zip \
  --json
```

Dry-run membership check (no archive write):

```bash
python scripts/package_repo.py --check --json
```

## Verify a generated archive

```bash
python scripts/verify_repo_archive.py scratch/repo-handoff.zip --json
```

Verification fails non-zero if the archive is malformed or non-compliant (extra/missing paths, duplicate entries, path traversal, metadata drift, digest mismatch).

## Exclusions and rationale

The clean archive intentionally excludes transient and sensitive local material:

- runtime/build artifacts (`artifacts/`, `scratch/`, caches, `node_modules`, `.next`, pycache),
- local environment files (`deployment.env`, `.env`, `.env.local`),
- local ledgers/databases (`*.sqlite*`, `*.db*`),
- local logs/coverage/jsonl runtime traces,
- generated archives (`*.zip`, `*.tar`, `*.gz`, `*.tgz`),
- common secret-key material (`*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.crt`),
- symlinked files/directories in archive inputs.

## Safety notes

- Archive output paths are validated to avoid self-inclusion in future archives.
- Archive verification rejects absolute-path and `..` traversal entries.
- Do not publish or upload generated archives automatically from this workflow.

## Keep generated artifacts out of commits

After local packaging checks:

```bash
git status --short
rm -f scratch/repo-handoff.zip
```

Use only gitignored output paths (`scratch/`, `artifacts/`) for local archives.
