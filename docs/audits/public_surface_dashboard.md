# Public Surface Dashboard

Generated from `python scripts/public_surface_dashboard.py --json`.

| Metric | Actual | Budget | Headroom | Status |
| --- | ---: | ---: | ---: | --- |
| `adr_count` | 95 | 98 | 3 | WITH_HEADROOM |
| `api_route_count` | 289 | 366 | 77 | WITH_HEADROOM |
| `api_route_modules` | 28 | 32 | 4 | WITH_HEADROOM |
| `application_exports` | 316 | 322 | 6 | WITH_HEADROOM |
| `cli_files` | 215 | 220 | 5 | WITH_HEADROOM |
| `compatibility_shims` | 37 | 40 | 3 | WITH_HEADROOM |
| `console_scripts` | 45 | 47 | 2 | WITH_HEADROOM |
| `docs_pages` | 179 | 182 | 3 | WITH_HEADROOM |
| `frontend_pages` | 80 | 88 | 8 | WITH_HEADROOM |
| `test_files` | 720 | 725 | 5 | WITH_HEADROOM |

No-headroom categories: none.

Rule: Any category with no headroom requires consolidation, an explicit budget update with rationale, or rejection of new public surface.
