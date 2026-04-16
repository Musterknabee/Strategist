"""Production API entrypoint."""
from __future__ import annotations

import argparse


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the strategy-validator FastAPI service')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--reload', action='store_true')
    ns = parser.parse_args(argv)

    try:
        import uvicorn
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit('uvicorn is required for strategy-validator-api; install the api or production extra') from exc

    uvicorn.run('strategy_validator.api.app:app', host=ns.host, port=ns.port, reload=ns.reload)
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
