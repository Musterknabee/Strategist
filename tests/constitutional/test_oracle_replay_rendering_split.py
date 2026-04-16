from pathlib import Path


def test_oracle_replay_rendering_split() -> None:
    replay = Path("strategy_validator/validator/oracle_replay.py").read_text(encoding="utf-8")
    rendering = Path("strategy_validator/validator/oracle_replay_rendering.py").read_text(encoding="utf-8")

    assert "from strategy_validator.validator.oracle_replay_rendering import (" in replay
    assert "render_oracle_compacted_state_rebuild_markdown" in replay
    assert "render_oracle_compacted_state_inspection_markdown" in replay
    assert "render_oracle_replay_audit_markdown" in replay

    assert "def render_oracle_compacted_state_rebuild_markdown(" not in replay
    assert "def render_oracle_compacted_state_inspection_markdown(" not in replay
    assert "def render_oracle_replay_audit_markdown(" not in replay

    assert "def render_oracle_compacted_state_rebuild_markdown(" in rendering
    assert "def render_oracle_compacted_state_inspection_markdown(" in rendering
    assert "def render_oracle_replay_audit_markdown(" in rendering
