# Cockpit Simplified Home

`Operator Home` is the default cockpit landing layer. It keeps all expert panes available, but starts with a plain-language summary for quick triage.

## Purpose

- Show immediate state for strategies, paper outcomes, blockers, review load, and provider/data health.
- Keep paper-only posture explicit.
- Route operators into existing advanced panes without removing any evidence depth.

## Paper Win/Loss Derivation

- A paper result is only treated as win/loss/flat when `paper_tracking.latest.scorecard.cumulative_paper_return` is explicitly present.
- If that field is absent, the home scoreboard shows `UNKNOWN` or `NO_PAPER_DATA`.
- The home screen does not infer profitability from missing data.

## Meaning of UNKNOWN

- `UNKNOWN` means the source payload is missing, unreadable, or not yet produced.
- `UNKNOWN` is not interpreted as success and is never silently converted to zero-risk or pass.

## Safety Posture

- Home always displays: paper only / no live trading.
- No promotion authority is granted from this screen.
- No live execution, broker mutation, deployment approval, or signoff authority is added.

## Advanced Data Location

- Use **Show advanced cockpit details** to reveal the existing switchboard, seven-pane grid, and full post-grid expert panes.
- Drilldown buttons in home open existing modes (research review, forensic audit, release control, capital firewall, first-run/provider setup).
# Cockpit Simplified Home

`Operator Home` is the default cockpit landing layer. It keeps all expert panes available, but starts with a plain-language summary for quick triage.

## Purpose

- Show immediate state for strategies, paper outcomes, blockers, review load, and provider/data health.
- Keep paper-only posture explicit.
- Route operators into existing advanced panes without removing any evidence depth.

## Paper Win/Loss Derivation

- A paper result is only treated as win/loss/flat when `paper_tracking.latest.scorecard.cumulative_paper_return` is explicitly present.
- If that field is absent, the home scoreboard shows `UNKNOWN` or `NO_PAPER_DATA`.
- The home screen does not infer profitability from missing data.

## Meaning of UNKNOWN

- `UNKNOWN` means the source payload is missing, unreadable, or not yet produced.
- `UNKNOWN` is not interpreted as success and is never silently converted to zero-risk or pass.

## Safety Posture

- Home always displays: paper only / no live trading.
- No promotion authority is granted from this screen.
- No live execution, broker mutation, deployment approval, or signoff authority is added.

## Advanced Data Location

- Use **Show advanced cockpit details** to reveal the existing switchboard, seven-pane grid, and full post-grid expert panes.
- Drilldown buttons in home open existing modes (research review, forensic audit, release control, capital firewall, first-run/provider setup).
