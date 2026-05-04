#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, path_error_payload, safe_input_file, safe_output_file  # noqa: E402

DEFAULT_SNAPSHOT = Path("docs/architecture/openapi.snapshot.json")


def generate_openapi_payload() -> dict:
    from strategy_validator.api.app import create_app

    return create_app().openapi()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify the FastAPI OpenAPI contract snapshot.")
    parser.add_argument("--output", default=str(DEFAULT_SNAPSHOT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    path = Path(args.output)

    try:
        checked_path = (
            safe_input_file(path, label="OPENAPI_SNAPSHOT", required=True)
            if args.check
            else safe_output_file(path, label="OPENAPI_SNAPSHOT_OUTPUT")
        )
    except PathIntegrityError as exc:
        print(json.dumps(path_error_payload(exc, schema_version="openapi_contract_snapshot_path_error/v1"), sort_keys=True))
        return 1
    assert checked_path is not None
    path = checked_path

    payload = generate_openapi_payload()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
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
