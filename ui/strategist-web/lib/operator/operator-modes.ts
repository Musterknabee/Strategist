/**
 * Operator cockpit modes — UI composition and ordering only (not a backend state machine).
 */

export type OperatorModeSafety = "READ_PLANE_ONLY" | "COMMAND_CAPABLE";

export type OperatorModeId =
  | "FIRST_RUN"
  | "DAILY_OPS"
  | "RESEARCH_REVIEW"
  | "RELEASE_CONTROL"
  | "INCIDENT_RESPONSE"
  | "FORENSIC_AUDIT"
  | "CAPITAL_FIREWALL"
  | "SYSTEM_TOPOLOGY";

/** Sections rendered below the seven-pane grid, in default document order. */
export type CockpitPostGridSectionKey =
  | "topology"
  | "research_paper_drilldown"
  | "candidate_workbench"
  | "capital_firewall"
  | "operator_health"
  | "remediation"
  | "first_run"
  | "provider_setup"
  | "strategy_lifecycle"
  | "release_control"
  | "evidence_runbook"
  | "audit_forensic"
  | "policy_risk"
  | "promotion_dossier"
  | "research_batch"
  | "operator_command";

export const COCKPIT_POST_GRID_SECTION_ORDER: CockpitPostGridSectionKey[] = [
  "topology",
  "research_paper_drilldown",
  "candidate_workbench",
  "capital_firewall",
  "operator_health",
  "remediation",
  "first_run",
  "provider_setup",
  "strategy_lifecycle",
  "release_control",
  "evidence_runbook",
  "audit_forensic",
  "policy_risk",
  "promotion_dossier",
  "research_batch",
  "operator_command",
];

export type OperatorModeDefinition = {
  mode_id: OperatorModeId;
  label: string;
  purpose: string;
  primary_panes: string[];
  secondary_panes: string[];
  /** Human-readable hint for where “next action” copy is derived from (not a live runner). */
  recommended_next_action_source: string;
  safety: OperatorModeSafety;
  /** Shown when safety is COMMAND_CAPABLE; remind about auth / trusted workstation. */
  command_warning: string | null;
};

function moveKeysToFront(order: CockpitPostGridSectionKey[], front: CockpitPostGridSectionKey[]): CockpitPostGridSectionKey[] {
  const seen = new Set(front);
  const rest = order.filter((k) => !seen.has(k));
  const frontOrdered = front.filter((k) => order.includes(k));
  return [...frontOrdered, ...rest];
}

