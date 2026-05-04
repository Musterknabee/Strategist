"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export function useUiResearchOsReviewJournalLatest() {
  return useQuery({
    queryKey: queryKeys.uiResearchOsReviewJournalLatest,
    queryFn: () => strategistGetJson("/ui/research-os/review-journal/latest"),
  });
}
