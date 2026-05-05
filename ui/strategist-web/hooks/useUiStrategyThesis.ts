"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyThesisLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiStrategyThesisLatest,
    "/ui/strategy-thesis/latest",
  );
}

export function useUiStrategyThesisGenerationLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiStrategyThesisGenerationLatest,
    "/ui/strategy-thesis/generation/latest",
  );
}
