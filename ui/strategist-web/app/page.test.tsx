/** @vitest-environment jsdom */

import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, cleanup } from "@testing-library/react";
import { useState, type ReactNode } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EventTape } from "@/components/terminal/EventTape";
import { InspectorDrawer } from "@/components/terminal/InspectorDrawer";
import { createStrategistQueryClient } from "@/lib/query/query-client";
import { TerminalCockpitProvider } from "@/lib/terminal/cockpit-context";
import HomePage from "./page";

vi.mock("@/lib/config/public-config", () => ({
  tryGetPublicStrategistApiBaseUrl: () => ({ ok: true, baseUrl: "http://127.0.0.1:8000" }),
}));

vi.mock("@/hooks/useProbeApiRoot", () => ({ useProbeApiRoot: () => ({ data: { schema_version: "root/v1" }, isError: false, isLoading: false }) }));
vi.mock("@/hooks/useProbeHealthz", () => ({ useProbeHealthz: () => ({ data: { ok: true }, isError: false, isLoading: false }) }));
vi.mock("@/hooks/useProbeReadyz", () => ({
  useProbeReadyz: () => ({
    data: {
      httpStatus: 200,
      data: {
        status: "READY",
        checked_at_utc: "2026-05-01T10:00:00Z",
        config_fingerprint: "abcdef1234567890",
        checks: { api_smoke: true, backup_restore: true, frontend_readiness_explicit: true },
        blockers: [],
        warnings: [{ code: "FRONTEND_NOT_CLAIMED", message: "frontend not claimed", remediation_hint: "Run evidence gate" }],
      },
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiSurfaceHealth", () => ({ useUiSurfaceHealth: () => ({ data: { ok: true }, isError: false, isLoading: false }) }));
vi.mock("@/hooks/useUiFacade", () => ({
  useUiFacade: () => ({
    data: {
      schema_version: "ui_public_facade_inventory/v1",
      surface: "ui",
      frontend_expected_package: "ui/strategist-web",
      frontend_package_present: true,
      frontend_package_detected_by_backend: true,
      frontend_readiness_claimed: false,
      frontend_runtime_reachable: null,
      read_plane_only: true,
      mutation_route: "/ui/commands/{action}",
      routes: [{ method: "GET", path: "/ui/facade", kind: "metadata", auth_required: false, payload_schema: "x" }],
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiEvidence", () => ({
  useUiEvidence: () => ({
    data: {
      schema_version: "ui_evidence_dashboard/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      deployment_status: "PASS",
      deployment_evidence_ok: true,
      api_smoke_status: "OK",
      api_smoke_ok: true,
      backup_restore_ok: true,
      ledger_integrity_ok: true,
      manual_operator_signoff_present: true,
      operator_decision: "APPROVED",
      frontend_readiness_status: "NOT_CLAIMED",
      registry: { projection_digest_sha256: "0123456789abcdef0123456789abcdef" },
      verification: { trust_status: "TRUST_RESTRICTED" },
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiProviderHealth", () => ({
  useUiProviderHealth: () => ({
    data: {
      generated_at_utc: "2026-05-01T10:00:00Z",
      entries: [
        {
          provider_id: "alpaca",
          display_name: "Alpaca Markets",
          access_type: "BROKER_ACCOUNT_REQUIRED",
          classified_status: "NOT_CHECKED",
          pit_suitability: "EXECUTION_ONLY",
          trust_level: "BROKER_EXECUTION",
          http_status: null,
          configured: true,
          reachable: false,
          warnings: ["PAPER_ONLY"],
        },
      ],
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiOperatorActions", () => ({
  useUiOperatorActions: () => ({
    data: { event_count: 1, chain_ok: true, entries: [{ action_event_id: "a1", event_hash: "feedfacecafebeef", action: "APPROVE", operator_id: "ops", target: "deploy", status: "ACCEPTED", accepted_at_utc: "2026-05-01T10:00:00Z" }] },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiWorkboard", () => ({
  useUiWorkboard: () => ({
    data: {
      schema_version: "ui_workboard_dashboard/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      board_label: "operator",
      stats: { active_count: 1, governed_count: 1, journaled_count: 0, escalated_count: 0, blocked_count: 0, linked_count: 0, stale_link_count: 0, pack_item_count: 1, pack_column_count: 1, freshness_state: "FRESH" },
      queue: { entries: [{ work_item_key: "WB-1", status: "READY", source_kind: "PACK", updated_at_utc: "2026-05-01T10:00:00Z" }], work_item_count: 1 },
      pack_workbench: {},
      transition_policy: {},
      intelligence: {
        ranked_items: [
          {
            work_item_key: "STRAT-ALPHA-1",
            review_target: "MOMENTUM_BREAKOUT_TEST",
            attention_state: "INVESTIGATE",
            priority_score: 87,
            command_readiness: { top_action: "claim-item", ready_count: 0, caution_count: 1, blocked_count: 2 },
            operator_brief: { summary_line: "Safest next move is claim item for the strategy test." },
          },
        ],
      },
      materialization: {},
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiRuntime", () => ({
  useUiRuntime: () => ({
    data: { schema_version: "ui_runtime_status/v1", environment: "RuntimeMode.DEV", read_plane: { status: "LIVE" }, backend: { base_mode: "DEV" } },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchCompute", () => ({
  useUiResearchCompute: () => ({
    data: {
      schema_version: "ui_research_compute/v1",
      gpu_available: false,
      research_compute_readiness: "CPU_FALLBACK_READY",
      gpu_probe: {
        gpu_hardware_detected: true,
        gpu_available: false,
        cuda_available: false,
        backend: "torch_cpu",
        nvidia_smi_devices: [{ name: "NVIDIA GeForce RTX 5060 Ti", memory_total_mib: 16311 }],
      },
    },
    isError: false,
    isLoading: false,
  }),
}));

function Harness({ children }: { children: ReactNode }) {
  const [client] = useState(() => createStrategistQueryClient());
  return (
    <QueryClientProvider client={client}>
      <TerminalCockpitProvider>
        {children}
        <InspectorDrawer />
        <EventTape />
      </TerminalCockpitProvider>
    </QueryClientProvider>
  );
}

beforeEach(() => cleanup());

describe("HomePage cockpit", () => {
  it("renders the terminal cockpit shell panes and keeps raw JSON in the inspector drilldown", async () => {
    render(<HomePage />, { wrapper: Harness });

    for (const heading of [
      "Overview",
      "Readiness Matrix",
      "Evidence Chain",
      "Provider Matrix",
      "Ledger / Operator Actions",
      "Workboard",
      "Runtime",
    ]) {
      expect(screen.getByText(heading)).toBeTruthy();
    }
    expect(screen.getByText("STRATEGY TESTS")).toBeTruthy();
    expect(screen.getByText("MOMENTUM_BREAKOUT_TEST")).toBeTruthy();
    expect(screen.getByText("gpu_hardware_detected")).toBeTruthy();
    expect(screen.getByText("NVIDIA GeForce RTX 5060 Ti")).toBeTruthy();

    expect(screen.queryByText(/"schema_version": "ui_evidence_dashboard\/v1"/)).toBeNull();
    fireEvent.click(screen.getByText("Alpaca Markets"));
    expect(screen.getByText(/Provider .* Alpaca Markets/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /show raw json/i }));
    expect(screen.getByText(/"provider_id": "alpaca"/)).toBeTruthy();

    await waitFor(() => expect(screen.getAllByText(/FRONTEND_NOT_CLAIMED/).length).toBeGreaterThan(0));
    expect(screen.getByText(/READY=READY/)).toBeTruthy();
  });

  it("opens evidence rows in the persistent inspector", () => {
    render(<HomePage />, { wrapper: Harness });
    fireEvent.click(screen.getAllByText("API Smoke")[1]);
    expect(screen.getByText("Evidence · API Smoke")).toBeTruthy();
  });
});
