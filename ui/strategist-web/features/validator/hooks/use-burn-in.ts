"use client";

import { useQuery } from "@tanstack/react-query";

import type { UiBurnInDashboard } from "@/lib/contracts/ui";

export function useBurnIn() {
  return useQuery<UiBurnInDashboard>({
    queryKey: ["ui", "burnin"],
    queryFn: async () => {
      const response = await fetch("/api/ui/burn-in", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load burn-in dashboard payload.");
      }
      return response.json();
    },
    refetchInterval: 30_000,
  });
}
