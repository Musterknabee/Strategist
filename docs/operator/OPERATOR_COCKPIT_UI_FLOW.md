# Operator Cockpit UI Flow

The cockpit is a solo-operator read plane for triage, review, and evidence inspection. It helps decide what to inspect next; it does not approve deployment, place orders, sign off an operator decision, or claim profitability.

## Daily Flow

1. Start at Operator Home.
2. Review the overall badge and the first attention item.
3. Open Candidate Workbench for strategy and candidate review.
4. If evidence, replay, provider, or paper data is missing or degraded, open the matching detail pane before judging a candidate.
5. Use Advanced Cockpit when you need route-level evidence, topology, release artifacts, or capital firewall details.

## Operator Home

Operator Home is the triage layer. It shows current status, what needs attention first, strategy/candidate counts, paper wins/losses, unknown paper results, replay issues, provider key gaps, and the next inspection path.

Missing values remain `UNKNOWN` or `NO_PAPER_DATA`. No paper data is not a win, loss, or OK state.

## Candidate Workbench

Candidate Workbench is the strategy review layer. It consolidates strategy memory, graveyard, backtest forensics, paper tracking, provider setup, provider health, and evidence chain data into review rows.

Use it to filter candidates by review state, paper outcome, missing data, blockers, duplicate warnings, and graveyard matches. A blocked candidate takes precedence over an optimistic paper return. Provider key gaps are pending/action-required, not success.

## Advanced Cockpit

Advanced Cockpit keeps raw inspection paths available: Evidence / Replay, Capital Firewall, Release Control, System Topology, and Provider Setup / First Run. These panes reveal read-plane detail and token-gated command posture where it already exists. They do not add backend authority.

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

Do not convert these states to OK during review. Open the relevant detail pane and inspect the payload before taking any external operator action.
