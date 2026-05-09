"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticReleaseHandoffPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticReleaseQuery = {
  searchRoot?: Nullable<string>;
  artifactKind?: Nullable<string>;
  recommendedAction?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  bundleIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  readyForAdjudication?: Nullable<boolean>;
  verified?: Nullable<boolean>;
  requireBlockers?: Nullable<boolean>;
  limit?: Nullable<number>;
  includeRaw?: Nullable<boolean>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticReleaseQuery): string {
  if (!query) return "/ui/semantic-release";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "bundle_id_contains", query.bundleIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "ready_for_adjudication", query.readyForAdjudication);
  append(params, "verified", query.verified);
  append(params, "require_blockers", query.requireBlockers);
  append(params, "limit", query.limit);
  append(params, "include_raw", query.includeRaw);
  if (query.artifactKind) params.append("artifact_kind", query.artifactKind);
  if (query.recommendedAction) params.append("recommended_action", query.recommendedAction);
  const qs = params.toString();
  return qs ? `/ui/semantic-release?${qs}` : "/ui/semantic-release";
}

export function useUiSemanticRelease(query?: UiSemanticReleaseQuery) {
  return useReadPlaneJsonQuery<UiSemanticReleaseHandoffPayload>(queryKeys.uiSemanticReleaseFiltered(query ?? {}), buildPath(query));
}
