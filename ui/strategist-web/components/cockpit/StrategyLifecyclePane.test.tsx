/** @vitest-environment jsdom */

import { QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createStrategistQueryClient } from "@/lib/query/query-client";
import type { UiMutationSafetyStatus } from "@/lib/api/types";
import { StrategyLifecyclePane } from "./StrategyLifecyclePane";

vi.mock("@/hooks/useUiStrategyIntake", () => ({
  useSubmitUiStrategyIntake: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ accepted: true, intake_id: "mock" }),
    isPending: false,
  }),
}));

beforeEach(() => cleanup());

describe("StrategyLifecyclePane", () => {
  function Harness({ children }: { children: ReactNode }) {
    const [client] = useState(() => createStrategistQueryClient());
    return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
  }

  const openInspector = vi.fn();
  const setLastDigest = vi.fn();

  const safeMutation: UiMutationSafetyStatus = {
    runtime_mode: "DEV",
    authorization_mode: "NON_PRODUCTION_BYPASS",
    token_configured: false,
    mutation_routes_safe: true,
    detail_code: "OK",
  };

  const blockedMutation: UiMutationSafetyStatus = {
    runtime_mode: "PROD",
    authorization_mode: "TOKEN_PROTECTED",
    token_configured: true,
    mutation_routes_safe: false,
    detail_code: "MUTATION_UNSAFE",
  };

  it("renders UNKNOWN/PENDING lifecycle when payloads are empty", () => {
    render(
      <StrategyLifecyclePane
        strategyIntakeLatest={null}
        strategyThesisLatest={null}
        strategyThesisGenerationLatest={null}
        strategyMemoryLatest={null}
        strategyGraveyardLatest={null}
        paperTrackingLatest={null}
        backtestForensicsLatest={null}
        strategyBatchLatest={null}
        workboard={null}
        evidenceChain={null}
        mutationSafety={safeMutation}
        queryFailed={false}
        openInspector={openInspector}
        setLastDigest={setLastDigest}
      />,
      { wrapper: Harness },
    );
    expect(screen.getByTestId("cockpit-strategy-lifecycle")).toBeTruthy();
    expect(screen.getAllByText(/SUBMIT_STRATEGY_IDEA|UNKNOWN/).length).toBeGreaterThan(0);
  });

  it("does not enable intake submit when mutation surface is blocked", () => {
    render(
      <StrategyLifecyclePane
        strategyIntakeLatest={null}
        strategyThesisLatest={null}
        strategyThesisGenerationLatest={null}
        strategyMemoryLatest={null}
        strategyGraveyardLatest={null}
        paperTrackingLatest={null}
        backtestForensicsLatest={null}
        strategyBatchLatest={null}
        workboard={null}
        evidenceChain={null}
        mutationSafety={blockedMutation}
        queryFailed={false}
        openInspector={openInspector}
      />,
      { wrapper: Harness },
    );
    const pane = screen.getAllByTestId("cockpit-strategy-lifecycle")[0];
    const submit = within(pane).getByTestId("lifecycle-intake-submit") as HTMLButtonElement;
    expect(submit.disabled).toBe(true);
  });

  it("invokes digest copy and inspector when row has digest_full", () => {
    const sha = "5555555555555555555555555555555555555555555555555555555555555555";
    render(
      <StrategyLifecyclePane
        strategyIntakeLatest={null}
        strategyThesisLatest={{
          schema_version: "ui_strategy_thesis/v1",
          degraded: [],
          latest: {
            strategy_id: "Z",
            thesis_id: "T",
            support_status: "SUPPORTED",
            evaluated_at_utc: "2026-05-01T11:00:00Z",
            evaluation_sha256: sha,
          },
        }}
        strategyThesisGenerationLatest={null}
        strategyMemoryLatest={null}
        strategyGraveyardLatest={null}
        paperTrackingLatest={null}
        backtestForensicsLatest={null}
        strategyBatchLatest={null}
        workboard={null}
        evidenceChain={null}
        mutationSafety={safeMutation}
        queryFailed={false}
        openInspector={openInspector}
        setLastDigest={setLastDigest}
      />,
      { wrapper: Harness },
    );
    const pane = screen.getAllByTestId("cockpit-strategy-lifecycle")[0];
    const tbody = pane.querySelector("tbody");
    const trs = tbody?.querySelectorAll("tr") ?? [];
    const evalRow = Array.from(trs).find((tr) => tr.cells[0]?.textContent === "Thesis evaluation");
    expect(evalRow).toBeTruthy();
    fireEvent.click(evalRow!);
    expect(setLastDigest).toHaveBeenCalledWith(sha);
    expect(openInspector).toHaveBeenCalled();
  });
});
