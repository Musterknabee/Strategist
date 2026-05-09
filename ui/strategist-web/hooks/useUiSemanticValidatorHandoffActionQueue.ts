"use client";
import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffActionQueuePayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";
type Nullable<T> = T | null | undefined;
export type UiSemanticValidatorHandoffActionQueueQuery = { experimentIdContains?: Nullable<string>; issueContains?: Nullable<string>; queueState?: Nullable<string>; priority?: Nullable<string>; trustBanner?: Nullable<string>; externalArtifactRequired?: Nullable<boolean>; blocked?: Nullable<boolean>; limit?: Nullable<number>; };
const append=(p:URLSearchParams,k:string,v:Nullable<string|number|boolean>)=>{ if(v!==null&&v!==undefined&&v!=="") p.set(k,String(v)); };
function path(q?:UiSemanticValidatorHandoffActionQueueQuery){ const p=new URLSearchParams(); if(q){ append(p,"experiment_id_contains",q.experimentIdContains); append(p,"issue_contains",q.issueContains); append(p,"external_artifact_required",q.externalArtifactRequired); append(p,"blocked",q.blocked); append(p,"limit",q.limit); if(q.queueState) p.append("queue_state",q.queueState); if(q.priority) p.append("priority",q.priority); if(q.trustBanner) p.append("trust_banner",q.trustBanner); } const qs=p.toString(); return qs?`/ui/semantic-validator-handoff/action-queue?${qs}`:"/ui/semantic-validator-handoff/action-queue"; }
export function useUiSemanticValidatorHandoffActionQueue(query?: UiSemanticValidatorHandoffActionQueueQuery){ return useReadPlaneJsonQuery<UiSemanticValidatorHandoffActionQueuePayload>(queryKeys.uiSemanticValidatorHandoffActionQueueFiltered(query ?? {}), path(query)); }
