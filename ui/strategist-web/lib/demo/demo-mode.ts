import contract from "@/lib/contracts/ui-facade-routes.json";

const DEMO_TS = "2026-05-05T00:00:00Z";
const DEMO_WARNING = "DEMO_DATA_NOT_REAL";

type DemoRoute = {
  method: string;
  path: string;
  kind: string;
  auth_required: boolean;
  payload_schema: string;
};

type DemoContract = {
  routes: DemoRoute[];
};

export type DemoPayload = Record<string, unknown>;

function mark(payload: DemoPayload): DemoPayload {
  return {
    demo_only: true,
    generated_at_utc: DEMO_TS,
    warnings: [DEMO_WARNING, "NO_REAL_BACKEND_EVIDENCE", "NO_DEPLOYMENT_APPROVAL", "NO_LIVE_EXECUTION"],
    ...payload,
  };
}

const readRoutes = (contract as DemoContract).routes.filter((route) => route.method === "GET" && route.kind === "read");

const facade = mark({
  schema_version: "ui_public_facade/v1",
  surface: "strategist-web-demo",
  frontend_expected_package: "ui/strategist-web",
  frontend_package_present: true,
  frontend_package_detected_by_backend: false,
  frontend_status: "DEMO_ONLY_BACKEND_ABSENT",
  frontend_readiness_claimed: false,
  frontend_runtime_reachable: null,
  frontend_operator_console_hint: "DEMO_ONLY synthetic contract preview; no backend readiness or deployment approval.",
  read_plane_only: true,
  mutation_route: "/ui/commands/{action}",
  routes: readRoutes,
});

