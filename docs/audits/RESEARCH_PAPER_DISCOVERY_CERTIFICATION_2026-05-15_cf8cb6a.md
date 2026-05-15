# Research-and-Paper-Discovery phase certification (2026-05-15, Windows hardening)

## Tag

| Field | Value |
|-------|--------|
| Tag | `research-paper-discovery-certified-2026-05-15-cf8cb6a` |
| Commit | `cf8cb6ae578d1fde9f30f965c48bbb74ced46948` |
| Branch at certify | `main` |
| Certification run ID | `9027a076d42e25e6952f7a5bff762bc8` |
| Repository | `https://github.com/Musterknabee/Strategist` |

## Certification command

```bash
python scripts/local_certify.py --certify-research-paper-discovery --json
```

Exit code: **0**. Post-run `verify-report` status: **PASS** (`blockers: []`).

## Post-certify verification

```bash
python scripts/local_certify.py --verify-report artifacts/local_certify/latest/local_certify_report.json --json
```

## Includes (commit `cf8cb6a`)

- Windows frontend workspace clean retries and dev-server port release
- `frontend_certify_runner` shell mode on Windows for `npm run` local binaries
- Refreshed `docs/audits/public_surface_dashboard.md`
- `scripts/merge_secrets_into_deployment_env.py`

## Prior tag

`research-paper-discovery-certified-2026-05-15` remains valid at commit `80bba54` for the earlier proof chain.

## Safety scope (explicit boundaries)

- **In scope:** Research-and-Paper-Discovery phase local certification only (paper/read-plane, proof chain).
- **Not granted:** live trading readiness; broker order authority; wallet integration; production deployment approval; operator signoff; fake readiness.
