# Operator Cockpit UI Flow

The cockpit is a solo-operator read plane for triage, review, and evidence inspection. It helps decide what to inspect next; it does not approve deployment, place orders, sign off an operator decision, or claim profitability.

## Recommended Daily Flow

1. Start at Operator Home.
2. Read the overall badge, the safety chip, and the first attention item.
3. Use the Operator Flow buttons for the next safe inspection path.
4. Open Candidate Workbench for strategy and candidate review.
5. If evidence, replay, provider, or paper data is missing or degraded, open the matching detail pane before judging a candidate.
6. Use Advanced Cockpit when you need route-level evidence, topology, release artifacts, or capital firewall details.

## Operator Home

Operator Home is the calm triage layer. It answers: current status, what needs attention first, candidate/research state, evidence/replay state, provider/data state, and where to click next.

The first screen intentionally favors summary cards and next safe inspection paths over raw tables. The strategy scoreboard remains available as detail, but it is not the main decision surface.

Missing values remain `UNKNOWN` or `NO_PAPER_DATA`. No paper data is not a win, loss, or OK state.

## Candidate Workbench

Candidate Workbench is the strategy review layer. It consolidates strategy memory, graveyard, backtest forensics, paper tracking, provider setup, provider health, and evidence chain data into review rows.

Use it to filter candidates by blockers, review state, paper outcome, missing data, duplicate/graveyard warnings, and degraded evidence/replay. Summary cards show blocked rows, missing paper data, evidence/replay degradation, and provider pending-key counts.

A blocked candidate takes precedence over an optimistic paper return. Provider key gaps are pending/action-required, not success. Paper wins/losses only come from explicit paper-tracking data.

## Advanced Cockpit

Advanced Cockpit is the expert detail layer. It keeps raw inspection paths available: Evidence / Replay, Capital Firewall, Release Control, System Topology, Provider Setup / First Run, incident/remediation surfaces, and command posture where it already exists.

Modes are grouped by operator intent. Read-plane modes do not expose browser shell execution. Command-capable modes show concise auth/token warnings and still do not create approval, signoff, trading, or deployment authority.

## Safety Boundaries

The cockpit is paper/research only:

- No live trading.
- No broker orders.
- No production deployment approval.
- No operator signoff.
- No promotion, rejection, or deployment authority from this UI.
- No profitability claim.

Evidence and replay verify integrity of artifacts and projections. They do not prove strategy quality or safety to execute.

## Data Semantics

- `UNKNOWN`: the UI cannot determine the state from current read-plane payloads.
- `PENDING`: the system is waiting on an expected artifact, setup step, or route result.
- `DEGRADED`: evidence, replay, provider, or hook data has a known problem.
- `NO_PAPER_DATA`: no explicit paper-tracking outcome exists for the candidate or strategy.
- `BLOCKED`: a blocker is present and must be inspected before treating the candidate or surface as reviewable.

Do not convert these states to OK during review. Open the relevant detail pane and inspect the payload before taking any external operator action.
