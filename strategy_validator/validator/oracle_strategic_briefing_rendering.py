from __future__ import annotations
from typing import Any
def render_oracle_strategic_briefing_markdown(report: Any)->str:
    return f"# Oracle Strategic Briefing\n\n- summary: {getattr(report,'summary_line','')}\n"
__all__=["render_oracle_strategic_briefing_markdown"]
