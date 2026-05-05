"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiProviderHealth() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiProviderHealth, "/ui/provider-health");
}
