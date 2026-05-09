"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiOperatorCommandPolicyProjectionPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export type UiOperatorCommandPolicyQuery = {
  action?: string | null;
  operatorId?: string | null;
  workItemKey?: string | null;
  reviewTarget?: string | null;
  packKind?: string | null;
  manifestPath?: string | null;
  idempotencyKey?: string | null;
  assumeTokenPresent?: boolean;
  tokenDelivery?: "authorization" | "x_strategy_validator_token";
  principalId?: string | null;
  role?: string | null;
  scopes?: string[];
};

function operatorCommandPolicyPath(params?: UiOperatorCommandPolicyQuery): string {
  const q = new URLSearchParams();
  const set = (key: string, value: string | null | undefined) => {
    const text = value?.trim();
    if (text) q.set(key, text);
  };
  if (params?.action && params.action !== "all") q.append("action", params.action);
  set("operator_id", params?.operatorId);
  set("work_item_key", params?.workItemKey);
  set("review_target", params?.reviewTarget);
  set("pack_kind", params?.packKind);
  set("manifest_path", params?.manifestPath);
  set("idempotency_key", params?.idempotencyKey);
  set("principal_id", params?.principalId);
  set("role", params?.role);
  if (params?.assumeTokenPresent) q.set("assume_token_present", "true");
  if (params?.tokenDelivery) q.set("token_delivery", params.tokenDelivery);
  for (const scope of params?.scopes ?? []) {
    const text = scope.trim();
    if (text) q.append("scope", text);
  }
  const suffix = q.toString();
  return `/ui/commands/policy${suffix ? `?${suffix}` : ""}`;
}

export function useUiOperatorCommandPolicy(params?: UiOperatorCommandPolicyQuery) {
  return useReadPlaneJsonQuery<UiOperatorCommandPolicyProjectionPayload>(
    queryKeys.uiOperatorCommandPolicy(params ?? {}),
    operatorCommandPolicyPath(params),
  );
}
