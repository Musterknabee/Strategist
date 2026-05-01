"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import type { UiFacadePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiFacade() {
  return useQuery({
    queryKey: queryKeys.uiFacade,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiFacadePayload>("/ui/facade");
      return data;
    },
  });
}
