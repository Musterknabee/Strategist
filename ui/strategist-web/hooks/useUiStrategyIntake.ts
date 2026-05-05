"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import { strategistPostJson } from "@/lib/api/strategist-client";
import type {
  UiStrategyIntakeLatestPayload,
  UiStrategyIntakeReceipt,
  UiStrategyIntakeRequest,
} from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyIntakeLatest() {
  return useReadPlaneJsonQuery<UiStrategyIntakeLatestPayload>(
    queryKeys.uiStrategyIntakeLatest,
    "/ui/strategy-intake/latest",
  );
}

export type UiStrategyIntakeMutationInput = {
  request: UiStrategyIntakeRequest;
  mutationToken?: string | null;
};

export function useSubmitUiStrategyIntake() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ request, mutationToken }: UiStrategyIntakeMutationInput) => {
      const { data } = await strategistPostJson<UiStrategyIntakeRequest, UiStrategyIntakeReceipt>(
        "/ui/strategy-intake",
        request,
        { mutationToken, operatorId: request.operator_id },
      );
      return data;
    },
    onSuccess: async (receipt) => {
      if (receipt.accepted !== true) return;
      const boardLabel = "operator";
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyIntakeLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyThesisLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyThesisGenerationLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyMemoryLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiWorkboard(boardLabel) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiOperatorActions }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiEvidenceChain }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiPaperTrackingLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyGraveyardLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyBatchesLatest }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiBacktestForensicsLatest }),
      ]);
    },
  });
}
