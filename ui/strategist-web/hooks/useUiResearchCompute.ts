"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiResearchComputePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiResearchComputeQuery = {
  artifactRoot?: Nullable<string>;
  backendUsed?: Nullable<string>;
  fallbackReason?: Nullable<string>;
  strategyIdContains?: Nullable<string>;
  taskContains?: Nullable<string>;
  warningContains?: Nullable<string>;
  blockerContains?: Nullable<string>;
  limit?: Nullable<number>;
  includeRaw?: Nullable<boolean>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiResearchComputeQuery): string {
  if (!query) return "/ui/research-compute";
  const params = new URLSearchParams();
  append(params, "artifact_root", query.artifactRoot);
  append(params, "strategy_id_contains", query.strategyIdContains);
  append(params, "task_contains", query.taskContains);
  append(params, "warning_contains", query.warningContains);
  append(params, "blocker_contains", query.blockerContains);
  append(params, "limit", query.limit);
  append(params, "include_raw", query.includeRaw);
  if (query.backendUsed) params.append("backend_used", query.backendUsed);
  if (query.fallbackReason) params.append("fallback_reason", query.fallbackReason);
  const qs = params.toString();
  return qs ? `/ui/research-compute?${qs}` : "/ui/research-compute";
}

export function useUiResearchCompute(query?: UiResearchComputeQuery) {
  return useReadPlaneJsonQuery<UiResearchComputePayload>(queryKeys.uiResearchComputeFiltered(query ?? {}), buildPath(query));
}
