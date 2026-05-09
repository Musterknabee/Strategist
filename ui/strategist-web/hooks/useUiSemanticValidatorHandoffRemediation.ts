"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffRemediationPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffRemediationQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  chainStatus?: Nullable<string>;
  remediationStatus?: Nullable<string>;
  severity?: Nullable<string>;
  requireOperatorAction?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffRemediationQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/remediation";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "require_operator_action", query.requireOperatorAction);
  append(params, "limit", query.limit);
  if (query.chainStatus) params.append("chain_status", query.chainStatus);
  if (query.remediationStatus) params.append("remediation_status", query.remediationStatus);
  if (query.severity) params.append("severity", query.severity);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/remediation?${qs}` : "/ui/semantic-validator-handoff/remediation";
}

export function useUiSemanticValidatorHandoffRemediation(query?: UiSemanticValidatorHandoffRemediationQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffRemediationPayload>(
    queryKeys.uiSemanticValidatorHandoffRemediationFiltered(query ?? {}),
    buildPath(query),
  );
}
