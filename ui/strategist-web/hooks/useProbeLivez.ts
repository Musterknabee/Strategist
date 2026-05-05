"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistProbeGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";
import { readPlaneProbeQueryDefaults } from "@/lib/query/read-plane-query";

type LivezPayload = { data: Record<string, unknown> | null; httpStatus: number };

export function useProbeLivez() {
  return useQuery({
    ...readPlaneProbeQueryDefaults<LivezPayload>(),
    queryKey: queryKeys.probeLivez,
    queryFn: async () => {
      const { data, status } = await strategistProbeGetJson<Record<string, unknown>>("/livez");
      return { data, httpStatus: status };
    },
  });
}
