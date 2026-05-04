# Market Data Integrity

Market Data Integrity checks detect evidence risks that can make a strategy appear stronger than it really is.

The check covers:

- missing trading-day coverage heuristics
- stale last bar versus `as_of_utc`
- duplicate vendor records
- split-like / unadjusted price jumps
- symbol continuity and survivorship warnings
- unknown adjusted/unadjusted status
- timezone/session warning hooks

## Status vocabulary

- `PROVEN`: no integrity warnings/blockers found by this heuristic layer.
- `WARNING`: evidence is usable for paper/research, but needs operator review.
- `BLOCKED`: integrity issue should block promotion evidence.
- `NOT_APPLICABLE`: no bars were available, typically synthetic/demo paths.

## Batch integration

Each strategy run writes:

```text
market_data_integrity_result.json
```

The strategy evidence manifest carries:

```text
market_data_integrity_evidence_sha256
market_data_integrity_gate_status
```

The Strategy Lab table shows an `MDI` column and inspector links to the artifact path/digest.

## Limitations

This is a deterministic heuristic layer. It does not replace a licensed corporate-actions database, exchange calendar service, or point-in-time constituent universe. Unknown adjustment status is intentionally a warning.
