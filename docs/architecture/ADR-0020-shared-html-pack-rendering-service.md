# ADR-0020 — Shared HTML pack rendering service

## Decision
Move briefing, status, and incident pack HTML rendering behind one shared control-plane HTML service.

## Why
These pack surfaces had converged on shared headers, section composition, and workboard rendering in markdown, but HTML remained a fragmented presentation seam. That made the operator presentation layer inconsistent and left status/incident HTML as missing or ad hoc behavior.

## Consequences
- One control-plane HTML rendering path now owns pack HTML framing.
- Validator renderers are compatibility facades.
- Status, incident, and briefing packs can all materialize JSON, Markdown, and HTML outputs through the same converged presentation plane.
