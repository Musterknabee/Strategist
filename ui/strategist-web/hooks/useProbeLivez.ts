"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistProbeGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useProbeLivez() {
  return useQuery({
    queryKey: queryKeys.probeLivez,
    queryFn: async () => {
      const { data, status } = await strategistProbeGetJson<Record<string, unknown>>("/livez");
      return { data, httpStatus: status };
    },
  });
}
