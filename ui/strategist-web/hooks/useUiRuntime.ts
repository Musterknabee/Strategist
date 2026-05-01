"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiRuntime(role = "operator") {
  return useQuery({
    queryKey: queryKeys.uiRuntime(role),
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>(
        `/ui/runtime?role=${encodeURIComponent(role)}`,
      );
      return data;
    },
  });
}
