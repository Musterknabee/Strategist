"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiPaperBrokerStatus() {
  return useQuery({
    queryKey: queryKeys.uiPaperBrokerStatus,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/paper-broker/status");
      return data;
    },
  });
}
