# Storage Upgrade Path

## Current posture

The repository's governed production target remains:

- one append-only SQLite ledger
- one operator-managed node
- explicit migration through `strategy-validator-migrate`

Current backend label:

- `sqlite_single_node`

Current upgrade status:

- `PATH_DECLARED_NOT_IMPLEMENTED`

This is intentional. The repository does **not** claim a live Postgres, multi-node, or distributed storage implementation.

## Governed upgrade path

If the SQLite ledger must be replaced in a future phase, the change must follow this order:

1. Freeze writes and capture a full runtime backup.
2. Export the append-only ledger and required closure evidence into portable artifacts.
3. Rehearse import into the candidate backend in a non-production environment.
4. Verify schema/version parity and replay integrity before any cutover.
5. Introduce the new backend behind the same application/reader/writer seams without weakening append-only discipline.

## Explicit non-goals in this phase

This phase does not add:

- a second storage backend
- live dual-write
- cross-node coordination
- background workers
- automatic cutover or rollback controllers
