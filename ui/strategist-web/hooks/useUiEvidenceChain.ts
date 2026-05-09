"use client";

import { useMemo } from "react";
import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiEvidenceChainPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";

export type UiEvidenceChainQuery = {
  streamFamily?: string | null;
  issueCode?: string | null;
  status?: string | null;
  actorContains?: string | null;
  aggregateContains?: string | null;
  eventTypeContains?: string | null;
  chained?: boolean | null;
  limit?: number | null;
};

function appendIfPresent(qs: URLSearchParams, key: string, value: string | number | boolean | null | undefined) {
  if (value === null || value === undefined || value === "") return;
  qs.append(key, String(value));
}

function buildPath(query?: UiEvidenceChainQuery): string {
  const qs = new URLSearchParams();
  qs.set("readonly", "true");
  appendIfPresent(qs, "limit", query?.limit ?? 250);
  appendIfPresent(qs, "stream_family", query?.streamFamily);
  appendIfPresent(qs, "issue_code", query?.issueCode);
  appendIfPresent(qs, "status", query?.status);
  appendIfPresent(qs, "actor_contains", query?.actorContains?.trim());
  appendIfPresent(qs, "aggregate_contains", query?.aggregateContains?.trim());
  appendIfPresent(qs, "event_type_contains", query?.eventTypeContains?.trim());
  appendIfPresent(qs, "chained", query?.chained);
  return `/ui/evidence-chain?${qs.toString()}`;
}

export function useUiEvidenceChain(query?: UiEvidenceChainQuery) {
  const key = useMemo(() => (query ? queryKeys.uiEvidenceChainFiltered(query) : queryKeys.uiEvidenceChain), [query]);
  const path = useMemo(() => buildPath(query), [query]);
  return useReadPlaneJsonQuery<UiEvidenceChainPayload>(key, path);
}
