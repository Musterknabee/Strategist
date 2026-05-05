"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiSurfaceHealth() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiHealth, "/ui/health");
}
