"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchCompute() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiResearchCompute, "/ui/research-compute");
}
