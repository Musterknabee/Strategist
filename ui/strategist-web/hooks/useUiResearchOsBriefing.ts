"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsBriefingLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsBriefingLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/research-os/briefing/latest");
      return data;
    },
  });
}
