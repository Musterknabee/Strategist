"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsDriftLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsDriftLatest,
    queryFn: () => strategistGetJson("/ui/research-os/drift/latest"),
  });
}
