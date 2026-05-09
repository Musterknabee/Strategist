"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffDecisionPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffDecisionQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  decisionStatus?: Nullable<string>;
  trustBanner?: Nullable<string>;
  decisionReady?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffDecisionQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/decision";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "decision_ready", query.decisionReady);
  append(params, "limit", query.limit);
  if (query.decisionStatus) params.append("decision_status", query.decisionStatus);
  if (query.trustBanner) params.append("trust_banner", query.trustBanner);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/decision?${qs}` : "/ui/semantic-validator-handoff/decision";
}

export function useUiSemanticValidatorHandoffDecision(query?: UiSemanticValidatorHandoffDecisionQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffDecisionPayload>(
    queryKeys.uiSemanticValidatorHandoffDecisionFiltered(query ?? {}),
    buildPath(query),
  );
}
