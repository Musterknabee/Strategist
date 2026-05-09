"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffSignoffPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffSignoffQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  signoffStatus?: Nullable<string>;
  trustBanner?: Nullable<string>;
  signoffRecorded?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffSignoffQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/signoff";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "signoff_recorded", query.signoffRecorded);
  append(params, "limit", query.limit);
  if (query.signoffStatus) params.append("signoff_status", query.signoffStatus);
  if (query.trustBanner) params.append("trust_banner", query.trustBanner);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/signoff?${qs}` : "/ui/semantic-validator-handoff/signoff";
}

export function useUiSemanticValidatorHandoffSignoff(query?: UiSemanticValidatorHandoffSignoffQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffSignoffPayload>(
    queryKeys.uiSemanticValidatorHandoffSignoffFiltered(query ?? {}),
    buildPath(query),
  );
}
