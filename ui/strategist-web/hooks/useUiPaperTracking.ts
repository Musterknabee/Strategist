"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiPaperTrackingLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiPaperTrackingLatest,
    "/ui/paper-tracking/latest",
  );
}

export function useUiPaperTrackingDetail(trackingId: string | null) {
  const id = trackingId ?? "";
  const path = `/ui/paper-tracking/${encodeURIComponent(id)}`;
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.uiPaperTrackingDetail(id), path, {
    enabled: Boolean(trackingId && trackingId.length > 0),
  });
}
