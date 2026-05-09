"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffAuditPacketPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffAuditPacketQuery = {
  searchRoot?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  packetStatus?: Nullable<string>;
  trustBanner?: Nullable<string>;
  auditReady?: Nullable<boolean>;
  operatorAttentionRequired?: Nullable<boolean>;
  limit?: Nullable<number>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffAuditPacketQuery): string {
  if (!query) return "/ui/semantic-validator-handoff/audit-packet";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "audit_ready", query.auditReady);
  append(params, "operator_attention_required", query.operatorAttentionRequired);
  append(params, "limit", query.limit);
  if (query.packetStatus) params.append("packet_status", query.packetStatus);
  if (query.trustBanner) params.append("trust_banner", query.trustBanner);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff/audit-packet?${qs}` : "/ui/semantic-validator-handoff/audit-packet";
}

export function useUiSemanticValidatorHandoffAuditPacket(query?: UiSemanticValidatorHandoffAuditPacketQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffAuditPacketPayload>(
    queryKeys.uiSemanticValidatorHandoffAuditPacketFiltered(query ?? {}),
    buildPath(query),
  );
}