export const OPERATOR_MODE_DEFINITIONS: Record<OperatorModeId, OperatorModeDefinition> = {
  DAILY_OPS: {
    mode_id: "DAILY_OPS",
    label: "Daily Ops",
    purpose: "Routine health, readiness, providers, evidence, workboard, and runtime posture.",
    primary_panes: [
      "Seven-pane grid (Overview, Readiness, Evidence chain, Providers, Operator actions, Workboard, Runtime)",
      "Operator health / alerts",
      "Candidate workbench",
      "Research OS + Paper execution drilldowns",
      "Capital / execution firewall",
    ],
    secondary_panes: [
      "Topology",
      "First run",
      "Release control",
      "Remediation",
      "Forensic / policy / promotion",
    ],
    recommended_next_action_source: "Probe + /readyz + GET /ui/evidence + GET /ui/facade + provider health (existing hooks).",
    safety: "COMMAND_CAPABLE",
    command_warning:
      "Operator command surface is token-gated server-side. Use only with production auth posture; browser does not execute shell commands.",
  },
  FIRST_RUN: {
    mode_id: "FIRST_RUN",
    label: "First Run / Setup",
    purpose: "Deployment tier, checklist, provider setup, and readiness before claiming frontend readiness.",
    primary_panes: ["First-run deployment cockpit", "Provider setup readiness", "Operator health / alerts", "Remediation / policy context"],
    secondary_panes: ["Seven-pane grid", "Topology", "Release control", "Research drilldowns"],
    recommended_next_action_source: "GET /readiness/deployment, /readyz, first-run checklist inputs, GET /ui/provider-setup.",
    safety: "READ_PLANE_ONLY",
    command_warning: null,
  },
  RESEARCH_REVIEW: {
    mode_id: "RESEARCH_REVIEW",
    label: "Research Review",
    purpose: "Strategy lifecycle, batches, backtests, paper tracking, and research OS evidence rows.",
    primary_panes: ["Candidate workbench", "Strategy lifecycle", "Research batch forensics", "Research OS + Paper drilldowns"],
    secondary_panes: ["Seven-pane grid", "Evidence runbook", "Promotion dossier", "Topology"],
    recommended_next_action_source: "GET /ui/research-os/status (aggregated), strategy batch + backtest forensics routes, lifecycle payloads.",
    safety: "READ_PLANE_ONLY",
    command_warning: null,
  },
  RELEASE_CONTROL: {
    mode_id: "RELEASE_CONTROL",
    label: "Release Control",
    purpose: "Evidence bundle, release readiness, handoff, signoff, and review journal read surfaces.",
    primary_panes: ["Release control", "Evidence runbook", "Promotion evidence dossier", "Seven-pane grid (evidence + facade tiles)"],
    secondary_panes: ["Research OS drilldown", "Audit forensic", "Topology"],
    recommended_next_action_source: "GET /ui/evidence, GET /ui/research-os/* latest payloads, registry CLI hints (copy-only).",
    safety: "COMMAND_CAPABLE",
    command_warning:
      "Release workflows may reference authenticated operator commands elsewhere; run sensitive CLIs only on trusted workstations.",
  },
  INCIDENT_RESPONSE: {
    mode_id: "INCIDENT_RESPONSE",
    label: "Incident Response",
    purpose: "Health alerts, remediation, exceptions, drift, and readiness blockers.",
    primary_panes: ["Operator health / alerts", "Incident / remediation / exceptions", "Operator command cockpit (posture only)"],
    secondary_panes: ["Capital firewall", "Policy / risk gates", "Seven-pane grid", "Topology"],
    recommended_next_action_source: "/healthz, /readyz, GET /ui/runtime mutation_safety, Research OS exception/remediation routes.",
    safety: "COMMAND_CAPABLE",
    command_warning: "Incident playbooks may pair read-plane triage with token-gated mutations; verify mutation_safety before acting.",
  },
  FORENSIC_AUDIT: {
    mode_id: "FORENSIC_AUDIT",
    label: "Forensic Audit",
    purpose: "Evidence chain integrity, audit timeline, exports, drift, and operator action projections.",
    primary_panes: ["Audit forensic", "Evidence runbook", "Evidence chain (grid pane)", "Research OS + Paper drilldowns"],
    secondary_panes: ["Promotion dossier", "Topology", "Seven-pane grid"],
    recommended_next_action_source: "GET /ui/evidence-chain, operator-actions projection, audit pane payloads.",
    safety: "READ_PLANE_ONLY",
    command_warning: null,
  },
  CAPITAL_FIREWALL: {
    mode_id: "CAPITAL_FIREWALL",
    label: "Capital Firewall",
    purpose: "Paper execution, broker status, tracking, provider posture, and execution authority hints.",
    primary_panes: ["Capital / execution firewall", "Paper execution drilldown", "Policy / risk gates"],
    secondary_panes: ["Seven-pane grid (runtime)", "Research paper drilldown", "Topology"],
    recommended_next_action_source: "GET /ui/paper-execution/latest, GET /ui/paper-broker/status, GET /ui/paper-tracking/latest, GET /ui/runtime.",
    safety: "READ_PLANE_ONLY",
    command_warning: null,
  },
  SYSTEM_TOPOLOGY: {
    mode_id: "SYSTEM_TOPOLOGY",
    label: "System Topology",
    purpose: "Pane → hook → route → builder → CLI → CI map; UNKNOWN for missing links.",
    primary_panes: ["System topology / dependency map", "Runtime pane (within grid)", "Facade inventory"],
    secondary_panes: ["Seven-pane grid", "Operator health (degraded hints)"],
    recommended_next_action_source: "ui-facade-routes.json + local-ops-command-registry.json + curated pane table.",
    safety: "READ_PLANE_ONLY",
    command_warning: null,
  },
};

export const OPERATOR_MODE_IDS: OperatorModeId[] = [
  "DAILY_OPS",
  "FIRST_RUN",
  "RESEARCH_REVIEW",
  "RELEASE_CONTROL",
  "INCIDENT_RESPONSE",
  "FORENSIC_AUDIT",
  "CAPITAL_FIREWALL",
  "SYSTEM_TOPOLOGY",
];

export function getPostGridSectionOrder(mode: OperatorModeId): CockpitPostGridSectionKey[] {
  const base = [...COCKPIT_POST_GRID_SECTION_ORDER];
  switch (mode) {
    case "DAILY_OPS":
      return base;
    case "FIRST_RUN":
      return moveKeysToFront(base, ["first_run", "provider_setup", "operator_health", "remediation", "topology"]);
    case "RESEARCH_REVIEW":
      return moveKeysToFront(base, [
        "candidate_workbench",
        "strategy_lifecycle",
        "research_batch",
        "research_paper_drilldown",
        "promotion_dossier",
        "evidence_runbook",
      ]);
    case "RELEASE_CONTROL":
      return moveKeysToFront(base, ["release_control", "evidence_runbook", "promotion_dossier", "audit_forensic", "research_paper_drilldown"]);
    case "INCIDENT_RESPONSE":
      return moveKeysToFront(base, ["operator_health", "remediation", "operator_command", "capital_firewall", "policy_risk"]);
    case "FORENSIC_AUDIT":
      return moveKeysToFront(base, ["audit_forensic", "evidence_runbook", "research_paper_drilldown", "promotion_dossier", "topology"]);
    case "CAPITAL_FIREWALL":
      return moveKeysToFront(base, ["capital_firewall", "research_paper_drilldown", "policy_risk", "operator_health"]);
    case "SYSTEM_TOPOLOGY":
      return moveKeysToFront(base, ["topology", "operator_health", "research_paper_drilldown"]);
    default:
      return base;
  }
}

