# UI Facade Snapshot Contract Slice

Implemented a backend-owned public UI facade snapshot so future `ui/strategist-web`
frontend work can consume a deterministic `/ui/*` contract without importing
backend internals or creating a premature frontend package.

## Added

- `scripts/ui_facade_contract_snapshot.py`
- `docs/api/ui-public-facade.snapshot.json`
- `tests/api/test_ui_public_facade_snapshot_contract.py`
- `tests/constitutional/test_ui_public_facade_snapshot_assets.py`

## Updated

- `.github/workflows/ci.yml` now checks the UI facade snapshot after dependency install.
- `scripts/repository_truth_check.py` now enforces the facade route and snapshot assets.
- `scripts/source_health.py` includes the new high-gravity files.
- `docs/architecture/STRATEGIST_UI_BLUEPRINT.md` documents the backend-owned facade contract.
