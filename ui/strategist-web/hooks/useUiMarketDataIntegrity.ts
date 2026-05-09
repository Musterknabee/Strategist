"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiMarketDataIntegrityPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export type UiMarketDataIntegrityQuery = {
  gateStatus?: string | null;
  providerId?: string | null;
  adjustedStatus?: string | null;
  strategyIdContains?: string | null;
  blockerContains?: string | null;
  warningContains?: string | null;
  limit?: number | null;
};

function marketDataIntegrityPath(params?: UiMarketDataIntegrityQuery): string {
  const q = new URLSearchParams();
  const set = (key: string, value: string | null | undefined) => {
    const text = value?.trim();
    if (text) q.set(key, text);
  };
  if (params?.gateStatus) q.append("gate_status", params.gateStatus);
  set("provider_id", params?.providerId);
  if (params?.adjustedStatus) q.append("adjusted_status", params.adjustedStatus);
  set("strategy_id_contains", params?.strategyIdContains);
  set("blocker_contains", params?.blockerContains);
  set("warning_contains", params?.warningContains);
  if (params?.limit && Number.isFinite(params.limit)) q.set("limit", String(Math.max(1, Math.floor(params.limit))));
  const suffix = q.toString();
  return `/ui/market-data-integrity${suffix ? `?${suffix}` : ""}`;
}

export function useUiMarketDataIntegrity(params?: UiMarketDataIntegrityQuery) {
  return useReadPlaneJsonQuery<UiMarketDataIntegrityPayload>(
    queryKeys.uiMarketDataIntegrityFiltered(params ?? {}),
    marketDataIntegrityPath(params),
  );
}
