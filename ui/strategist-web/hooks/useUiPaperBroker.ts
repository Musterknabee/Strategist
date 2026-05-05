"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiPaperBrokerStatus() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiPaperBrokerStatus,
    "/ui/paper-broker/status",
  );
}
