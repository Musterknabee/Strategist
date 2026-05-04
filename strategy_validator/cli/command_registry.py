from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    name: str
    help: str
    configure: Callable[[argparse.ArgumentParser], None]
    runner: Callable[..., int]


def register_command(subparsers: argparse._SubParsersAction[argparse.ArgumentParser], spec: CommandSpec) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(spec.name, help=spec.help)
    spec.configure(parser)
    parser.set_defaults(_run=spec.runner)
    return parser


def register_commands(subparsers: argparse._SubParsersAction[argparse.ArgumentParser], specs: list[CommandSpec]) -> list[argparse.ArgumentParser]:
    return [register_command(subparsers, spec) for spec in specs]
