"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsStatus() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsStatus,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/research-os/status");
      return data;
    },
  });
}
