// @vitest-environment jsdom

import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import uiFacadeContract from "@/lib/contracts/ui-facade-routes.json";
import { buildSystemTopology, type FacadeRoutesContract } from "@/lib/operator/system-topology-model";
import { SystemTopologyPane } from "./SystemTopologyPane";

describe("SystemTopologyPane", () => {
  it("renders topology sections (read-only; no network in this component)", () => {
    const { nodes } = buildSystemTopology({
      contract: uiFacadeContract as FacadeRoutesContract,
      facadePayload: { read_plane_only: true, mutation_route: "/ui/commands/{action}" },
      paneDegraded: {},
    });
    render(
      <SystemTopologyPane
        topologyNodes={nodes}
        facadeReadPlaneOnly
        mutationRouteLabel="/ui/commands/{action}"
        openInspector={vi.fn()}
      />,
    );
    expect(screen.getByTestId("cockpit-system-topology-pane")).toBeTruthy();
    expect(screen.getByText("System topology / dependency map")).toBeTruthy();
    expect(screen.getByText("Authority boundaries")).toBeTruthy();
  });
});
