"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyBatchLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiStrategyBatchesLatest,
    "/ui/strategy-batches/latest",
  );
}

export function useUiStrategyBatchList() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiStrategyBatchesList, "/ui/strategy-batches");
}

export function useUiStrategyBatchesLatest() {
  return useUiStrategyBatchLatest();
}

export function useUiStrategyBatches() {
  return useUiStrategyBatchList();
}
