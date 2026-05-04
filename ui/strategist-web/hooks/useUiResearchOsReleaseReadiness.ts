"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsReleaseReadinessLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsReleaseReadinessLatest,
    queryFn: () => strategistGetJson("/ui/research-os/release-readiness/latest"),
  });
}
