"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { strategistGetJson, strategistPostJson } from "@/lib/api/strategist-client";
import type {
  UiStrategyIntakeLatestPayload,
  UiStrategyIntakeReceipt,
  UiStrategyIntakeRequest,
} from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export function useUiStrategyIntakeLatest() {
  return useQuery({
    queryKey: queryKeys.uiStrategyIntakeLatest,
    queryFn: async () => {
      const { data } = await strategistGetJson<UiStrategyIntakeLatestPayload>("/ui/strategy-intake/latest");
      return data;
    },
  });
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
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: queryKeys.uiStrategyIntakeLatest });
    },
  });
}
