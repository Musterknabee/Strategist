"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiBacktestForensicsPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export type UiBacktestForensicsQuery = {
  reviewPosture?: string | null;
  status?: string | null;
  riskFlag?: string | null;
  dataPlane?: string | null;
  promotionEligible?: boolean | null;
  strategyIdContains?: string | null;
  blockerContains?: string | null;
  warningContains?: string | null;
  limit?: number | null;
};

function backtestForensicsPath(params?: UiBacktestForensicsQuery): string {
  const q = new URLSearchParams();
  const set = (key: string, value: string | null | undefined) => {
    const text = value?.trim();
    if (text) q.set(key, text);
  };
  if (params?.reviewPosture) q.append("review_posture", params.reviewPosture);
  if (params?.status) q.append("status", params.status);
  if (params?.riskFlag) q.append("risk_flag", params.riskFlag);
  if (params?.dataPlane) q.append("data_plane", params.dataPlane);
  if (params?.promotionEligible !== undefined && params.promotionEligible !== null) {
    q.set("promotion_eligible", String(params.promotionEligible));
  }
  set("strategy_id_contains", params?.strategyIdContains);
  set("blocker_contains", params?.blockerContains);
  set("warning_contains", params?.warningContains);
  if (params?.limit && Number.isFinite(params.limit)) q.set("limit", String(Math.max(1, Math.floor(params.limit))));
  const suffix = q.toString();
  return `/ui/backtest-forensics/latest${suffix ? `?${suffix}` : ""}`;
}

export function useUiBacktestForensicsLatest(params?: UiBacktestForensicsQuery) {
  return useReadPlaneJsonQuery<UiBacktestForensicsPayload>(
    queryKeys.uiBacktestForensicsFiltered(params ?? {}),
    backtestForensicsPath(params),
  );
}
