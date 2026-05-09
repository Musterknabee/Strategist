"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffCustodyPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffCustodyQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  custodyStatus?: Nullable<string>;
  trustBanner?: Nullable<string>;
  custodySealRecorded?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffCustodyQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/custody";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "custody_seal_recorded", query.custodySealRecorded);
  append(params, "limit", query.limit);
  if (query.custodyStatus) params.append("custody_status", query.custodyStatus);
  if (query.trustBanner) params.append("trust_banner", query.trustBanner);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/custody?${qs}` : "/ui/semantic-validator-handoff/custody";
}

export function useUiSemanticValidatorHandoffCustody(query?: UiSemanticValidatorHandoffCustodyQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffCustodyPayload>(
    queryKeys.uiSemanticValidatorHandoffCustodyFiltered(query ?? {}),
    buildPath(query),
  );
}
