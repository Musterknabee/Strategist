"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistProbeGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";
import { readPlaneProbeQueryDefaults } from "@/lib/query/read-plane-query";

type ReadyzPayload = { data: Record<string, unknown> | null; httpStatus: number };

export function useProbeReadyz() {
  return useQuery({
    ...readPlaneProbeQueryDefaults<ReadyzPayload>(),
    queryKey: queryKeys.probeReadyz,
    queryFn: async () => {
      const { data, status } = await strategistProbeGetJson<Record<string, unknown>>("/readyz");
      return { data, httpStatus: status };
    },
  });
}