export function getOperatorModeDefinition(mode: OperatorModeId): OperatorModeDefinition {
  return OPERATOR_MODE_DEFINITIONS[mode];
}

export function modeShowsOperatorCommandPane(mode: OperatorModeId): boolean {
  return OPERATOR_MODE_DEFINITIONS[mode].safety === "COMMAND_CAPABLE";
}

/** Plain context from cockpit hooks — no fabricated pass/fail. */
export type OperatorModeFocusContext = {
  readyStatus: string;
  anyHookError: boolean;
  deploymentReadinessFailed: boolean;
  deploymentBlockerCodes: readonly string[];
  deploymentWarningCodes: readonly string[];
  cockpitDeploymentStatus: string | null | undefined;
  operatorHealthFailed: boolean;
  researchLifecycleFailed: boolean;
  releaseControlFailed: boolean;
  remediationFailed: boolean;
  paperCapitalFailed: boolean;
  auditForensicFailed: boolean;
  topologyContractUnknown: boolean;
  chainIntegrityLabel: string | null | undefined;
};

export function deriveOperatorModeNextFocusLines(mode: OperatorModeId, ctx: OperatorModeFocusContext): string[] {
  const lines: string[] = [];
  const dep = (ctx.cockpitDeploymentStatus ?? "UNKNOWN").toString();
  const chain = (ctx.chainIntegrityLabel ?? "UNKNOWN").toString();

  const pushUnknown = (label: string, failed: boolean) => {
    if (failed) lines.push(`${label}: DEGRADED — read-plane query failed; treat as UNKNOWN until restored.`);
  };

  switch (mode) {
    case "FIRST_RUN":
      pushUnknown("GET /readiness/deployment", ctx.deploymentReadinessFailed);
      if (ctx.deploymentBlockerCodes.length > 0) {
        lines.push(`Review deployment tier blockers (${ctx.deploymentBlockerCodes.length}): ${ctx.deploymentBlockerCodes.slice(0, 8).join(", ")}`);
      } else if (!ctx.deploymentReadinessFailed) {
        lines.push("Compare GET /readiness/deployment with /readyz and first-run checklist (no PASS claim implied).");
      }
      if (ctx.deploymentWarningCodes.length > 0) {
        lines.push(`Warnings present (${ctx.deploymentWarningCodes.length}); see deployment payload — not auto-approved.`);
      }
      break;
    case "DAILY_OPS":
      pushUnknown("Operator health bundle", ctx.operatorHealthFailed);
      lines.push(`Readiness status: ${ctx.readyStatus} (from /readyz).`);
      lines.push(`Deployment evidence label: ${dep} (from GET /ui/evidence cockpit fields).`);
      if (ctx.anyHookError) lines.push("One or more read-plane hooks failed; prioritize failing route in Operator health.");
      break;
    case "RESEARCH_REVIEW":
      pushUnknown("Strategy lifecycle bundle", ctx.researchLifecycleFailed);
      lines.push("Triage strategy lifecycle + batch/forensics panes; evidence remains advisory until you open payloads.");
      break;
    case "RELEASE_CONTROL":
      pushUnknown("Release control bundle", ctx.releaseControlFailed);
      lines.push("Follow evidence runbook + release control panes; signoff state only as returned by GET routes.");
      break;
    case "INCIDENT_RESPONSE":
      pushUnknown("Remediation / governance bundle", ctx.remediationFailed);
      pushUnknown("Operator health bundle", ctx.operatorHealthFailed);
      lines.push("Check exceptions/remediation/latest payloads and /readyz blockers — no root cause without payload proof.");
      break;
    case "FORENSIC_AUDIT":
      pushUnknown("Audit forensic bundle", ctx.auditForensicFailed);
      lines.push(`Evidence chain integrity label: ${chain} (projection-only).`);
      break;
    case "CAPITAL_FIREWALL":
      pushUnknown("Capital / execution firewall bundle", ctx.paperCapitalFailed);
      lines.push("Review paper execution + broker + tracking read routes; browser does not submit orders.");
      break;
    case "SYSTEM_TOPOLOGY":
      if (ctx.topologyContractUnknown) {
        lines.push("Topology contract: UNKNOWN — ui-facade route bundle not loaded in model input.");
      } else {
        lines.push("Use topology map to find pane → hook → route; missing links stay UNKNOWN.");
      }
      pushUnknown("Operator health (for degraded hints)", ctx.operatorHealthFailed);
      break;
  }

  if (lines.length === 0) lines.push("PENDING — no derived focus for this mode.");
  return lines.slice(0, 8);
}