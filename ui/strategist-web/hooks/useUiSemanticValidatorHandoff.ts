"use client";

import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

type Nullable<T> = T | null | undefined;

export type UiSemanticValidatorHandoffQuery = {
  searchRoot?: Nullable<string>;
  artifactKind?: Nullable<string>;
  recommendedAction?: Nullable<string>;
  experimentIdContains?: Nullable<string>;
  certificateIdContains?: Nullable<string>;
  packetIdContains?: Nullable<string>;
  issueContains?: Nullable<string>;
  handoffAllowed?: Nullable<boolean>;
  verified?: Nullable<boolean>;
  readyForValidatorIngress?: Nullable<boolean>;
  requireBlockers?: Nullable<boolean>;
  limit?: Nullable<number>;
  includeRaw?: Nullable<boolean>;
};

function append(params: URLSearchParams, key: string, value: Nullable<string | number | boolean>) {
  if (value === null || value === undefined || value === "") return;
  params.set(key, String(value));
}

function buildPath(query?: UiSemanticValidatorHandoffQuery): string {
  if (!query) return "/ui/semantic-validator-handoff";
  const params = new URLSearchParams();
  append(params, "search_root", query.searchRoot);
  append(params, "experiment_id_contains", query.experimentIdContains);
  append(params, "certificate_id_contains", query.certificateIdContains);
  append(params, "packet_id_contains", query.packetIdContains);
  append(params, "issue_contains", query.issueContains);
  append(params, "handoff_allowed", query.handoffAllowed);
  append(params, "verified", query.verified);
  append(params, "ready_for_validator_ingress", query.readyForValidatorIngress);
  append(params, "require_blockers", query.requireBlockers);
  append(params, "limit", query.limit);
  append(params, "include_raw", query.includeRaw);
  if (query.artifactKind) params.append("artifact_kind", query.artifactKind);
  if (query.recommendedAction) params.append("recommended_action", query.recommendedAction);
  const qs = params.toString();
  return qs ? `/ui/semantic-validator-handoff?${qs}` : "/ui/semantic-validator-handoff";
}

export function useUiSemanticValidatorHandoff(query?: UiSemanticValidatorHandoffQuery) {
  return useReadPlaneJsonQuery<UiSemanticValidatorHandoffPayload>(queryKeys.uiSemanticValidatorHandoffFiltered(query ?? {}), buildPath(query));
}
