"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { strategistPostJson } from "@/lib/api/strategist-client";
import type {
  UiOperatorCommandAction,
  UiOperatorCommandReceipt,
  UiOperatorCommandRequest,
} from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export type UiOperatorCommandMutationInput = {
  action: UiOperatorCommandAction;
  request: UiOperatorCommandRequest;
  mutationToken?: string | null;
};

export function useUiOperatorCommand(boardLabel: string = "operator") {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ action, request, mutationToken }: UiOperatorCommandMutationInput) => {
      const { data } = await strategistPostJson<UiOperatorCommandRequest, UiOperatorCommandReceipt>(
        `/ui/commands/${encodeURIComponent(action)}`,
        request,
        { mutationToken, operatorId: request.operator_id },
      );
      return data;
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: queryKeys.uiWorkboard(boardLabel) }),
        queryClient.invalidateQueries({ queryKey: queryKeys.uiOperatorActions }),
      ]);
    },
  });
}