const routePayloads: Record<string, DemoPayload> = {
  "/": mark({ schema_version: "api_root/v1", ok: true, status: "DEMO_ONLY", service: "strategy-validator-demo" }),
  "/healthz": mark({ ok: true, status: "DEMO_ONLY", checks: { backend: "ABSENT_SYNTHETIC" } }),
  "/livez": mark({ ok: true, status: "DEMO_ONLY", checks: { process: "SYNTHETIC" } }),
  "/readyz": mark({
    ok: false,
    status: "DEMO_ONLY_NOT_READY",
    blockers: ["DEMO_DATA_NOT_REAL", "BACKEND_ABSENT"],
    checks: { deployment_approved: false, real_backend_evidence: false },
  }),
  "/ui/facade": facade,
  "/ui/runtime": mark({
    schema_version: "ui_runtime/v1",
    read_plane_only: true,
    mutation_safety: {
      runtime_mode: "DEMO_ONLY",
      authorization_mode: "DISABLED_IN_DEMO",
      token_configured: false,
      mutation_routes_safe: false,
      detail_code: "DEMO_MODE_NO_MUTATIONS",
    },
  }),
  "/ui/evidence": mark({
    schema_version: "ui_evidence/v1",
    read_plane_only: true,
    deployment_status: "DEMO_ONLY_NOT_APPROVED",
    operator_decision: "NO_REAL_OPERATOR_DECISION",
    manual_operator_signoff_present: false,
    evidence_summary: { real_evidence_count: 0, synthetic_demo_count: 4 },
  }),
  "/ui/evidence-chain": mark({
    schema_version: "ui_evidence_chain/v1",
    read_plane_only: true,
    mutation_authority: "none_demo",
    promotion_authority: "none_demo",
    execution_authority: "none_demo",
    readonly: true,
    ok: false,
    degraded: ["DEMO_CHAIN_NOT_REAL"],
    summary: {
      event_count_total: 0,
      chain_issue_count_total: 0,
      decision_ledger_event_count: 0,
      decision_ledger_stream_count: 0,
      operator_action_event_count: 0,
      decision_ledger_chain_ok: false,
      operator_action_chain_ok: false,
    },
    streams: {},
    timeline: { entry_count: 1, returned_count: 1, limit: 250, entries: [{ stream_family: "demo", record_id: "DEMO_ONLY_RECORD_001", event_type: "SYNTHETIC_PREVIEW" }] },
  }),
  "/ui/operator-actions": mark({
    schema_version: "ui_operator_action_projection/v1",
    read_plane_only: true,
    entries: [{ action_event_id: "DEMO_ONLY_ACTION_001", status: "SIMULATED_READ_ONLY", actor_id: "DEMO_OPERATOR" }],
    summary: { action_count: 1, mutation_authority: "disabled" },
  }),
  "/ui/workboard": mark({
    schema_version: "ui_workboard/v1",
    board_label: "DEMO_ONLY_WORKBOARD",
    queue: { entries: [{ work_item_key: "DEMO-WB-001", status: "DEMO_ONLY_BLOCKED", source_kind: "SYNTHETIC" }], work_item_count: 1, queue_summary_line: "Synthetic preview item; not deployable." },
    pack_workbench: {},
    transition_policy: {},
    intelligence: {},
    materialization: {},
    stats: { active_count: 1, governed_count: 0, journaled_count: 0, escalated_count: 0, blocked_count: 1, linked_count: 0, stale_link_count: 0, pack_item_count: 0, pack_column_count: 0, freshness_state: "DEMO_ONLY" },
  }),
  "/ui/provider-health": mark({ schema_version: "ui_provider_health/v1", read_plane_only: true, providers: [], summary: { ready_count: 0, blocked_count: 1, demo_only: true } }),
  "/ui/provider-setup": mark({
    schema_version: "ui_provider_setup_console/v1",
    read_plane_only: true,
    mutation_authority: "none_demo",
    execution_authority: "none_demo",
    no_network_calls: true,
    no_secret_values: true,
    freshness_max_age_seconds: 0,
    summary: { provider_count: 1, ready_count: 0, blocked_count: 1, action_required_count: 1, stale_count: 0, not_checked_count: 1, missing_secret_count: 0, public_no_signup_count: 1, keyed_provider_count: 0, pit_strong_count: 0 },
    entries: [{ provider_id: "DEMO_PUBLIC_DATA", display_name: "Synthetic public sample", category: "demo", research_role: "preview", access_type: "public_demo", trust_level: "synthetic", pit_suitability: "not_real", recommended_priority: 99, requires_secret: false, configured: false, reachable: false, classified_status: "DEMO_ONLY", setup_status: "NOT_REAL", readiness_tier: "NOT_READY", freshness_class: "SYNTHETIC", freshness_max_age_seconds: 0, warnings: [DEMO_WARNING], blockers: ["BACKEND_REQUIRED_FOR_REAL_PROVIDER_HEALTH"] }],
  }),
  "/ui/paper-execution": mark({ schema_version: "ui_paper_execution/v1", read_plane_only: true, no_live_trading: true, execution_authority: "none_demo", broker_policy_status: "DEMO_ONLY_DISABLED", summary: { intent_count: 0, live_order_capable: false } }),
  "/ui/research-os/status": mark({ schema_version: "ui_research_os_status/v1", read_plane_only: true, status: "DEMO_ONLY", latest: null }),
  "/ui/research-os/release-readiness/latest": mark({ schema_version: "ui_research_os_release_readiness/v1", read_plane_only: true, latest: { status: "DEMO_ONLY_NOT_READY", decision: "NO_DEPLOYMENT_APPROVAL", blockers: ["DEMO_DATA_NOT_REAL"] } }),
  "/ui/research-os/handoff/latest": mark({ schema_version: "ui_research_os_handoff/v1", read_plane_only: true, latest_handoff: null, handoff_ready: false, degraded: ["DEMO_ONLY_NO_HANDOFF_ARTIFACT"] }),
  "/ui/research-os/handoff-signoff/latest": mark({ schema_version: "ui_research_os_handoff_signoff/v1", read_plane_only: true, latest_verification: null, latest_signoff: null, deployment_approved: false, degraded: ["DEMO_ONLY_NO_SIGNOFF"] }),
  "/ui/strategy-batches/latest": mark({ schema_version: "ui_strategy_batches/v1", read_plane_only: true, latest: { batch_id: "DEMO_ONLY_BATCH_001", status: "SYNTHETIC_PREVIEW", promoted: false }, summary: { batch_count: 1 } }),
  "/ui/backtest-forensics/latest": mark({ schema_version: "ui_backtest_forensics/v1", read_plane_only: true, no_live_trading: true, scan_root: "DEMO_ONLY_SYNTHETIC", degraded: ["DEMO_ONLY_NO_BACKTEST_FILES"], summary: { run_count: 1 } }),
  "/ui/strategy-intake/latest": mark({ schema_version: "ui_strategy_intake/v1", read_plane_only: true, latest: { intake_id: "DEMO_ONLY_INTAKE_001", status: "DRAFT_SYNTHETIC" }, mutation_authority: "disabled" }),
  "/ui/strategy-thesis/latest": mark({ schema_version: "ui_strategy_thesis/v1", read_plane_only: true, latest: { thesis_id: "DEMO_ONLY_THESIS_001", status: "SYNTHETIC_NOT_VALIDATED", digest: "DEMO_DIGEST_NOT_SHA256" } }),
  "/ui/strategy-memory/latest": mark({ schema_version: "ui_strategy_memory/v1", read_plane_only: true, latest: { memory_id: "DEMO_ONLY_MEMORY_001", status: "SYNTHETIC" }, append_only_real_entries: 0 }),
  "/ui/strategy-graveyard/latest": mark({ schema_version: "ui_strategy_graveyard/v1", read_plane_only: true, latest: { record_id: "DEMO_ONLY_GRAVEYARD_001", status: "SYNTHETIC" } }),
};

export const demoReadPlanePaths = Object.freeze(Object.keys(routePayloads));

export function getDemoReadPlanePayload(path: string): DemoPayload | null {
  return routePayloads[path] ?? null;
}

export function getDemoCoverageReport(): DemoPayload {
  return mark({
    schema_version: "strategist_demo_coverage/v1",
    mode: "DEMO_ONLY",
    route_count: demoReadPlanePaths.length,
    represented_paths: demoReadPlanePaths,
    contract_route_count: readRoutes.length,
    uncovered_contract_paths: readRoutes.map((route) => route.path).filter((path) => !routePayloads[path]),
    safety: {
      opt_in_env: "NEXT_PUBLIC_STRATEGIST_DEMO_MODE=true",
      mutations_disabled: true,
      real_readiness_claimed: false,
      deployment_approval_claimed: false,
      live_execution_authority: false,
    },
  });
}
