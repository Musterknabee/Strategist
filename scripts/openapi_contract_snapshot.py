#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.api.app import create_app

DEFAULT_SNAPSHOT = Path("docs/architecture/openapi.snapshot.json")


def generate_openapi_payload() -> dict:
    return create_app().openapi()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify the FastAPI OpenAPI contract snapshot.")
    parser.add_argument("--output", default=str(DEFAULT_SNAPSHOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = generate_openapi_payload()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    path = Path(args.output)
    if args.check:
        if not path.exists():
            print(f"missing OpenAPI snapshot: {path}")
            return 1
        current = path.read_text(encoding="utf-8")
        if current != text:
            print(f"OpenAPI snapshot drift: {path}")
            return 1
        print(f"OpenAPI snapshot OK: {path}")
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(str(path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
