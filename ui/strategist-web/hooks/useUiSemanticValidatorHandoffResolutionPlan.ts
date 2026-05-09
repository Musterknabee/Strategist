"use client";
import { useReadPlaneJsonQuery } from "@/hooks/useReadPlaneJsonQuery";
import type { UiSemanticValidatorHandoffResolutionPlanPayload } from "@/lib/api/types";
import { queryKeys } from "@/lib/query/keys";
type Nullable<T> = T | null | undefined;
export type UiSemanticValidatorHandoffResolutionPlanQuery = { experimentIdContains?: Nullable<string>; issueContains?: Nullable<string>; phase?: Nullable<string>; priority?: Nullable<string>; trustBanner?: Nullable<string>; requiresExternalArtifact?: Nullable<boolean>; blocksHandoffClearance?: Nullable<boolean>; limit?: Nullable<number>; };
const append=(p:URLSearchParams,k:string,v:Nullable<string|number|boolean>)=>{ if(v!==null&&v!==undefined&&v!=="") p.set(k,String(v)); };
function path(q?:UiSemanticValidatorHandoffResolutionPlanQuery){ const p=new URLSearchParams(); if(q){ append(p,"experiment_id_contains",q.experimentIdContains); append(p,"issue_contains",q.issueContains); append(p,"requires_external_artifact",q.requiresExternalArtifact); append(p,"blocks_handoff_clearance",q.blocksHandoffClearance); append(p,"limit",q.limit); if(q.phase) p.append("phase",q.phase); if(q.priority) p.append("priority",q.priority); if(q.trustBanner) p.append("trust_banner",q.trustBanner); } const qs=p.toString(); return qs?`/ui/semantic-validator-handoff/resolution-plan?${qs}`:"/ui/semantic-validator-handoff/resolution-plan"; }
export function useUiSemanticValidatorHandoffResolutionPlan(query?: UiSemanticValidatorHandoffResolutionPlanQuery){ return useReadPlaneJsonQuery<UiSemanticValidatorHandoffResolutionPlanPayload>(queryKeys.uiSemanticValidatorHandoffResolutionPlanFiltered(query ?? {}), path(query)); }
