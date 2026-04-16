import type { UiOperatorCommandReceipt, UiRuntimeStatus } from "@/lib/contracts/ui";

export function makeRuntimeStatus(overrides: Partial<UiRuntimeStatus> = {}): UiRuntimeStatus {
  return {
    schema_version: "ui.runtime.v1",
    generated_at_utc: new Date("2026-04-16T10:00:00Z").toISOString(),
    environment: "staging",
    read_plane: {
      status: "ready",
      freshness_status: "fresh",
      operator_message: "All projections fresh.",
    },
    backend: { status: "reachable", base_mode: "proxy", operator_message: "Backend reachable." },
    blindness: { tribunal_mode: "enforced", operator_message: "Blindness law enforced." },
    providers: { enabled_count: 3, items: [] },
    persona: {
      active_role: "operator",
      active_label: "Operator",
      available_roles: ["operator", "validator", "tribunal"],
      default_route: "/workboard",
    },
    policy: {
      allowed_domains: ["control-plane", "validator", "tribunal", "evidence"],
      redacted_domains: [],
      allowed_actions: ["claim-item", "acknowledge-reentry", "renew-lease"],
    },
    command_bar: { allowed_actions: ["claim-item"], operator_hint: "Use governed actions only." },
    ...overrides,
  } as UiRuntimeStatus;
}

export function makeCommandReceipt(overrides: Partial<UiOperatorCommandReceipt> = {}): UiOperatorCommandReceipt {
  return {
    schema_version: "ui.command-receipt.v1",
    generated_at_utc: new Date("2026-04-16T10:00:00Z").toISOString(),
    command_id: "cmd-1",
    action: "claim-item",
    accepted: true,
    operator_id: "jp-k",
    execution_mode: "SIMULATED_RECEIPT_ONLY",
    requires_projection_refresh: true,
    target: { pack_kind: "alpha-pack", work_item_key: "wk-1", review_target: "SPY", manifest_path: "/tmp/pack.json" },
    summary_line: "Claim item receipt recorded.",
    operator_message: "Receipt accepted; wait for projection refresh.",
    ...overrides,
  };
}
