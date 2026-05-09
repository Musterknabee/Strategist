/**
 * Frontend-only command palette entries (navigation + read-plane refresh). No mutations.
 */
export type TerminalCommand = {
  id: string;
  label: string;
  keywords?: string[];
  action:
    | { type: "nav"; path: string }
    | { type: "refresh-all" }
    | { type: "refresh-visible" }
    | { type: "toggle-raw-json" }
    | { type: "open-palette" }
    | { type: "close-overlays" }
    | { type: "focus-tape" }
    | { type: "focus-alerts" }
    | { type: "copy-last-digest" }
    | { type: "shortcut-help" };
};

/** Second key after G (lowercase). Must match `Go: *` nav paths in this registry. */
export const G_CHORD_ROUTES: Record<string, string> = {
  o: "/",
  w: "/workboard",
  r: "/readiness",
  e: "/evidence",
  "]": "/evidence-chain",
  g: "/evidence-bundles",
  x: "/operator-packs",
  k: "/operator-actions",
  ";": "/operator-command-policy",
  l: "/ledger",
  "[": "/tribunal",
  p: "/providers",
  f: "/backtest-forensics",
  "\\": "/promotion-review",
  t: "/runtime",
  ",": "/research-compute",
  ".": "/projection-registry",
  "=": "/semantic-release",
  "_": "/semantic-validator-handoff",
  "-": "/semantic-validator-handoff-lineage",
  "+": "/semantic-validator-handoff-remediation",
  "*": "/semantic-validator-handoff-review",
  "!": "/semantic-validator-handoff-decision",
  "?": "/semantic-validator-handoff-signoff",
  "/": "/semantic-validator-handoff-custody",
  "'": "/semantic-validator-handoff-archive",
  ":": "/semantic-validator-handoff-closure",
  "~": "/semantic-validator-handoff-continuity",
  "`": "/semantic-validator-handoff-runbook",
  "@": "/semantic-validator-handoff-exceptions",
  "#": "/semantic-validator-handoff-timeline",
  "%": "/semantic-validator-handoff-evidence-gaps",
  "^": "/semantic-validator-handoff-audit-packet",
  b: "/shadow-book",
  c: "/research-closure",
  a: "/research-attestation",
  d: "/research-briefing",
  z: "/research-export",
  u: "/research-run",
  i: "/research-catalog",
  v: "/research-drift",
  y: "/research-policy-gate",
  n: "/research-exception",
  m: "/research-remediation",
  q: "/research-release-readiness",
  h: "/research-handoff",
  s: "/research-handoff-signoff",
  j: "/research-review-journal",
};

