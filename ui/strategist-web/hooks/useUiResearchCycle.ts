"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { strategistPostJson } from "@/lib/api/strategist-client";
import { queryKeys } from "@/lib/query/keys";

export type UiResearchCycleStatusPayload = Record<string, unknown>;

export type UiResearchCycleTriggerRequest = {
  operator_id: string;
  mode: "light" | "heavy";
  idempotency_key?: string | null;
};

export type UiResearchCycleTriggerReceipt = {
  schema_version?: string;
  accepted?: boolean;
  queued?: boolean;
  mode?: string;
  operator_message?: string;
  trigger_path?: string;
};

export function useUiResearchCycleStatusLatest() {
  return useReadPlaneJsonQuery<UiResearchCycleStatusPayload>(
    queryKeys.uiResearchCycleStatusLatest,
    "/ui/research-cycle/status/latest",
    { refetchInterval: 30_000 },
  );
}

export type UiResearchCycleTriggerInput = {
  request: UiResearchCycleTriggerRequest;
  mutationToken?: string | null;
};

export function useTriggerUiResearchCycle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ request, mutationToken }: UiResearchCycleTriggerInput) => {
      const { data } = await strategistPostJson<UiResearchCycleTriggerRequest, UiResearchCycleTriggerReceipt>(
        "/ui/research-cycle/trigger",
        request,
        { mutationToken, operatorId: request.operator_id },
      );
      return data;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.uiResearchCycleStatusLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiResearchOsStatus }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiResearchOsBriefingLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiResearchOsRunLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyBatchesLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyThesisGenerationLatest }),
      ]);
    },
  });
}
