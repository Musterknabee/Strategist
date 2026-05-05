"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiShadowBookLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiShadowBookLatest, "/ui/shadow-book/latest");
}
