"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { queryKeys } from "@/lib/query/keys";
import { readPlaneProbeQueryDefaults } from "@/lib/query/read-plane-query";

/** Read-plane deployment tier checks (ledger paths, backup roots, schema, repo key scan). */
export function useReadinessDeployment() {
  return useReadPlaneJsonQuery<Record<string, unknown>>(
    queryKeys.readinessDeployment,
    "/readiness/deployment",
    readPlaneProbeQueryDefaults(),
  );
}
