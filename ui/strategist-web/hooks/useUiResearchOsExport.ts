"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsExportLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiResearchOsExportLatest,
    "/ui/research-os/export/latest",
  );
}
