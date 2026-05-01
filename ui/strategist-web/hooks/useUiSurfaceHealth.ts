"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiSurfaceHealth() {
  return useQuery({
    queryKey: queryKeys.uiHealth,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/health");
      return data;
    },
  });
}
