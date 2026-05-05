"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiWorkboardPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiWorkboard(boardLabel: string = "operator") {
  const path = `/ui/workboard?${new URLSearchParams({ board_label: boardLabel }).toString()}`;
  return useReadPlaneJsonQuery<UiWorkboardPayload>(queryKeys.uiWorkboard(boardLabel), path);
}
