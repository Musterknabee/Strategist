"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";
import { ProvenanceStrip } from "@/features/shared/components/provenance-strip";
import { ReadPlaneDriftBanner } from "@/features/shared/components/read-plane-drift-banner";
import { BurnInMetrics } from "@/features/validator/components/burn-in-metrics";
import { ValidatorRouteHeader } from "@/features/validator/components/validator-route-header";
import { ValidatorSnapshotActions } from "@/features/validator/components/validator-snapshot-actions";
import { ReviewPacketActions } from "@/features/shared/components/review-packet-actions";
import { useBurnIn } from "@/features/validator/hooks/use-burn-in";
import { isReadPlaneDrifted } from "@/lib/read-plane";
import { DeepLinkContextPills } from "@/features/shared/components/deep-link-context-pills";

export default function ValidatorForensicPage() {
  const { data, isLoading, isError } = useBurnIn();

  if (isLoading) return <div className="text-sm text-zinc-400">Loading validator forensic projections…</div>;
  if (isError || !data) {
    return <Card><CardHeader><CardTitle>Validator forensic dashboard unavailable</CardTitle></CardHeader><CardContent className="text-sm text-zinc-400">Projection read failed. Check `/ui/burnin` or backend reachability.</CardContent></Card>;
  }

  const drifted = isReadPlaneDrifted(data.generated_at_utc, 30 * 60_000);
  const staleArtifacts = data.artifact_summary.total_stale_count > 0;

  return (
    <DomainPolicyGate domain="validator" title="Validator forensic review">
      <div className="space-y-4">
        <DeepLinkContextPills />
        <ValidatorRouteHeader
          title="Validator forensic review"
          description="Inspect CPCV stability, DSR/PBO posture, realism constraints, and provider provenance in a review-focused route."
          posture={data.metrics.dsrPbo.promotionPosture}
          rightSlot={
            <div className="flex flex-wrap justify-end gap-2">
              <ReviewPacketActions
                packetKind="validator-forensic"
                pagePayload={data}
                provenance={{ artifactSummary: data.artifact_summary, forensicSummary: data.metrics.forensicSummary }}
                notes={data.metrics.forensicSummary.forensic_notes}
              />
              <ValidatorSnapshotActions payload={data} fileStem="strategist-validator-forensic-snapshot" />
            </div>
          }
        />
        <ProvenanceStrip provenance={{ generatedAtUtc: data.generated_at_utc, sourceLabel: "validator forensic projection", verificationLabel: staleArtifacts ? "stale artifacts present" : "forensic artifacts hydrated", verificationTone: staleArtifacts ? "restricted" : "verified", projectionFamily: "validator", trustLabel: data.metrics.forensicSummary.overfit_risk }} />
        <ReadPlaneDriftBanner drifted={drifted} message="Forensic validator diagnostics are stale. Treat this page as historical evidence until the read-plane refreshes." />
        <BurnInMetrics data={data} initialExecutiveMode={false} />
      </div>
    </DomainPolicyGate>
  );
}
