from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_briefing_replay_commands import register_oracle_briefing_replay_commands
from strategy_validator.cli.oracle_event_diagnostic_runners import (
    cmd_oracle_briefing_pack,
    cmd_oracle_compacted_state_inspect,
    cmd_oracle_compacted_state_rebuild,
    cmd_oracle_replay_audit,
)
from strategy_validator.cli.oracle_event_transition_memory_runners import cmd_oracle_transition

BRIEFING_REPLAY_RUNNERS = {
    "oracle-compacted-state-inspect": cmd_oracle_compacted_state_inspect,
    "oracle-compacted-state-rebuild": cmd_oracle_compacted_state_rebuild,
    "oracle-briefing-pack": cmd_oracle_briefing_pack,
    "oracle-replay-audit": cmd_oracle_replay_audit,
    "oracle-transition": cmd_oracle_transition,
}


def register_oracle_briefing_replay_runtime_commands(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    register_oracle_briefing_replay_commands(sub, runners=BRIEFING_REPLAY_RUNNERS)
