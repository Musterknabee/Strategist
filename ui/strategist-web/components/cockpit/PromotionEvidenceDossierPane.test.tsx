/** @vitest-environment jsdom */

import { render, screen } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { QueryClientProvider } from "@tanstack/react-query";
import { createStrategistQueryClient } from "@/lib/query/query-client";
import { TerminalCockpitProvider } from "@/lib/terminal/cockpit-context";
import { PromotionEvidenceDossierPane } from "./PromotionEvidenceDossierPane";

function Harness({ children }: { children: ReactNode }) {
  const [client] = useState(() => createStrategistQueryClient());
  return (
    <QueryClientProvider client={client}>
      <TerminalCockpitProvider>{children}</TerminalCockpitProvider>
    </QueryClientProvider>
  );
}

describe("PromotionEvidenceDossierPane", () => {
  it("renders UNKNOWN decision state with empty payloads", () => {
    render(
      <Harness>
        <PromotionEvidenceDossierPane
          readyzBody={null}
          strategyIntakeLatest={null}
          strategyThesisLatest={null}
          strategyThesisGenerationLatest={null}
          paperTrackingLatest={null}
          strategyBatchLatest={null}
          backtestForensicsLatest={null}
          evidenceChain={null}
          operatorActions={null}
          workboard={null}
          evidence={null}
          paperExecution={null}
          queryFailed={false}
          openInspector={vi.fn()}
        />
      </Harness>,
    );
    expect(screen.getByTestId("cockpit-promotion-dossier")).toBeTruthy();
    const states = screen.getAllByText("UNKNOWN");
    expect(states.length).toBeGreaterThan(0);
  });
});
