# Candidate Workbench

## Purpose

`Candidate Workbench` is a read-plane summary for daily candidate review. It gives one place to inspect:

- candidate/strategy anchors
- paper/research-only outcomes
- blockers and warnings
- duplicate and graveyard warnings
- evidence and replay health
- next safe action

This view is advisory and evidence-driven.

## What this page does not do

- No promotion authority.
- No rejection or approval authority.
- No ledger mutation.
- No live trading or broker orders.
- No profitability guarantee.

## Derivation rules (safety-first)

- Paper outcomes are derived only from explicit paper tracking fields.
- Missing or ambiguous data stays `NO_PAPER_DATA` / `UNKNOWN`.
- Blockers are surfaced; not hidden.
- Duplicate/graveyard statuses come only from explicit memory/graveyard payloads.
- Evidence/replay statuses are conservative (`MISSING` / `DEGRADED` / `UNKNOWN` when uncertain).

## Status meanings

- `PAPER_WIN` / `PAPER_LOSS` / `PAPER_FLAT`: explicit paper metrics only.
- `NO_PAPER_DATA`: no explicit paper evidence.
- `BLOCKED`: explicit lifecycle or forensic blocker.
- `DUPLICATE_WARNING`: duplicate-variant warning exists in memory payload.
- `PRIOR_DEATH_REASON` / `GRAVEYARDED`: graveyard projection has a match.
- `VERIFY_REPLAY` / `CHECK_EVIDENCE`: replay or evidence trust requires operator review.

## Troubleshooting

- No candidates yet:
  - run paper/research workflows and refresh read-plane payloads.
- No paper data:
  - candidate exists but paper tracking evidence has not landed yet.
- Provider key missing:
  - use Provider Setup Center and validate non-persistently.
- Evidence missing/degraded:
  - inspect forensics/evidence chain panes and artifact digests.
