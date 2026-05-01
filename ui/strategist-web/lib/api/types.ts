/** Subset of `GET /ui/facade` used by the operator console. */
export type UiFacadeRoute = {
  method: string;
  path: string;
  kind: string;
  auth_required: boolean;
  payload_schema: string;
};

export type UiFacadePayload = {
  schema_version: string;
  surface: string;
  frontend_expected_package: string;
  frontend_package_present: boolean;
  /** Same as `frontend_package_present`: true only if the API process sees `ui/strategist-web` under its cwd. */
  frontend_package_detected_by_backend?: boolean;
  frontend_status?: string;
  frontend_readiness_claimed: boolean;
  /** The API does not assess browser reachability; always null from backend. */
  frontend_runtime_reachable?: boolean | null;
  frontend_operator_console_hint?: string;
  read_plane_only: boolean;
  mutation_route: string;
  routes: UiFacadeRoute[];
};

export type UiWorkboardStats = {
  active_count: number;
  governed_count: number;
  journaled_count: number;
  escalated_count: number;
  blocked_count: number;
  linked_count: number;
  stale_link_count: number;
  pack_item_count: number;
  pack_column_count: number;
  freshness_state: string;
};

export type UiWorkboardQueueEntry = Record<string, unknown>;

export type UiWorkboardPayload = {
  schema_version: string;
  generated_at_utc: string;
  board_label: string;
  queue: {
    entries?: UiWorkboardQueueEntry[];
    work_item_count?: number;
    queue_summary_line?: string;
    queue_key?: string;
    [key: string]: unknown;
  };
  pack_workbench: Record<string, unknown>;
  transition_policy: Record<string, unknown>;
  intelligence: Record<string, unknown>;
  materialization: Record<string, unknown>;
  stats: UiWorkboardStats;
};

export function deriveWorkboardDegradedReason(payload: UiWorkboardPayload): string | null {
  const fresh = (payload.stats?.freshness_state || "UNKNOWN").toUpperCase();
  if (fresh === "STALE" || fresh === "DEGRADED") {
    return `Workboard projection freshness is ${payload.stats.freshness_state}.`;
  }
  const matState = String(payload.materialization?.materialization_state || "").toUpperCase();
  if (matState && matState !== "READY" && matState !== "UNKNOWN" && matState !== "") {
    return `Materialization state: ${payload.materialization.materialization_state}.`;
  }
  return null;
}
