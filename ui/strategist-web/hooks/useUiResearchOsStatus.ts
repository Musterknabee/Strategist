"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsStatus() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiResearchOsStatus, "/ui/research-os/status");
}
