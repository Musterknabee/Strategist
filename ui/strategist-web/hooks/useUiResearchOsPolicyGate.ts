"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsPolicyGateLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsPolicyGateLatest,
    queryFn: () => strategistGetJson("/ui/research-os/policy-gate/latest"),
  });
}
