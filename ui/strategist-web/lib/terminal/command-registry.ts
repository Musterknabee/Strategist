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
  l: "/ledger",
  p: "/providers",
  t: "/runtime",
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
  { id: "go-ledger", label: "Go: Ledger", keywords: ["journal", "actions"], action: { type: "nav", path: "/ledger" } },
  { id: "go-providers", label: "Go: Providers", keywords: ["market", "data"], action: { type: "nav", path: "/providers" } },
  { id: "go-runtime", label: "Go: Runtime", keywords: ["sys", "env"], action: { type: "nav", path: "/runtime" } },
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
