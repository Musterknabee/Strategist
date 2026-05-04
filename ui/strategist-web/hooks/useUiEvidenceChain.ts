"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import type { UiEvidenceChainPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiEvidenceChain() {
  return useQuery({
    queryKey: queryKeys.uiEvidenceChain,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiEvidenceChainPayload>("/ui/evidence-chain?readonly=true&limit=250");
      return data;
    },
  });
}
