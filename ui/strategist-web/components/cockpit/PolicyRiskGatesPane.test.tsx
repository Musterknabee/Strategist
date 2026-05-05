/** @vitest-environment jsdom */

import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { createStrategistQueryClient } from "@/lib/query/query-client";
import { TerminalCockpitProvider } from "@/lib/terminal/cockpit-context";
import { PolicyRiskGatesPane } from "./PolicyRiskGatesPane";

function Harness({ children }: { children: ReactNode }) {
  const [client] = useState(() => createStrategistQueryClient());
  return (
    <QueryClientProvider client={client}>
      <TerminalCockpitProvider>{children}</TerminalCockpitProvider>
    </QueryClientProvider>
  );
}

describe("PolicyRiskGatesPane", () => {
  it("shows UNKNOWN counts with empty payloads and filters categories", () => {
    const openInspector = vi.fn();
    render(
      <Harness>
        <PolicyRiskGatesPane
          readyzBody={null}
          readyzError={false}
          runtimeBody={null}
          mutationSafety={null}
          facade={null}
          evidence={null}
          operatorActions={null}
          providerHealth={null}
          backtestForensics={null}
          paperExecution={null}
          paperTracking={null}
          queryFailed={false}
          openInspector={openInspector}
        />
      </Harness>,
    );
    expect(screen.getByTestId("cockpit-policy-risk-gates")).toBeTruthy();
    expect(screen.getByTestId("cockpit-risk-count-unknown").textContent).toMatch(/UNKNOWN/);
    fireEvent.click(screen.getByTestId("cockpit-risk-filter-benchmark-evidence"));
    expect(screen.getByText("UNKNOWN · no gate rows for this filter")).toBeTruthy();
  });
});
