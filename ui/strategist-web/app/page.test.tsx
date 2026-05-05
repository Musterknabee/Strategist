/** @vitest-environment jsdom */

import { QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor, cleanup, within } from "@testing-library/react";
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
vi.mock("@/hooks/useProbeLivez", () => ({
  useProbeLivez: () => ({ data: { httpStatus: 200, data: { ok: true } }, isError: false, isLoading: false }),
}));
vi.mock("@/hooks/useReadinessDeployment", () => ({
  useReadinessDeployment: () => ({
    data: {
      schema_version: "deployment_readiness_payload/v2",
      status: "READY",
      checks: {
        environment_overrides_valid: true,
        private_key_material_absent: true,
        ledger_database_path_configured: true,
        ledger_path_resolved: true,
        schema_compatibility: true,
        ledger_backup_dir_configured: true,
        backup_root_writable: true,
      },
      blocker_codes: [],
      warning_codes: [],
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiEvidenceChain", () => ({
  useUiEvidenceChain: () => ({
    data: {
      schema_version: "ui_evidence_chain/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      read_plane_only: true,
      mutation_authority: "x",
      promotion_authority: "y",
      execution_authority: "z",
      readonly: true,
      ok: true,
      degraded: [],
      summary: {
        event_count_total: 0,
        chain_issue_count_total: 0,
        decision_ledger_event_count: 0,
        decision_ledger_stream_count: 0,
        operator_action_event_count: 0,
        decision_ledger_chain_ok: true,
        operator_action_chain_ok: true,
      },
      streams: {},
      timeline: { entry_count: 0, returned_count: 0, limit: 250, entries: [] },
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiProviderSetup", () => ({
  useUiProviderSetup: () => ({
    data: {
      schema_version: "ui_provider_setup_console/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      read_plane_only: true,
      mutation_authority: "read_plane",
      execution_authority: "none",
      no_network_calls: true,
      no_secret_values: true,
      freshness_max_age_seconds: 86400,
      summary: {
        provider_count: 1,
        ready_count: 1,
        blocked_count: 0,
        action_required_count: 0,
        stale_count: 0,
        not_checked_count: 0,
        missing_secret_count: 0,
        public_no_signup_count: 0,
        keyed_provider_count: 0,
        pit_strong_count: 0,
      },
      entries: [],
    },
    isError: false,
    isLoading: false,
  }),
}));
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
      frontend_operator_console_hint: "Package detection is cwd-scoped; readiness claim is opt-in.",
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
    data: {
      schema_version: "ui_runtime_status/v1",
      environment: "RuntimeMode.DEV",
      read_plane: { status: "LIVE" },
      backend: { base_mode: "DEV" },
      mutation_safety: {
        runtime_mode: "DEV",
        authorization_mode: "NON_PRODUCTION_BYPASS",
        token_configured: false,
        mutation_routes_safe: true,
        detail_code: "REMOTE_NON_PRODUCTION_MUTATION_BYPASS_ENABLED",
      },
    },
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
vi.mock("@/hooks/useUiResearchOsStatus", () => ({
  useUiResearchOsStatus: () => ({
    data: {
      schema_version: "ui_research_os_status/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      read_plane_only: true,
      degraded: [],
      warnings: [],
      artifact_root_summary: { artifact_root: "/tmp/artifacts" },
      research_os_closure_latest: {
        status: "PRESENT",
        generated_at_utc: "2026-05-01T10:00:00Z",
        latest: {
          status: "COMPLETE",
          trust_banner: "TRUSTED",
          manifest_sha256: "abcdef0123456789abcdef0123456789",
          blockers: [],
          warnings: [],
        },
        degraded: [],
      },
      research_os_attestation_latest: {
        status: "PRESENT",
        generated_at_utc: "2026-05-01T10:00:00Z",
        latest_verification: { status: "VERIFIED", trust_banner: "TRUSTED", blockers: [], warnings: [] },
        latest_attestation: { decision: "ACKNOWLEDGED", blockers: [], warnings: [] },
        degraded: [],
      },
      research_os_evidence_drift_latest: {
        status: "PRESENT",
        generated_at_utc: "2026-05-01T10:00:00Z",
        latest: { status: "READY", trust_banner: "TRUSTED", artifact_sha256: "fedcba0123456789fedcba0123456789", blockers: [], warnings: [] },
        degraded: [],
      },
      research_os_policy_gate_latest: {
        status: "PRESENT",
        latest: { decision: "PASS", trust_banner: "TRUSTED" },
        degraded: [],
      },
      research_os_release_readiness_latest: { status: "NOT_PRESENT", degraded: ["NO_RELEASE_READINESS_REPORT"] },
      research_os_exception_latest: { status: "NOT_PRESENT", degraded: [] },
      research_os_remediation_latest: { status: "NOT_PRESENT", degraded: [] },
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiPaperBroker", () => ({
  useUiPaperBrokerStatus: () => ({
    data: {
      policy_status: "PAPER_READY",
      blockers: [],
      warnings: [],
      generated_at_utc: "2026-05-01T10:00:00Z",
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiPaperExecution", () => ({
  useUiPaperExecutionCockpit: () => ({
    data: {
      schema_version: "ui_paper_execution_cockpit/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      read_plane_only: true,
      no_live_trading: true,
      no_browser_orders: true,
      execution_authority: "LIVE_BLOCKED",
      promotion_authority: "PAPER_ONLY_GATE",
      summary: {
        broker_policy_status: "PAPER_READY",
        paper_submission_capability: "CLI_ONLY",
        submission_guard_blocker_count: 0,
        evidence_bundle_blocker_count: 0,
        timeline_blocker_count: 0,
        evidence_freshness_blocker_count: 0,
        timeline_warning_count: 0,
        position_reconciliation_warning_count: 0,
        latest_evidence_bundle_sha256: "0123456789abcdef0123456789abcdef",
        latest_evidence_bundle_trust_banner: "TRUST_RESTRICTED",
        latest_evidence_bundle_status: "SEALED",
        selected_intent_dry_run_status: "OK",
      },
      dry_run_results: [
        { status: "OK", trust_banner: "TRUSTED", artifact_sha256: "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", generated_at_utc: "2026-05-01T09:00:00Z" },
      ],
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiStrategyBatches", () => ({
  useUiStrategyBatchesLatest: () => ({
    data: {
      generated_at_utc: "2026-05-01T10:00:00Z",
      latest: { run_id: "run-42", ok: true, blocked_count: 0, failed_count: 0, top_candidate: "STRAT-ALPHA-1" },
      degraded: [],
    },
    isError: false,
    isLoading: false,
  }),
  useUiStrategyBatches: () => ({
    data: { generated_at_utc: "2026-05-01T10:00:00Z", batches: [], degraded: [] },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiBacktestForensics", () => ({
  useUiBacktestForensicsLatest: () => ({
    data: {
      generated_at_utc: "2026-05-01T10:00:00Z",
      summary_path: "/tmp/forensics.json",
      degraded: [],
      summary: { blocked_count: 0, needs_evidence_count: 0, failed_count: 0, batch_present: true },
      batch: { run_id: "run-42" },
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiPaperTracking", () => ({
  useUiPaperTrackingLatest: () => ({
    data: { generated_at_utc: "2026-05-01T10:00:00Z", degraded: [], latest: { tracking_id: "trk-1", lifecycle_state: "ACTIVE" } },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiStrategyGraveyard", () => ({
  useUiStrategyGraveyardLatest: () => ({
    data: { generated_at_utc: "2026-05-01T10:00:00Z", degraded: [], summary: { hard_blocked_count: 1, operator_review_count: 0 } },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiStrategyMemory", () => ({
  useUiStrategyMemoryLatest: () => ({
    data: {
      generated_at_utc: "2026-05-01T10:00:00Z",
      degraded: [],
      index_path: "/tmp/memory_index.json",
      latest: { index_sha256: "0123456789abcdef0123456789abcdef", duplicate_variant_count: 0, killed_count: 1 },
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiStrategyIntake", () => ({
  useUiStrategyIntakeLatest: () => ({
    data: {
      schema_version: "ui_strategy_intake/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      read_plane_only: true,
      latest: { intake_count: 0, entries: [] },
      degraded: [],
    },
    isError: false,
    isLoading: false,
  }),
  useSubmitUiStrategyIntake: () => ({
    mutateAsync: vi.fn().mockResolvedValue({ accepted: true, intake_id: "mock" }),
    isPending: false,
  }),
}));
vi.mock("@/hooks/useUiStrategyThesis", () => ({
  useUiStrategyThesisLatest: () => ({
    data: { schema_version: "ui_strategy_thesis/v1", degraded: ["NO_THESIS_EVALUATION"], latest: null },
    isError: false,
    isLoading: false,
  }),
  useUiStrategyThesisGenerationLatest: () => ({
    data: { schema_version: "ui_strategy_thesis_generation/v1", degraded: ["NO_THESIS_GENERATION_REPORT"], latest_generation: null },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsReleaseReadiness", () => ({
  useUiResearchOsReleaseReadinessLatest: () => ({
    data: {
      schema_version: "ui_research_os_release_readiness/v1",
      status: "MISSING",
      degraded: ["NO_RESEARCH_OS_RELEASE_READINESS_REPORT"],
      latest: null,
      generated_at_utc: "2026-05-01T10:00:00Z",
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsHandoff", () => ({
  useUiResearchOsHandoffLatest: () => ({
    data: { schema_version: "ui_research_os_handoff/v1", status: "MISSING", degraded: ["NO_RESEARCH_OS_HANDOFF_PACK"], latest: null },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsHandoffSignoff", () => ({
  useUiResearchOsHandoffSignoffLatest: () => ({
    data: {
      schema_version: "ui_research_os_handoff_signoff/v1",
      status: "MISSING",
      degraded: ["NO_RESEARCH_OS_HANDOFF_VERIFICATION_RESULT"],
      latest_verification: null,
      latest_signoff: null,
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsReviewJournal", () => ({
  useUiResearchOsReviewJournalLatest: () => ({
    data: {
      schema_version: "ui_research_os_review_journal/v1",
      status: "NOT_PRESENT",
      degraded: ["NO_RESEARCH_OS_REVIEW_JOURNAL"],
      latest: null,
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsExport", () => ({
  useUiResearchOsExportLatest: () => ({
    data: {
      schema_version: "ui_research_os_export/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      degraded: ["NO_RESEARCH_OS_EXPORT_MANIFEST"],
      latest_export: null,
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsDrift", () => ({
  useUiResearchOsDriftLatest: () => ({
    data: {
      schema_version: "ui_research_os_evidence_drift/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      degraded: ["NO_RESEARCH_OS_EVIDENCE_DRIFT_REPORT"],
      latest: null,
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsException", () => ({
  useUiResearchOsExceptionLatest: () => ({
    data: {
      schema_version: "ui_research_os_exception/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      degraded: [],
      latest: null,
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsRemediation", () => ({
  useUiResearchOsRemediationLatest: () => ({
    data: {
      schema_version: "ui_research_os_remediation/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      degraded: [],
      latest: null,
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiResearchOsPolicyGate", () => ({
  useUiResearchOsPolicyGateLatest: () => ({
    data: {
      schema_version: "ui_research_os_policy_gate/v1",
      generated_at_utc: "2026-05-01T10:00:00Z",
      degraded: [],
      latest: {
        gate_id: "gate-1",
        decision: "PASS",
        trust_banner: "TRUSTED",
        blockers: [],
        warnings: [],
        rules: [],
        blocker_count: 0,
        warning_count: 0,
      },
    },
    isError: false,
    isLoading: false,
  }),
}));
vi.mock("@/hooks/useUiShadowBook", () => ({
  useUiShadowBookLatest: () => ({ data: { schema_version: "ui_shadow_book/v1" }, isError: false, isLoading: false }),
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

    expect(screen.getByTestId("cockpit-mode-switchboard")).toBeTruthy();
    expect(screen.getByTestId("cockpit-mode-current-label").textContent).toMatch(/Daily Ops/i);
    expect(screen.getByTestId("cockpit-mode-command-banner")).toBeTruthy();

    fireEvent.click(screen.getByTestId("cockpit-mode-select-FIRST_RUN"));
    expect(screen.getByTestId("cockpit-mode-readonly-banner")).toBeTruthy();
    expect(screen.queryByTestId("cockpit-mode-command-banner")).toBeNull();

    fireEvent.click(screen.getByTestId("cockpit-mode-select-DAILY_OPS"));
    expect(screen.getByTestId("cockpit-mode-command-banner")).toBeTruthy();

    const sevenPaneGrid = screen.getByTestId("cockpit-seven-pane-grid");
    expect(sevenPaneGrid).toBeTruthy();
    expect(screen.getAllByText("PENDING").length).toBeGreaterThan(0);
    expect(screen.getAllByText("NOT_CHECKED").length).toBeGreaterThan(0);

    for (const heading of [
      "Overview",
      "Readiness Matrix",
      "Evidence Chain",
      "Provider Matrix",
      "Ledger / Operator Actions",
      "Workboard",
      "Runtime",
    ]) {
      expect(within(sevenPaneGrid).getByText(heading)).toBeTruthy();
    }
    expect(within(screen.getByTestId("cockpit-research-os-drilldown")).getByText("Research OS Evidence")).toBeTruthy();
    expect(within(screen.getByTestId("cockpit-paper-execution-drilldown")).getByText("Paper Execution Evidence")).toBeTruthy();
    expect(within(screen.getByTestId("cockpit-execution-firewall")).getByText("Capital / execution firewall")).toBeTruthy();
    expect(within(screen.getByTestId("cockpit-operator-health-alerts")).getByText("Operator health / alerts")).toBeTruthy();
    expect(within(screen.getByTestId("cockpit-remediation-governance")).getByText("Incident / remediation / exceptions")).toBeTruthy();
    expect(within(screen.getByTestId("cockpit-policy-risk-gates")).getByText("Policy / risk gates")).toBeTruthy();
    expect(within(screen.getByTestId("cockpit-promotion-dossier")).getByText("Promotion evidence dossier")).toBeTruthy();
    expect(screen.getByText("System topology / dependency map")).toBeTruthy();
    expect(screen.getByTestId("cockpit-research-os-drilldown")).toBeTruthy();
    expect(screen.getByTestId("cockpit-paper-execution-drilldown")).toBeTruthy();
    expect(screen.getByTestId("cockpit-execution-firewall")).toBeTruthy();
    expect(screen.getByTestId("cockpit-operator-health-alerts")).toBeTruthy();
    expect(screen.getByTestId("cockpit-remediation-governance")).toBeTruthy();
    expect(screen.getByTestId("cockpit-operator-command")).toBeTruthy();
    expect(screen.getByTestId("cockpit-first-run-deployment")).toBeTruthy();
    expect(screen.getByTestId("cockpit-provider-setup-readiness")).toBeTruthy();
    expect(screen.getByTestId("cockpit-strategy-lifecycle")).toBeTruthy();
    expect(screen.getByTestId("cockpit-release-control")).toBeTruthy();
    expect(screen.getByTestId("cockpit-evidence-runbook")).toBeTruthy();
    expect(screen.getByTestId("cockpit-audit-forensic")).toBeTruthy();
    expect(screen.getByTestId("cockpit-policy-risk-gates")).toBeTruthy();
    expect(screen.getByTestId("cockpit-promotion-dossier")).toBeTruthy();
    expect(screen.getByTestId("cockpit-research-batch-forensics")).toBeTruthy();
    expect(screen.getAllByText(/PAPER_ONLY/).length).toBeGreaterThan(0);
    expect(screen.getByText("Evidence drift")).toBeTruthy();
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
