"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsDriftLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiResearchOsDriftLatest,
    "/ui/research-os/drift/latest",
  );
}