export const TERMINAL_COMMANDS: TerminalCommand[] = [
  { id: "go-overview", label: "Go: Overview", keywords: ["home", "index"], action: { type: "nav", path: "/" } },
  { id: "go-workboard", label: "Go: Workboard", keywords: ["queue", "wb"], action: { type: "nav", path: "/workboard" } },
  { id: "go-readiness", label: "Go: Readiness", keywords: ["ready", "health"], action: { type: "nav", path: "/readiness" } },
  { id: "go-evidence", label: "Go: Evidence", keywords: ["deploy", "proof"], action: { type: "nav", path: "/evidence" } },
  { id: "go-evidence-chain", label: "Go: Evidence Chain", keywords: ["chain", "integrity", "ledger", "journal", "hash"], action: { type: "nav", path: "/evidence-chain" } },
  { id: "go-evidence-bundles", label: "Go: Evidence Bundles", keywords: ["bundle", "archive", "handoff", "digest"], action: { type: "nav", path: "/evidence-bundles" } },
  { id: "go-operator-packs", label: "Go: Operator Packs", keywords: ["packs", "workbench", "queue", "claims", "lease"], action: { type: "nav", path: "/operator-packs" } },
  { id: "go-operator-actions", label: "Go: Operator Actions", keywords: ["journal", "commands", "actions", "operator", "chain"], action: { type: "nav", path: "/operator-actions" } },
  { id: "go-operator-command-policy", label: "Go: Command Policy", keywords: ["commands", "policy", "mutation", "auth", "token"], action: { type: "nav", path: "/operator-command-policy" } },
  { id: "go-ledger", label: "Go: Ledger", keywords: ["journal", "actions"], action: { type: "nav", path: "/ledger" } },
  { id: "go-tribunal", label: "Go: Tribunal", keywords: ["qualitative", "blindness", "judge", "skeptic", "citations"], action: { type: "nav", path: "/tribunal" } },
  { id: "go-providers", label: "Go: Providers", keywords: ["market", "data"], action: { type: "nav", path: "/providers" } },
  { id: "go-market-data-integrity", label: "Go: Market Data Integrity", keywords: ["market", "data", "integrity", "stale", "adjusted", "survivorship"], action: { type: "nav", path: "/market-data-integrity" } },
  { id: "go-backtest-forensics", label: "Go: Backtest Forensics", keywords: ["backtest", "forensics", "promotion", "evidence", "strategy batch", "risk flags"], action: { type: "nav", path: "/backtest-forensics" } },
  { id: "go-promotion-review", label: "Go: Promotion Review", keywords: ["promotion", "review", "packet", "human", "paper tracking", "candidate"], action: { type: "nav", path: "/promotion-review" } },
  { id: "go-runtime", label: "Go: Runtime", keywords: ["sys", "env"], action: { type: "nav", path: "/runtime" } },
  { id: "go-research-compute", label: "Go: Research Compute", keywords: ["compute", "gpu", "cuda", "monte carlo", "benchmark"], action: { type: "nav", path: "/research-compute" } },
  { id: "go-projection-registry", label: "Go: Projection Registry", keywords: ["projection", "registry", "backfill", "checkpoint", "artifact index"], action: { type: "nav", path: "/projection-registry" } },
  { id: "go-semantic-release", label: "Go: Semantic Release", keywords: ["semantic", "release", "handoff", "capsule", "decision", "adjudication"], action: { type: "nav", path: "/semantic-release" } },
  { id: "go-semantic-validator-handoff", label: "Go: Semantic Validator Handoff", keywords: ["semantic", "validator", "handoff", "packet", "ingress", "certificate"], action: { type: "nav", path: "/semantic-validator-handoff" } },
  { id: "go-semantic-validator-handoff-lineage", label: "Go: Semantic Validator Handoff Lineage", keywords: ["semantic", "validator", "handoff", "lineage", "continuity", "checksum", "packet", "ingress"], action: { type: "nav", path: "/semantic-validator-handoff-lineage" } },
  { id: "go-semantic-validator-handoff-remediation", label: "Go: Semantic Validator Handoff Remediation", keywords: ["semantic", "validator", "handoff", "remediation", "repair", "checksum", "lineage", "missing"], action: { type: "nav", path: "/semantic-validator-handoff-remediation" } },
  { id: "go-semantic-validator-handoff-review", label: "Go: Semantic Validator Handoff Review", keywords: ["semantic", "validator", "handoff", "review", "gate", "trust", "checklist", "operator"], action: { type: "nav", path: "/semantic-validator-handoff-review" } },
  { id: "go-semantic-validator-handoff-decision", label: "Go: Semantic Validator Handoff Decision", keywords: ["semantic", "validator", "handoff", "decision", "dossier", "signoff", "operator", "digest"], action: { type: "nav", path: "/semantic-validator-handoff-decision" } },
  { id: "go-semantic-validator-handoff-signoff", label: "Go: Semantic Validator Handoff Signoff", keywords: ["semantic", "validator", "handoff", "signoff", "receipt", "operator", "digest", "human"], action: { type: "nav", path: "/semantic-validator-handoff-signoff" } },
  { id: "go-semantic-validator-handoff-custody", label: "Go: Semantic Validator Handoff Custody", keywords: ["semantic", "validator", "handoff", "custody", "seal", "archive", "digest"], action: { type: "nav", path: "/semantic-validator-handoff-custody" } },
  { id: "go-semantic-validator-handoff-archive", label: "Go: Semantic Validator Handoff Archive", keywords: ["semantic", "validator", "handoff", "archive", "manifest", "custody", "audit"], action: { type: "nav", path: "/semantic-validator-handoff-archive" } },
  { id: "go-semantic-validator-handoff-closure", label: "Go: Semantic Validator Handoff Closure", keywords: ["semantic", "validator", "handoff", "closure", "attestation", "archive", "audit"], action: { type: "nav", path: "/semantic-validator-handoff-closure" } },
  { id: "go-semantic-validator-handoff-continuity", label: "Go: Semantic Validator Handoff Continuity", keywords: ["semantic", "validator", "handoff", "continuity", "chain", "timeline", "audit", "closure"], action: { type: "nav", path: "/semantic-validator-handoff-continuity" } },
  { id: "go-semantic-validator-handoff-runbook", label: "Go: Semantic Validator Handoff Runbook", keywords: ["semantic", "validator", "handoff", "runbook", "next action", "operator", "closure", "checklist"], action: { type: "nav", path: "/semantic-validator-handoff-runbook" } },
  { id: "go-semantic-validator-handoff-exceptions", label: "Go: Semantic Validator Handoff Exceptions", keywords: ["semantic", "validator", "handoff", "exceptions", "queue", "blocked", "integrity", "operator"], action: { type: "nav", path: "/semantic-validator-handoff-exceptions" } },
  { id: "go-semantic-validator-handoff-timeline", label: "Go: Semantic Validator Handoff Timeline", keywords: ["semantic", "validator", "handoff", "timeline", "stage", "chain", "event", "audit"], action: { type: "nav", path: "/semantic-validator-handoff-timeline" } },
  { id: "go-semantic-validator-handoff-evidence-gaps", label: "Go: Semantic Validator Handoff Evidence Gaps", keywords: ["semantic", "validator", "handoff", "evidence", "gap", "missing", "artifact", "repair"], action: { type: "nav", path: "/semantic-validator-handoff-evidence-gaps" } },
  { id: "go-semantic-validator-handoff-audit-packet", label: "Go: Semantic Validator Handoff Audit Packet", keywords: ["semantic", "validator", "handoff", "audit", "packet", "consolidated", "closure"], action: { type: "nav", path: "/semantic-validator-handoff-audit-packet" } },
  { id: "go-semantic-validator-handoff-action-queue", label: "Go: Semantic Validator Handoff Action Queue", keywords: ["semantic", "validator", "handoff", "action", "queue", "repair", "external", "blocked"], action: { type: "nav", path: "/semantic-validator-handoff-action-queue" } },
  { id: "go-semantic-validator-handoff-escalation-board", label: "Go: Semantic Validator Handoff Escalation Board", keywords: ["semantic", "validator", "handoff", "escalation", "board", "blocker", "external", "priority"], action: { type: "nav", path: "/semantic-validator-handoff-escalation-board" } },
  { id: "go-semantic-validator-handoff-resolution-plan", label: "Go: Semantic Validator Handoff Resolution Plan", keywords: ["semantic", "validator", "handoff", "resolution", "plan", "remediation", "blocker", "external"], action: { type: "nav", path: "/semantic-validator-handoff-resolution-plan" } },
  { id: "go-semantic-validator-handoff-clearance-gate", label: "Go: Semantic Validator Handoff Clearance Gate", keywords: ["semantic", "validator", "handoff", "clearance", "gate", "approval", "signoff", "blocked"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-gate" } },
  { id: "go-semantic-validator-handoff-clearance-dossier", label: "Go: Semantic Validator Handoff Clearance Dossier", keywords: ["semantic", "validator", "handoff", "clearance", "dossier", "review", "approval", "signoff"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-dossier" } },
  { id: "go-semantic-validator-handoff-clearance-checklist", label: "Go: Semantic Validator Handoff Clearance Checklist", keywords: ["semantic", "validator", "handoff", "clearance", "checklist", "checks", "approval", "signoff", "ack"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-checklist" } },
  { id: "go-semantic-validator-handoff-clearance-evidence-matrix", label: "Go: Semantic Validator Handoff Clearance Evidence Matrix", keywords: ["semantic", "validator", "handoff", "clearance", "evidence", "matrix", "coverage", "attest", "override"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-evidence-matrix" } },
  { id: "go-semantic-validator-handoff-clearance-coverage-board", label: "Go: Semantic Validator Handoff Clearance Coverage Board", keywords: ["semantic", "validator", "handoff", "clearance", "coverage", "board", "evidence", "lane", "attest"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-coverage-board" } },
  { id: "go-semantic-validator-handoff-clearance-operations-board", label: "Go: Semantic Validator Handoff Clearance Operations Board", keywords: ["semantic", "validator", "handoff", "clearance", "operations", "triage", "coverage", "operator", "readiness"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-operations-board" } },
  { id: "go-semantic-validator-handoff-clearance-action-register", label: "Go: Semantic Validator Handoff Clearance Action Register", keywords: ["semantic", "validator", "handoff", "clearance", "action", "register", "triage", "operator", "firewall"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-action-register" } },
  { id: "go-semantic-validator-handoff-clearance-resolution-plan", label: "Go: Semantic Validator Handoff Clearance Resolution Plan", keywords: ["semantic", "validator", "handoff", "clearance", "resolution", "plan", "repair", "external", "blocker"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-resolution-plan" } },
  { id: "go-semantic-validator-handoff-clearance-verification-board", label: "Go: Semantic Validator Handoff Clearance Verification Board", keywords: ["semantic", "validator", "handoff", "clearance", "verification", "board", "fail", "closed", "completion"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-verification-board" } },
  { id: "go-semantic-validator-handoff-clearance-closeout-board", label: "Go: Semantic Validator Handoff Clearance Closeout Board", keywords: ["semantic", "validator", "handoff", "clearance", "closeout", "board", "review", "ready", "signoff"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-closeout-board" } },
  { id: "go-semantic-validator-handoff-clearance-review-docket", label: "Go: Semantic Validator Handoff Clearance Review Docket", keywords: ["semantic", "validator", "handoff", "clearance", "review", "docket", "authorized", "signoff", "approval"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-review-docket" } },
  { id: "go-semantic-validator-handoff-clearance-signoff-packet", label: "Go: Semantic Validator Handoff Clearance Signoff Packet", keywords: ["semantic", "validator", "handoff", "clearance", "signoff", "packet", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-signoff-packet" } },
  { id: "go-semantic-validator-handoff-clearance-acceptance-board", label: "Go: Semantic Validator Handoff Clearance Acceptance Board", keywords: ["semantic", "validator", "handoff", "clearance", "acceptance", "board", "human", "signoff", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-acceptance-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-readiness-board", label: "Go: Semantic Validator Handoff Clearance Release Readiness Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "readiness", "acceptance", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-readiness-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-packet", label: "Go: Semantic Validator Handoff Clearance Release Packet", keywords: ["semantic", "validator", "handoff", "clearance", "release", "packet", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-packet" } },
  { id: "go-semantic-validator-handoff-clearance-release-handoff-board", label: "Go: Semantic Validator Handoff Clearance Release Handoff Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "handoff", "transfer", "packet", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-handoff-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-custody-board", label: "Go: Semantic Validator Handoff Clearance Release Custody Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "custody", "transfer", "handoff", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-custody-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-receipt-board", label: "Go: Semantic Validator Handoff Clearance Release Receipt Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "receipt", "custody", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-receipt-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-acknowledgment-board", label: "Go: Semantic Validator Handoff Clearance Release Acknowledgment Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "acknowledgment", "receipt", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-acknowledgment-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-confirmation-board", label: "Go: Semantic Validator Handoff Clearance Release Confirmation Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "confirmation", "acknowledgment", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-confirmation-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-completion-board", label: "Go: Semantic Validator Handoff Clearance Release Completion Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "completion", "confirmation", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-completion-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-closure-board", label: "Go: Semantic Validator Handoff Clearance Release Closure Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "closure", "completion", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-closure-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-archive-board", label: "Go: Semantic Validator Handoff Clearance Release Archive Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "archive", "closure", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-archive-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-retention-board", label: "Go: Semantic Validator Handoff Clearance Release Retention Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "retention", "archive", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-retention-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-disposition-board", label: "Go: Semantic Validator Handoff Clearance Release Disposition Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "disposition", "retention", "archive", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-disposition-board" } },
  { id: "go-semantic-validator-handoff-clearance-release-disposal-board", label: "Go: Semantic Validator Handoff Clearance Release Disposal Board", keywords: ["semantic", "validator", "handoff", "clearance", "release", "disposal", "disposition", "retention", "record", "human", "approval", "decision"], action: { type: "nav", path: "/semantic-validator-handoff-clearance-release-disposal-board" } },
  { id: "go-shadow-book", label: "Go: Shadow Book", keywords: ["paper", "portfolio", "book"], action: { type: "nav", path: "/shadow-book" } },
  { id: "go-research-closure", label: "Go: Research Closure", keywords: ["closure", "evidence", "digest"], action: { type: "nav", path: "/research-closure" } },
  { id: "go-research-attestation", label: "Go: Research Attestation", keywords: ["attestation", "verify", "signoff"], action: { type: "nav", path: "/research-attestation" } },
  { id: "go-research-briefing", label: "Go: Research Briefing", keywords: ["briefing", "daily", "operator"], action: { type: "nav", path: "/research-briefing" } },
  { id: "go-research-export", label: "Go: Research Export", keywords: ["export", "bundle", "audit"], action: { type: "nav", path: "/research-export" } },
  { id: "go-research-run", label: "Go: Research Run", keywords: ["run", "operator", "daily"], action: { type: "nav", path: "/research-run" } },
  { id: "go-research-catalog", label: "Go: Research Catalog", keywords: ["catalog", "inventory", "evidence", "timeline"], action: { type: "nav", path: "/research-catalog" } },
  { id: "go-research-drift", label: "Go: Research Drift", keywords: ["drift", "diff", "catalog", "change"], action: { type: "nav", path: "/research-drift" } },
  { id: "go-research-policy-gate", label: "Go: Research Policy Gate", keywords: ["policy", "gate", "pass", "block", "warn"], action: { type: "nav", path: "/research-policy-gate" } },
  { id: "go-research-exception", label: "Go: Research Exception", keywords: ["exception", "override", "constraint", "warn"], action: { type: "nav", path: "/research-exception" } },
  { id: "go-research-remediation", label: "Go: Research Remediation", keywords: ["remediation", "action", "queue", "fix"], action: { type: "nav", path: "/research-remediation" } },
  { id: "go-research-release-readiness", label: "Go: Research Release Readiness", keywords: ["release", "readiness", "review", "single tenant"], action: { type: "nav", path: "/research-release-readiness" } },
  { id: "go-research-handoff", label: "Go: Research Handoff", keywords: ["handoff", "release", "operator", "single tenant"], action: { type: "nav", path: "/research-handoff" } },
  { id: "go-research-handoff-signoff", label: "Go: Research Handoff Signoff", keywords: ["handoff", "signoff", "verify", "reviewer"], action: { type: "nav", path: "/research-handoff-signoff" } },
  { id: "go-research-review-journal", label: "Go: Research Review Journal", keywords: ["journal", "review", "decision", "ledger"], action: { type: "nav", path: "/research-review-journal" } },
  {
    id: "refresh-route",
    label: "Refresh current route queries",
    keywords: ["page", "visible", "r"],
    action: { type: "refresh-visible" },
  },
  {
    id: "refresh-all",
    label: "Refresh all read-plane queries (full)",
    keywords: ["reload", "invalidate", "everything"],
    action: { type: "refresh-all" },
  },
  { id: "toggle-raw", label: "Toggle raw JSON drilldown mode", keywords: ["json"], action: { type: "toggle-raw-json" } },
  { id: "palette", label: "Open command palette", keywords: ["cmd", "k"], action: { type: "open-palette" } },
  { id: "close", label: "Close palette / inspector / help", keywords: ["esc"], action: { type: "close-overlays" } },
  { id: "tape", label: "Focus event tape", keywords: ["log", "events"], action: { type: "focus-tape" } },
  { id: "alerts", label: "Focus status rail", keywords: ["rail"], action: { type: "focus-alerts" } },
  { id: "copy-digest", label: "Copy last digest (if set)", keywords: ["clipboard"], action: { type: "copy-last-digest" } },
  { id: "shortcuts", label: "Keyboard shortcuts", keywords: ["help", "?"], action: { type: "shortcut-help" } },
];

export function filterCommands(query: string, commands: TerminalCommand[] = TERMINAL_COMMANDS): TerminalCommand[] {
  const q = query.trim().toLowerCase();
  if (!q) return commands;
  return commands.filter((c) => {
    if (c.label.toLowerCase().includes(q)) return true;
    if (c.keywords?.some((k) => k.includes(q) || q.includes(k))) return true;
    if (c.id.toLowerCase().includes(q)) return true;
    return false;
  });
}
