"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsBriefingLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiResearchOsBriefingLatest,
    "/ui/research-os/briefing/latest",
  );
}
