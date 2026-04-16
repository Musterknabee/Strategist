"use client";

import { useQuery } from "@tanstack/react-query";

import type { UiRuntimeStatus } from "@/lib/contracts/ui";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";

export function useRuntimeStatus() {
  const { operatorRole } = useDomainBoundary();

  return useQuery<UiRuntimeStatus>({
    queryKey: ["ui", "runtime", operatorRole],
    queryFn: async () => {
      const response = await fetch(`/api/ui/runtime?role=${encodeURIComponent(operatorRole)}`, { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load runtime status payload.");
      }
      return response.json();
    },
    refetchInterval: 10_000,
  });
}
