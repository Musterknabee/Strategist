"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiStrategyGraveyardPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyGraveyardLatest() {
  return useReadPlaneJsonQuery<UiStrategyGraveyardPayload>(
    queryKeys.uiStrategyGraveyardLatest,
    "/ui/strategy-graveyard/latest",
  );
}
