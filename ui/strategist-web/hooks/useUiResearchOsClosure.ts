"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsClosureLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsClosureLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/research-os/closure/latest");
      return data;
    },
  });
}
