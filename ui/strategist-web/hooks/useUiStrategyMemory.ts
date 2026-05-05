"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyMemoryLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiStrategyMemoryLatest,
    "/ui/strategy-memory/latest",
  );
}
