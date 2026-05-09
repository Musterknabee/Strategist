"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffClosurePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffClosureQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  closureStatus?: Nullable<string>;
  trustBanner?: Nullable<string>;
  closureAttestationRecorded?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffClosureQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/closure";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "closure_attestation_recorded", query.closureAttestationRecorded);
  append(params, "limit", query.limit);
  if (query.closureStatus) params.append("closure_status", query.closureStatus);
  if (query.trustBanner) params.append("trust_banner", query.trustBanner);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/closure?${qs}` : "/ui/semantic-validator-handoff/closure";
}

export function useUiSemanticValidatorHandoffClosure(query?: UiSemanticValidatorHandoffClosureQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffClosurePayload>(
    queryKeys.uiSemanticValidatorHandoffClosureFiltered(query ?? {}),
    buildPath(query),
  );
}
