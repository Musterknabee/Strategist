"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiEvidence(searchRoot?: string) {
  const q = searchRoot ? `?search_root=${encodeURIComponent(searchRoot)}` : "";
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiEvidence(searchRoot), `/ui/evidence${q}`);
}
