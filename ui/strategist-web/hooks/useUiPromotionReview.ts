"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiPromotionReviewPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiPromotionReviewQuery = {
  paperTrackingRoot?: Nullable<string>;
  recommendation?: Nullable<string>;
  lifecycleState?: Nullable<string>;
  trackingId?: Nullable<string>;
  strategyIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  requireBlockers?: Nullable<boolean>;
  limit?: Nullable<number>;
  includeRaw?: Nullable<boolean>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiPromotionReviewQuery): string {
  if (!query) return "/ui/promotion-review";
  const params = new URLSearchParams();
  append(params, "paper_tracking_root", query.paperTrackingRoot);
  append(params, "tracking_id", query.trackingId);
  append(params, "strategy_id_contains", query.strategyIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "require_blockers", query.requireBlockers);
  append(params, "limit", query.limit);
  append(params, "include_raw", query.includeRaw);
  if (query.recommendation) params.append("recommendation", query.recommendation);
  if (query.lifecycleState) params.append("lifecycle_state", query.lifecycleState);
  const qs = params.toString();
  return qs ? `/ui/promotion-review?${qs}` : "/ui/promotion-review";
}

export function useUiPromotionReview(query?: UiPromotionReviewQuery) {
  return useReadPlaneJsonQuery<UiPromotionReviewPayload>(queryKeys.uiPromotionReviewFiltered(query ?? {}), buildPath(query));
}
