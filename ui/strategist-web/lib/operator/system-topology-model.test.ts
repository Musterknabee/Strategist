import { describe, expect, it } from "vitest";
import type { UiFacadeRoute } from "@/lib/api/types";
import uiFacadeContract from "@/lib/contracts/ui-facade-routes.json";
import {
  buildSystemTopology,
  redactTopologyRaw,
  topologyDegradedHints,
  topologyMutationRoutes,
  topologyReadPlaneContractRoutes,
  type FacadeRoutesContract,
} from "./system-topology-model";

describe("buildSystemTopology", () => {
  it("marks facade contract UNKNOWN when contract is missing", () => {
    const { nodes } = buildSystemTopology({
      contract: null,
      facadePayload: null,
      paneDegraded: {},
    });
    const snap = nodes.find((n) => n.node_id === "snapshot:facade-contract");
    expect(snap?.status).toBe("UNKNOWN");
    expect(nodes.filter((n) => n.node_id.startsWith("route:")).length).toBe(0);
  });

  it("marks deployment readiness path UNKNOWN vs UI facade contract (not fabricated)", () => {
    const contract = uiFacadeContract as FacadeRoutesContract;
    const { nodes } = buildSystemTopology({ contract, facadePayload: null, paneDegraded: {} });
    const ep = nodes.find((n) => n.node_id === "endpoint:first-run:/readiness/deployment");
    expect(ep?.status).toBe("UNKNOWN");
    expect((ep?.raw as { in_ui_facade_contract?: boolean })?.in_ui_facade_contract).toBe(false);
  });

  it("maps frontend pane to endpoint and contract route when provided", () => {
    const contract = uiFacadeContract as FacadeRoutesContract;
    const { nodes } = buildSystemTopology({
      contract,
      facadePayload: null,
      paneDegraded: {},
    });
    const ep = nodes.find((n) => n.node_id === "endpoint:evidence-chain:/ui/evidence-chain");
    expect(ep).toBeDefined();
    expect(ep?.related_nodes).toContain("route:GET:/ui/evidence-chain");
  });

  it("classifies mutation routes as MUTATION_AUTH with auth_required from contract", () => {
    const contract = uiFacadeContract as FacadeRoutesContract;
    const { nodes } = buildSystemTopology({ contract, facadePayload: null, paneDegraded: {} });
    const mut = topologyMutationRoutes(nodes);
    expect(mut.length).toBeGreaterThanOrEqual(2);
    for (const m of mut) {
      expect(m.safety_class).toBe("MUTATION_AUTH");
      const rows = Array.isArray(m.raw?.routes) ? (m.raw?.routes as UiFacadeRoute[]) : [];
      expect(rows.some((r) => r.kind === "mutation")).toBe(true);
    }
    const commands = mut.find((n) => n.label.includes("/ui/commands"));
    expect(commands).toBeDefined();
  });

  it("includes read-plane GET routes from contract", () => {
    const contract = uiFacadeContract as FacadeRoutesContract;
    const { nodes } = buildSystemTopology({ contract, facadePayload: null, paneDegraded: {} });
    const reads = topologyReadPlaneContractRoutes(nodes);
    expect(reads.some((r) => r.label === "/ui/evidence")).toBe(true);
  });

  it("marks pane DEGRADED when paneDegraded says so", () => {
    const contract = uiFacadeContract as FacadeRoutesContract;
    const { nodes } = buildSystemTopology({
      contract,
      facadePayload: null,
      paneDegraded: { overview: true },
    });
    const pane = nodes.find((n) => n.node_id === "pane:overview");
    expect(pane?.status).toBe("DEGRADED");
    expect(topologyDegradedHints("overview")).toMatch(/Inspect/);
  });

  it("maps CLI registry entry to evidence and pane keys", () => {
    const contract = uiFacadeContract as FacadeRoutesContract;
    const { nodes } = buildSystemTopology({ contract, facadePayload: null, paneDegraded: {} });
    const cli = nodes.find((n) => n.node_id === "cli:loc_rc_generate");
    const ev = nodes.find((n) => n.node_id === "evidence:loc_rc_generate");
    expect(cli?.node_type).toBe("CLI_COMMAND");
    expect(ev?.node_type).toBe("EVIDENCE_ARTIFACT");
    expect(cli?.related_nodes).toContain("evidence:loc_rc_generate");
    expect(cli?.related_nodes).toContain("pane:release-control");
  });

  it("renders authority boundary nodes", () => {
    const { nodes } = buildSystemTopology({
      contract: null,
      facadePayload: null,
      paneDegraded: {},
    });
    expect(nodes.some((n) => n.node_id === "boundary:append-only-ledger")).toBe(true);
    expect(nodes.some((n) => n.node_id === "boundary:frontend-read-plane")).toBe(true);
  });

  it("redacts sensitive raw keys in defense in depth", () => {
    expect(redactTopologyRaw({ bearer_token: "x", ok: 1 })).toEqual({ bearer_token: "[REDACTED]", ok: 1 });
  });
});
