"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { UiOperatorCommandReceipt } from "@/lib/contracts/ui";
import { useCommandReceiptLane } from "@/features/shared/command-receipts/command-receipt-lane-provider";

export function useOperatorCommand() {
  const queryClient = useQueryClient();
  const { pushReceipt } = useCommandReceiptLane();

  return useMutation<UiOperatorCommandReceipt, Error, { action: string; payload: Record<string, unknown> }>({
    mutationFn: async ({ action, payload }) => {
      const response = await fetch(`/api/ui/commands/${action}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(`Failed to submit ${action} command.`);
      }
      return response.json();
    },
    onSuccess: (receipt) => {
      pushReceipt(receipt);
      queryClient.invalidateQueries({ queryKey: ["ui", "workboard"] });
      queryClient.invalidateQueries({ queryKey: ["ui", "pack-detail"] });
    },
  });
}
