"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { strategistPostJson } from "@/lib/api/strategist-client";
import type {
  UiOperatorCommandAction,
  UiOperatorCommandReceipt,
  UiOperatorCommandRequest,
} from "@/lib/api/types";
import type { StrategistMutationTokenDelivery } from "@/lib/api/strategist-client";
import { invalidateReadPlaneAfterOperatorCommand } from "@/lib/query/operator-command-invalidation";

export type UiOperatorCommandMutationInput = {
  action: UiOperatorCommandAction;
  request: UiOperatorCommandRequest;
  mutationToken?: string | null;
  tokenDelivery?: StrategistMutationTokenDelivery;
};

/** Governed POST /ui/commands/{action} mutation (explicit token + operator headers only). */
export function useUiOperatorCommandMutation(boardLabel: string = "operator") {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ action, request, mutationToken, tokenDelivery }: UiOperatorCommandMutationInput) => {
      const { data } = await strategistPostJson<UiOperatorCommandRequest, UiOperatorCommandReceipt>(
        `/ui/commands/${encodeURIComponent(action)}`,
        request,
        { mutationToken, operatorId: request.operator_id, tokenDelivery },
      );
      return data;
    },
    onSuccess: async (receipt) => {
      await invalidateReadPlaneAfterOperatorCommand(queryClient, boardLabel, receipt);
    },
  });
}

/** @deprecated Use `useUiOperatorCommandMutation` (alias preserved for existing imports). */
export const useUiOperatorCommand = useUiOperatorCommandMutation;
