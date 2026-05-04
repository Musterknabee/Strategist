"""Production API entrypoint."""
from __future__ import annotations

import argparse


def _fail_if_production_startup_is_not_ready() -> None:
    """Fail closed before binding the API in unsafe production configurations."""
    from strategy_validator.core.config import load_config
    from strategy_validator.core.enums import RuntimeMode
    from strategy_validator.validator.readiness import perform_readiness_check

    cfg = load_config()
    if cfg.mode != RuntimeMode.PRODUCTION:
        return

    readiness = perform_readiness_check()
    if readiness.status == "READY":
        return

    blockers = "; ".join(f"{b.code}: {b.message}" for b in readiness.blockers)
    raise SystemExit(
        "strategy-validator-api refused to start in PRODUCTION because runtime "
        f"readiness is {readiness.status}. Blockers: {blockers or 'UNKNOWN'}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Run the strategy-validator FastAPI service')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--reload', action='store_true')
    ns = parser.parse_args(argv)

    _fail_if_production_startup_is_not_ready()

    try:
        import uvicorn
    except ModuleNotFoundError as exc:  # pragma: no cover
        raise SystemExit('uvicorn is required for strategy-validator-api; install the api or production extra') from exc

    uvicorn.run('strategy_validator.api.app:app', host=ns.host, port=ns.port, reload=ns.reload)
    return 0


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
