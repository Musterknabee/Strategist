"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffRunbookPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffRunbookQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  actionKind?: Nullable<string>;
  priority?: Nullable<string>;
  severity?: Nullable<string>;
  completed?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffRunbookQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/runbook";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "completed", query.completed);
  append(params, "limit", query.limit);
  if (query.actionKind) params.append("action_kind", query.actionKind);
  if (query.priority) params.append("priority", query.priority);
  if (query.severity) params.append("severity", query.severity);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/runbook?${qs}` : "/ui/semantic-validator-handoff/runbook";
}

export function useUiSemanticValidatorHandoffRunbook(query?: UiSemanticValidatorHandoffRunbookQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffRunbookPayload>(
    queryKeys.uiSemanticValidatorHandoffRunbookFiltered(query ?? {}),
    buildPath(query),
  );
}
