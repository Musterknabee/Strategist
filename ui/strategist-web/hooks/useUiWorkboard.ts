"use client";

import { useQuery } from "@tanstack/react-query";
import { strategistGetJson } from "@/lib/api/strategist-client";
import type { UiWorkboardPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiWorkboard(boardLabel: string = "operator") {
  return useQuery({
    queryKey: queryKeys.uiWorkboard(boardLabel),
    queryFn: async () => {
      const q = new URLSearchParams({ board_label: boardLabel });
      const { data } = await strategistGetJson<UiWorkboardPayload>(`/ui/workboard?${q.toString()}`);
      return data;
    },
  });
}
