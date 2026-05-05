import { asBool, asNumber, asRecord, asString } from "@/lib/operator/payload-utils";
import type { UiProviderSetupConsolePayload, UiProviderSetupEntry } from "@/lib/api/types";

export type ProviderReadinessRow = UiProviderSetupEntry & {
  __id: string;
  env_hint_lines: string[];
  freshness_line: string;
  safety_line: string;
};

export type ProviderReadinessSummary = {
  provider_count: number;
  ready_count: number;
  blocked_count: number;
  action_required_count: number;
  stale_count: number;
  not_checked_count: number;
  missing_secret_count: number;
};

export type ProviderReadinessModel = {
  generated_at_utc: string | null;
  samples_manifest_digest_prefix: string | null;
  samples_manifest_path: string | null;
  execution_workflow_blockers: string[];
  trust_status: string;
  summary: ProviderReadinessSummary;
  rows: ProviderReadinessRow[];
  recommended_next_provider_id: string | null;
};

function envHintLines(expectedEnvVars: string[] | undefined): string[] {
  if (!expectedEnvVars || expectedEnvVars.length === 0) return [];
  return expectedEnvVars.map((name) => `${name}=<set-in-gitignored-env-file>`);
}

function freshnessLine(entry: UiProviderSetupEntry): string {
  const cls = asString(entry.freshness_class) ?? "UNKNOWN";
  const age = asNumber(entry.freshness_age_seconds);
  const max = asNumber(entry.freshness_max_age_seconds);
  return `freshness=${cls} age=${age ?? "?"}s max=${max ?? "?"}s`;
}

function safetyLine(entry: UiProviderSetupEntry): string {
  const mayGate = entry.may_gate_live_promotion === true ? "GATES_LIVE_PROMOTION" : "NO_LIVE_GATE";
  const unsafe =
    entry.unsafe_as_promotion_authority_without_license === true
      ? "UNSAFE_PROMOTION_AUTHORITY_WITHOUT_LICENSE"
      : "PROMOTION_AUTHORITY_NOT_FLAGGED_UNSAFE";
  return `${mayGate} · ${unsafe}`;
}

function summaryFromPayload(payload: UiProviderSetupConsolePayload | null | undefined): ProviderReadinessSummary {
  const s = payload?.summary;
  return {
    provider_count: Number(s?.provider_count ?? 0),
    ready_count: Number(s?.ready_count ?? 0),
    blocked_count: Number(s?.blocked_count ?? 0),
    action_required_count: Number(s?.action_required_count ?? 0),
    stale_count: Number(s?.stale_count ?? 0),
    not_checked_count: Number(s?.not_checked_count ?? 0),
    missing_secret_count: Number(s?.missing_secret_count ?? 0),
  };
}

function recommendedNext(rows: ProviderReadinessRow[]): string | null {
  const sorted = [...rows].sort((a, b) => {
    const pa = Number(a.recommended_priority ?? 999);
    const pb = Number(b.recommended_priority ?? 999);
    if (pa !== pb) return pa - pb;
    return String(a.provider_id).localeCompare(String(b.provider_id));
  });
  const urgent =
    sorted.find((r) => r.readiness_tier === "BLOCKED") ??
    sorted.find((r) => r.readiness_tier === "ACTION_REQUIRED") ??
    sorted.find((r) => r.freshness_class === "STALE") ??
    sorted.find((r) => r.freshness_class === "NOT_CHECKED") ??
    sorted.find((r) => r.setup_status === "MISSING_OPTIONAL_SECRET");
  return urgent ? urgent.provider_id : sorted[0]?.provider_id ?? null;
}

export function buildProviderReadinessModel(
  providerSetup: UiProviderSetupConsolePayload | null | undefined,
  providerHealth: unknown,
): ProviderReadinessModel {
  const h = asRecord(providerHealth);
  const rows: ProviderReadinessRow[] = (providerSetup?.entries ?? []).map((entry) => ({
    ...entry,
    __id: entry.provider_id,
    env_hint_lines: envHintLines(entry.expected_env_vars),
    freshness_line: freshnessLine(entry),
    safety_line: safetyLine(entry),
  }));

  return {
    generated_at_utc: providerSetup?.generated_at_utc ?? null,
    samples_manifest_digest_prefix:
      asString(providerSetup?.samples_manifest_digest_prefix) ??
      asString(h?.samples_manifest_digest_prefix) ??
      null,
    samples_manifest_path: asString(providerSetup?.samples_manifest_path) ?? asString(h?.samples_manifest_path) ?? null,
    execution_workflow_blockers: Array.isArray(providerSetup?.execution_workflow_blockers)
      ? providerSetup?.execution_workflow_blockers.map(String)
      : [],
    trust_status: asString(h?.summary != null ? (asRecord(h.summary)?.trust_status as unknown) : undefined) ?? "UNKNOWN",
    summary: summaryFromPayload(providerSetup),
    rows,
    recommended_next_provider_id: recommendedNext(rows),
  };
}

export function providerReadinessPaneStatus(model: ProviderReadinessModel): string {
  if (model.rows.length === 0) return "UNKNOWN";
  if (model.summary.blocked_count > 0) return "BLOCKED";
  if (model.summary.action_required_count > 0 || model.summary.missing_secret_count > 0) return "ACTION_REQUIRED";
  if (model.summary.stale_count > 0 || model.summary.not_checked_count > 0) return "WARN";
  return "READY";
}
