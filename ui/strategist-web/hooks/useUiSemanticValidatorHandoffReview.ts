"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffReviewPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffReviewQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  reviewStatus?: Nullable<string>;
  trustBanner?: Nullable<string>;
  operatorReviewAllowed?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffReviewQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/review";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "operator_review_allowed", query.operatorReviewAllowed);
  append(params, "limit", query.limit);
  if (query.reviewStatus) params.append("review_status", query.reviewStatus);
  if (query.trustBanner) params.append("trust_banner", query.trustBanner);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/review?${qs}` : "/ui/semantic-validator-handoff/review";
}

export function useUiSemanticValidatorHandoffReview(query?: UiSemanticValidatorHandoffReviewQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffReviewPayload>(
    queryKeys.uiSemanticValidatorHandoffReviewFiltered(query ?? {}),
    buildPath(query),
  );
}
