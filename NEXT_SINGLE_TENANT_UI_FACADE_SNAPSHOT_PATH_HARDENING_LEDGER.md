# Next Slice Ledger — UI Facade Snapshot Path-Integrity Hardening

## Slice

Harden the public backend UI facade contract snapshot generator so snapshot verification and snapshot materialization do not read or write through symlinked filesystem paths.

## Problem

`scripts/ui_facade_contract_snapshot.py` is part of the public UI facade contract gate. It can be run in check mode against a committed snapshot or in generation mode to write a snapshot. Before this slice, the caller-provided `--output` path was used directly after relative-path joining. That left the snapshot path weaker than the newer deployment/evidence handoff tooling:

- `--check --output <symlink>` could read through a symlinked snapshot path.
- `--output <symlink>` could overwrite an unintended target through filesystem indirection.
- `--output <symlinked-parent>/snapshot.json` could materialize evidence outside the reviewed workspace.

## Change

Updated `scripts/ui_facade_contract_snapshot.py` to reuse the shared operator path-integrity helpers:

- check mode validates the output snapshot as a safe input file using `UI_FACADE_SNAPSHOT` labels;
- write mode validates the output snapshot as a safe output file using `UI_FACADE_SNAPSHOT_OUTPUT` labels;
- path-integrity failures emit `ui_facade_contract_snapshot_path_error/v1` JSON and return non-zero before building the snapshot or touching the file.

## Tests

Added `tests/constitutional/test_ui_facade_contract_snapshot_path_integrity.py` covering:

- symlinked snapshot input rejection in `--check` mode;
- symlinked snapshot output rejection in write mode;
- output under a symlinked parent rejection in write mode.

## Validation

Focused validation passed:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_ui_facade_contract_snapshot_path_integrity.py \
  tests/api/test_ui_public_facade_snapshot_contract.py \
  tests/constitutional/test_ui_public_facade_snapshot_assets.py \
  tests/constitutional/test_frontend_readiness_claim_path_integrity.py \
  tests/constitutional/test_repo_archive_path_integrity.py \
  tests/constitutional/test_provider_operator_path_integrity.py \
  tests/constitutional/test_generate_operator_deployment_signoff.py
```

Result: `34 passed`.
