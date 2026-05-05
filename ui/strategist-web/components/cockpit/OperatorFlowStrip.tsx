"use client";

import type { OperatorModeId } from "@/lib/operator/operator-modes";

type FlowItem = { id: string; label: string; detail: string; mode: OperatorModeId };

const FLOW_ITEMS: FlowItem[] = [
  { id: "home", label: "Home", detail: "Triage status and first attention item.", mode: "DAILY_OPS" },
  { id: "workbench", label: "Candidate Workbench", detail: "Review strategies, paper outcomes, and blockers.", mode: "RESEARCH_REVIEW" },
  { id: "evidence", label: "Evidence / Replay", detail: "Inspect integrity, replay gaps, and degraded chains.", mode: "FORENSIC_AUDIT" },
  { id: "capital", label: "Capital Firewall", detail: "Confirm paper-only and broker-order boundaries.", mode: "CAPITAL_FIREWALL" },
  { id: "release", label: "Release Control", detail: "Read release evidence without approval authority.", mode: "RELEASE_CONTROL" },
  { id: "topology", label: "System Topology", detail: "Map panes to read-plane routes and contracts.", mode: "SYSTEM_TOPOLOGY" },
];

export function OperatorFlowStrip({ onOpenDetail }: { onOpenDetail: (mode: OperatorModeId) => void }) {
  return (
    <nav className="operator-flow-strip" aria-label="Operator flow" data-testid="cockpit-operator-flow">
      {FLOW_ITEMS.map((item, index) => (
        <button
          key={item.id}
          type="button"
          className="operator-flow-strip__item"
          onClick={() => onOpenDetail(item.mode)}
          aria-label={`Open ${item.label}: ${item.detail}`}
          data-testid={`cockpit-flow-${item.id}`}
        >
          <span className="operator-flow-strip__step">{String(index + 1).padStart(2, "0")}</span>
          <span className="operator-flow-strip__text">
            <strong>{item.label}</strong>
            <em>{item.detail}</em>
          </span>
        </button>
      ))}
    </nav>
  );
}
