# Production Slice v1

This repository's first production target is a **single-tenant operator-grade governance service**.

## In scope
- adjudication and readiness surfaces
- evidence ledger and projection backfill
- operator queue, workboard, pack assembly, and release publication
- authenticated mutation routes
- backend-connected operator UI with strict backend mode available
- single service deployment via `strategy-validator-api`
- explicit ledger migration via `strategy-validator-migrate`

## Out of scope for v1
- multi-tenant tenancy controls
- silent mock-backed operator views
- distributed worker topologies
- broad provider fan-out beyond one sanctioned production path
- frontend demo defaults presented as operational truth
