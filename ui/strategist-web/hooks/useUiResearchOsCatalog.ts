"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsCatalogLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiResearchOsCatalogLatest,
    "/ui/research-os/catalog/latest",
  );
}
