# Next Set Implementation Ledger

This ledger records the continuation slices applied after `NEXT_SLICES_IMPLEMENTATION_LEDGER.md`.

## Completed slices

1. **Scoped mutation auth context**
   - Extended UI mutation auth context with explicit `role` and `scopes`.
   - Added `STRATEGY_VALIDATOR_API_TOKEN_SCOPES` parsing with safe default operator write/read scopes.
   - UI operator command policy now blocks writes unless `operator:command:write` is present.

2. **Request-id security envelope**
   - Security middleware now preserves valid `X-Request-ID` values or generates a bounded ID.
   - All normal responses and middleware rejections include `x-request-id`.

3. **In-process mutation rate-limit guard**
   - Added optional `STRATEGY_VALIDATOR_API_MUTATION_RATE_LIMIT_PER_MINUTE` enforcement for mutating methods.
   - Disabled by default to preserve local/dev behavior.

4. **Operator action projection application boundary**
   - Added `strategy_validator.application.operator_action_projection` so API/UI routes can read operator-event projections without importing projections directly.
   - Added `/ui/operator-actions` read endpoint through the existing UI route composition.

5. **Operator action projection lineage expansion**
   - Projection entries now include authorization role, scopes, and target payload digest.

6. **UI command target digesting**
   - UI operator command targets now include a canonical `payload_digest`.
   - Receipts expose `target_payload_digest` to ease audit correlation.

## Validation performed in sandbox

- AST parse checks on changed Python files: PASS
- Direct source-health/repository-truth execution was attempted but the dependency-bearing test/runtime environment remains unreliable in this sandbox. CI should run the included tests as the authoritative check.
