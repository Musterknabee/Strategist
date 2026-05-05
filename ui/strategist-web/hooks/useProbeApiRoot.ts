"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";
import { readPlaneProbeQueryDefaults } from "@/lib/query/read-plane-query";

/** GET / on the API host (operator banner JSON), not the Next.js app root. */
export function useProbeApiRoot() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(queryKeys.probeApiRoot, "/", {
    ...readPlaneProbeQueryDefaults(),
    retry: false,
  });
}
