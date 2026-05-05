"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiBacktestForensicsPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiBacktestForensicsLatest() {
  return useReadPlaneJsonQuery<UiBacktestForensicsPayload>(
    queryKeys.uiBacktestForensicsLatest,
    "/ui/backtest-forensics/latest",
  );
}
