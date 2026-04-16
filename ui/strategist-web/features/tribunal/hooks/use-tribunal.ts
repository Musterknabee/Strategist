"use client";

import { useQuery } from "@tanstack/react-query";

import type { UiTribunalWorkspace } from "@/lib/contracts/ui";

export function useTribunal() {
  return useQuery<UiTribunalWorkspace>({
    queryKey: ["ui", "tribunal"],
    queryFn: async () => {
      const response = await fetch("/api/ui/tribunal", { cache: "no-store" });
      if (!response.ok) {
        throw new Error("Failed to load tribunal workspace payload.");
      }
      return response.json();
    },
    refetchInterval: 15_000,
  });
}
