"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffContinuityPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffContinuityQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  terminalStatus?: Nullable<string>;
  currentStage?: Nullable<string>;
  openAction?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffContinuityQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/continuity";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "open_action", query.openAction);
  append(params, "limit", query.limit);
  if (query.terminalStatus) params.append("terminal_status", query.terminalStatus);
  if (query.currentStage) params.append("current_stage", query.currentStage);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/continuity?${qs}` : "/ui/semantic-validator-handoff/continuity";
}

export function useUiSemanticValidatorHandoffContinuity(query?: UiSemanticValidatorHandoffContinuityQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffContinuityPayload>(
    queryKeys.uiSemanticValidatorHandoffContinuityFiltered(query ?? {}),
    buildPath(query),
  );
}
