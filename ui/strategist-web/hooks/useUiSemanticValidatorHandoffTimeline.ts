"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffTimelinePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffTimelineQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  stage?: Nullable<string>;
  eventState?: Nullable<string>;
  severity?: Nullable<string>;
  includeReady?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffTimelineQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/timeline";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "include_ready", query.includeReady);
  append(params, "limit", query.limit);
  if (query.stage) params.append("stage", query.stage);
  if (query.eventState) params.append("event_state", query.eventState);
  if (query.severity) params.append("severity", query.severity);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/timeline?${qs}` : "/ui/semantic-validator-handoff/timeline";
}

export function useUiSemanticValidatorHandoffTimeline(query?: UiSemanticValidatorHandoffTimelineQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffTimelinePayload>(
    queryKeys.uiSemanticValidatorHandoffTimelineFiltered(query ?? {}),
    buildPath(query),
  );
}
