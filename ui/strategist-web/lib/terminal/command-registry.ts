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
};

export const TERMINAL_COMMANDS: TerminalCommand[] = [
  { id: "go-overview", label: "Go: Overview", keywords: ["home", "index"], action: { type: "nav", path: "/" } },
  { id: "go-workboard", label: "Go: Workboard", keywords: ["queue", "wb"], action: { type: "nav", path: "/workboard" } },
  { id: "go-readiness", label: "Go: Readiness", keywords: ["ready", "health"], action: { type: "nav", path: "/readiness" } },
  { id: "go-evidence", label: "Go: Evidence", keywords: ["deploy", "proof"], action: { type: "nav", path: "/evidence" } },
  { id: "go-ledger", label: "Go: Ledger", keywords: ["journal", "actions"], action: { type: "nav", path: "/ledger" } },
  { id: "go-providers", label: "Go: Providers", keywords: ["market", "data"], action: { type: "nav", path: "/providers" } },
  { id: "go-runtime", label: "Go: Runtime", keywords: ["sys", "env"], action: { type: "nav", path: "/runtime" } },
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
