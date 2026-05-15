import { existsSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { G_CHORD_HELP_ROWS, G_CHORD_ROUTES, TERMINAL_COMMANDS, TERMINAL_NAV_GROUPS, filterCommands } from "./command-registry";

function navPaths(): Set<string> {
  return new Set(
    TERMINAL_COMMANDS.filter((c) => c.action.type === "nav").map((c) =>
      c.action.type === "nav" ? c.action.path : "",
    ),
  );
}

describe("command-registry", () => {
  it("includes expected navigation targets", () => {
    const paths = navPaths();
    expect(paths.has("/")).toBe(true);
    expect(paths.has("/daily-operator-run")).toBe(true);
    expect(paths.has("/readiness")).toBe(true);
    expect(paths.has("/evidence")).toBe(true);
    expect(paths.has("/ledger")).toBe(true);
    expect(paths.has("/paper-execution")).toBe(true);
    expect(paths.has("/providers")).toBe(true);
    expect(paths.has("/runtime")).toBe(true);
    expect(paths.has("/strategy-inbox")).toBe(true);
    expect(paths.has("/workboard")).toBe(true);
    expect(paths.has("/strategy-graveyard")).toBe(true);
    expect(paths.has("/strategy-lab")).toBe(true);
    expect(paths.has("/paper-tracking")).toBe(true);
    expect(paths.has("/strategy-memory")).toBe(true);
    expect(paths.has("/thesis")).toBe(true);
    expect(paths.has("/research-os")).toBe(true);
  });

  it("keeps every top-level app page discoverable from the command palette", () => {
    const appDir = join(process.cwd(), "app");
    const pageRoutes = readdirSync(appDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory())
      .filter((entry) => existsSync(join(appDir, entry.name, "page.tsx")))
      .map((entry) => `/${entry.name}`)
      .sort();

    const missingRoutes = pageRoutes.filter((route) => !navPaths().has(route));
    expect(missingRoutes).toEqual([]);
  });

  it("uses the same route metadata for rail navigation and Go commands", () => {
    const groupedRoutes = TERMINAL_NAV_GROUPS.flatMap((group) => group.items.map((item) => item.path)).sort();
    const groupedCommandRoutes = TERMINAL_COMMANDS.filter((c) => c.action.type === "nav")
      .map((c) => (c.action.type === "nav" ? c.action.path : ""))
      .sort();

    expect(groupedRoutes).toEqual(groupedCommandRoutes);
    expect(new Set(groupedRoutes).size).toBe(groupedRoutes.length);
  });

  it("includes route refresh and full refresh palette commands", () => {
    expect(TERMINAL_COMMANDS.some((c) => c.id === "refresh-route")).toBe(true);
    expect(TERMINAL_COMMANDS.some((c) => c.id === "refresh-all")).toBe(true);
    const route = TERMINAL_COMMANDS.find((c) => c.id === "refresh-route");
    const all = TERMINAL_COMMANDS.find((c) => c.id === "refresh-all");
    expect(route?.action.type).toBe("refresh-visible");
    expect(all?.action.type).toBe("refresh-all");
  });

  it("G_CHORD_ROUTES paths match Go: nav commands", () => {
    const paths = navPaths();
    for (const p of Object.values(G_CHORD_ROUTES)) {
      expect(paths.has(p)).toBe(true);
    }
    expect(G_CHORD_HELP_ROWS.length).toBe(Object.keys(G_CHORD_ROUTES).length);
    expect(G_CHORD_HELP_ROWS.some(([key, label]) => key === "G then O" && label.includes("Overview"))).toBe(true);
  });

  it("filterCommands narrows by label and keyword", () => {
    const all = filterCommands("");
    expect(all.length).toBe(TERMINAL_COMMANDS.length);
    const ev = filterCommands("evidence");
    expect(ev.some((c) => c.id === "go-evidence")).toBe(true);
    const wb = filterCommands("wb");
    expect(wb.some((c) => c.id === "go-workboard")).toBe(true);
    const grouped = filterCommands("release");
    expect(grouped.some((c) => c.id === "go-research-os")).toBe(true);
    const described = filterCommands("duplicate");
    expect(described.some((c) => c.id === "go-strategy-memory")).toBe(true);
    const none = filterCommands("zzznomatch999");
    expect(none.length).toBe(0);
  });
});
