# Next Slices Implementation Ledger

This ledger records the additional bounded slices applied after the Horizon A-to-C full-repo bundle.

## Completed slices

1. **Read-only operator-action diagnostics**
   - Added read-only operator action journal readers/verifiers.
   - Updated ledger CLI diagnostics and production smoke projection indexing to avoid creating or migrating missing diagnostic databases.
   - Added tests for missing/empty ledger read-only behavior.

2. **Operator-action projection auth lineage**
   - Preserved mutation authorization context in operator-action event targets.
   - Surfaced authorization principal, principal source, and auth mode in the operator-action projection index.

3. **API app factory contract**
   - Added `create_app()` while preserving module-level `app = create_app()`.
   - Wired CI/repository truth to require OpenAPI snapshot generation against the factory.

4. **OpenAPI snapshot CI gate**
   - Added the OpenAPI contract snapshot check to the main CI validation job.
   - Extended constitutional tests and repository truth checks to verify the app-factory/snapshot contract.

5. **Actual request-body cap enforcement**
   - Hardened the security envelope to buffer/replay write-method request bodies and reject oversized streamed bodies even when `Content-Length` is absent or inaccurate.
   - Added ASGI-level test coverage for streamed-body rejection.

6. **Operator principal validation**
   - Normalized and validated operator principal headers for mutation routes.
   - Invalid principal headers now fail closed with a deterministic API error.

7. **Provider network URL hardening**
   - Tightened provider URL policy to reject protocol-relative URLs and private/link-local/loopback/reserved IP targets unless explicitly allowed by policy call sites.
   - Provider environment overrides are validated before assignment so invalid overrides are reported rather than silently adopted.

8. **Repository truth ratchet**
   - Updated repository truth to require migration truth v3, sequence uniqueness, OpenAPI CI checks, app factory wiring, read-only diagnostics, and provider env URL validation.

9. **Architecture health budget alignment**
   - Aligned the architecture-health application public-surface budget with the current ratcheted budget.
   - Expanded source-health roots to include provider URL policy and config validation.

10. **Documentation update**
   - Updated architecture health notes to document the new read-only diagnostics, app-factory/OpenAPI contract, and provider env hardening.

## Validation performed in sandbox

- `python -m py_compile` on changed Python files: PASS
- `scripts/migration_truth_check.py`: PASS
- `scripts/source_health.py`: PASS
- `scripts/repository_truth_check.py`: PASS

Full pytest was not run in this sandbox because the dependency-bearing Python environment hangs on normal import/test execution. The added tests are included for CI execution.
