"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";
import { readPlaneProbeQueryDefaults } from "@/lib/query/read-plane-query";

export function useProbeHealthz() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.probeHealthz,
    "/healthz",
    readPlaneProbeQueryDefaults(),
  );
}
