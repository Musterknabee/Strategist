"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiProviderHealth() {
  return useQuery({
    queryKey: queryKeys.uiProviderHealth,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/provider-health");
      return data;
    },
  });
}
