/**
 * Frontend-only command palette entries (navigation + read-plane refresh). No mutations.
 */
export type TerminalCommandGroup = "Ops" | "Research" | "Evidence" | "Release" | "Tools";

export type TerminalNavItem = {
  id: string;
  label: string;
  path: string;
  icon: string;
  group: Exclude<TerminalCommandGroup, "Tools">;
  description: string;
  keywords?: string[];
};

export type TerminalNavGroup = {
  id: string;
  label: Exclude<TerminalCommandGroup, "Tools">;
  items: TerminalNavItem[];
};

export type TerminalCommand = {
  id: string;
  label: string;
  group?: TerminalCommandGroup;
  description?: string;
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

export const TERMINAL_NAV_GROUPS: TerminalNavGroup[] = [
  {
    id: "ops",
    label: "Ops",
    items: [
      { id: "go-overview", label: "Go: Overview", path: "/", icon: "O", group: "Ops", description: "Home cockpit and guided operator path.", keywords: ["home", "index"] },
      { id: "go-workboard", label: "Go: Workboard", path: "/workboard", icon: "W", group: "Ops", description: "Operator queue, work items, and pack workbench.", keywords: ["queue", "wb"] },
      { id: "go-daily-operator-run", label: "Go: Daily Operator Run", path: "/daily-operator-run", icon: "D", group: "Ops", description: "Composite daily checklist and recommended next actions.", keywords: ["daily", "briefing", "checklist"] },
      { id: "go-readiness", label: "Go: Readiness", path: "/readiness", icon: "R", group: "Ops", description: "Readiness checks and blockers.", keywords: ["ready", "health"] },
      { id: "go-providers", label: "Go: Providers", path: "/providers", icon: "P", group: "Ops", description: "Provider/data posture.", keywords: ["market", "data"] },
      { id: "go-runtime", label: "Go: Runtime", path: "/runtime", icon: "T", group: "Ops", description: "Runtime, read-plane, and mutation-safety status.", keywords: ["sys", "env"] },
    ],
  },
  {
    id: "research",
    label: "Research",
    items: [
      { id: "go-strategy-inbox", label: "Go: Strategy Inbox", path: "/strategy-inbox", icon: "I", group: "Research", description: "Advisory intake queue and proposal capture.", keywords: ["inbox", "intake", "proposal"] },
      { id: "go-strategy-lab", label: "Go: Strategy Lab", path: "/strategy-lab", icon: "S", group: "Research", description: "Strategy tests, forensics, and research diagnostics.", keywords: ["strategy", "lab", "test"] },
      { id: "go-paper-tracking", label: "Go: Paper Tracking", path: "/paper-tracking", icon: "K", group: "Research", description: "Paper-only lifecycle and tracking posture.", keywords: ["paper", "tracking"] },
      { id: "go-strategy-memory", label: "Go: Strategy Memory", path: "/strategy-memory", icon: "M", group: "Research", description: "Strategy memory and duplicate warnings.", keywords: ["memory", "graveyard", "duplicate"] },
      { id: "go-strategy-graveyard", label: "Go: Strategy Graveyard", path: "/strategy-graveyard", icon: "G", group: "Research", description: "Rejected strategies, resurrection rules, and research memory.", keywords: ["graveyard", "killed", "rejected", "resurrection"] },
      { id: "go-thesis", label: "Go: Thesis", path: "/thesis", icon: "F", group: "Research", description: "Thesis and falsification evidence.", keywords: ["thesis", "falsification"] },
      { id: "go-shadow-book", label: "Go: Shadow Book", path: "/shadow-book", icon: "B", group: "Research", description: "Paper portfolio and shadow-book views.", keywords: ["paper", "portfolio", "book"] },
    ],
  },
  {
    id: "evidence",
    label: "Evidence",
    items: [
      { id: "go-evidence", label: "Go: Evidence", path: "/evidence", icon: "E", group: "Evidence", description: "Deployment evidence and proof status.", keywords: ["deploy", "proof"] },
      { id: "go-ledger", label: "Go: Ledger", path: "/ledger", icon: "L", group: "Evidence", description: "Operator action ledger.", keywords: ["journal", "actions"] },
      { id: "go-research-catalog", label: "Go: Research Catalog", path: "/research-catalog", icon: "C", group: "Evidence", description: "Evidence catalog and inventory.", keywords: ["catalog", "inventory", "evidence", "timeline"] },
      { id: "go-research-drift", label: "Go: Research Drift", path: "/research-drift", icon: "V", group: "Evidence", description: "Evidence drift and catalog change posture.", keywords: ["drift", "diff", "catalog", "change"] },
      { id: "go-research-review-journal", label: "Go: Research Review Journal", path: "/research-review-journal", icon: "J", group: "Evidence", description: "Review journal and decision evidence.", keywords: ["journal", "review", "decision", "ledger"] },
    ],
  },
  {
    id: "release",
    label: "Release",
    items: [
      { id: "go-research-os", label: "Go: Research OS", path: "/research-os", icon: "X", group: "Release", description: "Research OS aggregate status.", keywords: ["research os", "operating system"] },
      { id: "go-paper-execution", label: "Go: Paper Execution", path: "/paper-execution", icon: "P", group: "Release", description: "Paper-only execution evidence, receipts, and guarded dry-runs.", keywords: ["paper", "execution", "dry-run", "receipt"] },
      { id: "go-research-run", label: "Go: Research Run", path: "/research-run", icon: "U", group: "Release", description: "Operator research run status.", keywords: ["run", "operator", "daily"] },
      { id: "go-research-closure", label: "Go: Research Closure", path: "/research-closure", icon: "C", group: "Release", description: "Closure evidence and digests.", keywords: ["closure", "evidence", "digest"] },
      { id: "go-research-attestation", label: "Go: Research Attestation", path: "/research-attestation", icon: "A", group: "Release", description: "Attestation and verification views.", keywords: ["attestation", "verify", "signoff"] },
      { id: "go-research-briefing", label: "Go: Research Briefing", path: "/research-briefing", icon: "D", group: "Release", description: "Briefing packet status.", keywords: ["briefing", "daily", "operator"] },
      { id: "go-research-export", label: "Go: Research Export", path: "/research-export", icon: "Z", group: "Release", description: "Export manifests and bundles.", keywords: ["export", "bundle", "audit"] },
      { id: "go-research-policy-gate", label: "Go: Research Policy Gate", path: "/research-policy-gate", icon: "Y", group: "Release", description: "Policy gate pass/block/warn status.", keywords: ["policy", "gate", "pass", "block", "warn"] },
      { id: "go-research-exception", label: "Go: Research Exception", path: "/research-exception", icon: "N", group: "Release", description: "Exceptions and constraints.", keywords: ["exception", "override", "constraint", "warn"] },
      { id: "go-research-remediation", label: "Go: Research Remediation", path: "/research-remediation", icon: "M", group: "Release", description: "Remediation queue and repair posture.", keywords: ["remediation", "action", "queue", "fix"] },
      { id: "go-research-release-readiness", label: "Go: Research Release Readiness", path: "/research-release-readiness", icon: "Q", group: "Release", description: "Release readiness evidence.", keywords: ["release", "readiness", "review", "single tenant"] },
      { id: "go-research-handoff", label: "Go: Research Handoff", path: "/research-handoff", icon: "H", group: "Release", description: "Handoff pack status.", keywords: ["handoff", "release", "operator", "single tenant"] },
      { id: "go-research-handoff-signoff", label: "Go: Research Handoff Signoff", path: "/research-handoff-signoff", icon: "S", group: "Release", description: "Handoff verification and reviewer signoff.", keywords: ["handoff", "signoff", "verify", "reviewer"] },
    ],
  },
];

const TERMINAL_NAV_COMMANDS: TerminalCommand[] = TERMINAL_NAV_GROUPS.flatMap((group) =>
  group.items.map((item) => ({
    id: item.id,
    label: item.label,
    group: group.label,
    description: item.description,
    keywords: item.keywords,
    action: { type: "nav", path: item.path },
  })),
);

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

const NAV_BY_PATH = new Map<string, TerminalNavItem>(
  TERMINAL_NAV_GROUPS.flatMap((group) => group.items.map((item) => [item.path, item] as const)),
);

export function findTerminalNavItem(pathname: string): TerminalNavItem | undefined {
  return NAV_BY_PATH.get(pathname);
}

export const G_CHORD_HELP_ROWS: [string, string][] = Object.entries(G_CHORD_ROUTES).map(([key, path]) => {
  const label = NAV_BY_PATH.get(path)?.label.replace(/^Go: /, "") ?? path;
  const detail = path === "/" ? `${label} (/) · not while typing in inputs` : label;
  return [`G then ${key.toUpperCase()}`, detail];
});

export const TERMINAL_COMMANDS: TerminalCommand[] = [
  ...TERMINAL_NAV_COMMANDS,
  {
    id: "refresh-route",
    label: "Refresh current route queries",
    group: "Tools",
    keywords: ["page", "visible", "r"],
    action: { type: "refresh-visible" },
  },
  {
    id: "refresh-all",
    label: "Refresh all read-plane queries (full)",
    group: "Tools",
    keywords: ["reload", "invalidate", "everything"],
    action: { type: "refresh-all" },
  },
  { id: "toggle-raw", label: "Toggle raw JSON drilldown mode", group: "Tools", keywords: ["json"], action: { type: "toggle-raw-json" } },
  { id: "palette", label: "Open command palette", group: "Tools", keywords: ["cmd", "k"], action: { type: "open-palette" } },
  { id: "close", label: "Close palette / inspector / help", group: "Tools", keywords: ["esc"], action: { type: "close-overlays" } },
  { id: "tape", label: "Focus event tape", group: "Tools", keywords: ["log", "events"], action: { type: "focus-tape" } },
  { id: "alerts", label: "Focus status rail", group: "Tools", keywords: ["rail"], action: { type: "focus-alerts" } },
  { id: "copy-digest", label: "Copy last digest (if set)", group: "Tools", keywords: ["clipboard"], action: { type: "copy-last-digest" } },
  { id: "shortcuts", label: "Keyboard shortcuts", group: "Tools", keywords: ["help", "?"], action: { type: "shortcut-help" } },
];

export function filterCommands(query: string, commands: TerminalCommand[] = TERMINAL_COMMANDS): TerminalCommand[] {
  const q = query.trim().toLowerCase();
  if (!q) return commands;
  return commands.filter((c) => {
    if (c.label.toLowerCase().includes(q)) return true;
    if (c.group?.toLowerCase().includes(q)) return true;
    if (c.description?.toLowerCase().includes(q)) return true;
    if (c.keywords?.some((k) => k.includes(q) || q.includes(k))) return true;
    if (c.id.toLowerCase().includes(q)) return true;
    return false;
  });
}
