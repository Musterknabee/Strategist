"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffLineagePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffLineageQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  chainStatus?: Nullable<string>;
  readyForOperatorReview?: Nullable<boolean>;
  requireBrokenLinks?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffLineageQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/lineage";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "ready_for_operator_review", query.readyForOperatorReview);
  append(params, "require_broken_links", query.requireBrokenLinks);
  append(params, "limit", query.limit);
  if (query.chainStatus) params.append("chain_status", query.chainStatus);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/lineage?${qs}` : "/ui/semantic-validator-handoff/lineage";
}

export function useUiSemanticValidatorHandoffLineage(query?: UiSemanticValidatorHandoffLineageQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffLineagePayload>(
    queryKeys.uiSemanticValidatorHandoffLineageFiltered(query ?? {}),
    buildPath(query),
  );
}
