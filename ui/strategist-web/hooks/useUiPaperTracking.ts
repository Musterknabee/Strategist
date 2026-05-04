"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiPaperTrackingLatest() {
  return useQuery({
    queryKey: queryKeys.uiPaperTrackingLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/paper-tracking/latest");
      return data;
    },
  });
}

export function useUiPaperTrackingDetail(trackingId: string | null) {
  return useQuery({
    queryKey: queryKeys.uiPaperTrackingDetail(trackingId ?? ""),
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>(
        `/ui/paper-tracking/${encodeURIComponent(trackingId ?? "")}`,
      );
      return data;
    },
    enabled: Boolean(trackingId && trackingId.length > 0),
  });
}
