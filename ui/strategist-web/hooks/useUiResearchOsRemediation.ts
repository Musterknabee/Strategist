"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsRemediationLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsRemediationLatest,
    queryFn: () => strategistGetJson("/ui/research-os/remediation/latest"),
  });
}
