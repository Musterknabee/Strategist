# ADR-0026: Operator pack timeline / activity feed read plane

## Decision
Introduce a typed operator pack timeline read model above the indexed operator pack registry so pack families can be rendered as chronological operator activity, not only latest-state boards.

## Consequences
- CLI can emit a structured timeline payload over indexed pack activity.
- Briefing, status, and incident markdown surfaces can render a shared pack timeline section.
- Future operator consoles can consume activity history without rebuilding recency ordering over raw index matches.
