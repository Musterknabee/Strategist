"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsAttestationLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsAttestationLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<Record<string, unknown>>("/ui/research-os/attestation/latest");
      return data;
    },
  });
}
