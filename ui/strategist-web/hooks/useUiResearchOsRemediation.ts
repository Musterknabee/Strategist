"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsRemediationLatest() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.uiResearchOsRemediationLatest,
    "/ui/research-os/remediation/latest",
  );
}
