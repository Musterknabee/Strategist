"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffExceptionsPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffExceptionsQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  exceptionState?: Nullable<string>;
  exceptionKind?: Nullable<string>;
  priority?: Nullable<string>;
  severity?: Nullable<string>;
  includeResolved?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffExceptionsQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/exceptions";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "include_resolved", query.includeResolved);
  append(params, "limit", query.limit);
  if (query.exceptionState) params.append("exception_state", query.exceptionState);
  if (query.exceptionKind) params.append("exception_kind", query.exceptionKind);
  if (query.priority) params.append("priority", query.priority);
  if (query.severity) params.append("severity", query.severity);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/exceptions?${qs}` : "/ui/semantic-validator-handoff/exceptions";
}

export function useUiSemanticValidatorHandoffExceptions(query?: UiSemanticValidatorHandoffExceptionsQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffExceptionsPayload>(
    queryKeys.uiSemanticValidatorHandoffExceptionsFiltered(query ?? {}),
    buildPath(query),
  );
}
