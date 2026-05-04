import { describe, expect, it } from "vitest";
import { G_CHORD_ROUTES, TERMINAL_COMMANDS, filterCommands } from "./command-registry";

describe("command-registry", () => {
  it("includes expected navigation targets", () => {
    const paths = new Set(
      TERMINAL_COMMANDS.filter((c) => c.action.type === "nav").map((c) =>
        c.action.type === "nav" ? c.action.path : "",
      ),
    );
    expect(paths.has("/")).toBe(true);
    expect(paths.has("/readiness")).toBe(true);
    expect(paths.has("/evidence")).toBe(true);
    expect(paths.has("/ledger")).toBe(true);
    expect(paths.has("/providers")).toBe(true);
    expect(paths.has("/runtime")).toBe(true);
    expect(paths.has("/workboard")).toBe(true);
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
    const navPaths = new Set(
      TERMINAL_COMMANDS.filter((c) => c.action.type === "nav").map((c) =>
        c.action.type === "nav" ? c.action.path : "",
      ),
    );
    for (const p of Object.values(G_CHORD_ROUTES)) {
      expect(navPaths.has(p)).toBe(true);
    }
  });

  it("filterCommands narrows by label and keyword", () => {
    const all = filterCommands("");
    expect(all.length).toBe(TERMINAL_COMMANDS.length);
    const ev = filterCommands("evidence");
    expect(ev.some((c) => c.id === "go-evidence")).toBe(true);
    const wb = filterCommands("wb");
    expect(wb.some((c) => c.id === "go-workboard")).toBe(true);
    const none = filterCommands("zzznomatch999");
    expect(none.length).toBe(0);
  });
});
