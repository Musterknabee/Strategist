"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiOperatorActionJournalPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export type UiOperatorActionsQuery = {
  operatorId?: string | null;
  action?: string | null;
  status?: string | null;
  accepted?: boolean | null;
  controlPlaneOnly?: boolean;
  issueCode?: string | null;
  authorizationRole?: string | null;
  reviewTarget?: string | null;
  workItemKey?: string | null;
  limit?: number | null;
};

function operatorActionsPath(params?: UiOperatorActionsQuery): string {
  const q = new URLSearchParams();
  q.set("readonly", "true");
  const set = (key: string, value: string | null | undefined) => {
    const text = value?.trim();
    if (text) q.set(key, text);
  };
  set("operator_id", params?.operatorId);
  set("authorization_role", params?.authorizationRole);
  set("review_target", params?.reviewTarget);
  set("work_item_key", params?.workItemKey);
  if (params?.action) q.append("action", params.action);
  if (params?.status) q.append("status", params.status);
  if (params?.accepted !== undefined && params.accepted !== null) q.set("accepted", String(params.accepted));
  if (params?.controlPlaneOnly) q.set("control_plane_only", "true");
  if (params?.issueCode) q.append("issue_code", params.issueCode);
  if (params?.limit && Number.isFinite(params.limit)) q.set("limit", String(Math.max(1, Math.floor(params.limit))));
  const suffix = q.toString();
  return `/ui/operator-actions${suffix ? `?${suffix}` : ""}`;
}

export function useUiOperatorActions(params?: UiOperatorActionsQuery) {
  return useReadPlaneJsonQuery<UiOperatorActionJournalPayload>(
    queryKeys.uiOperatorActionsFiltered(params ?? {}),
    operatorActionsPath(params),
  );
}
