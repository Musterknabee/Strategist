"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";
import { ProvenanceStrip } from "@/features/shared/components/provenance-strip";
import { ReadPlaneDriftBanner } from "@/features/shared/components/read-plane-drift-banner";
import { ProviderIngressHealth } from "@/features/validator/components/provider-ingress-health";
import { ValidatorRouteHeader } from "@/features/validator/components/validator-route-header";
import { ValidatorSnapshotActions } from "@/features/validator/components/validator-snapshot-actions";
import { ReviewPacketActions } from "@/features/shared/components/review-packet-actions";
import { useBurnIn } from "@/features/validator/hooks/use-burn-in";
import { isReadPlaneDrifted } from "@/lib/read-plane";
import { DeepLinkContextPills } from "@/features/shared/components/deep-link-context-pills";

export default function ValidatorProvidersPage() {
  const { data, isLoading, isError } = useBurnIn();

  if (isLoading) return <div className="text-sm text-zinc-400">Loading provider ingress health…</div>;
  if (isError || !data) {
    return <Card><CardHeader><CardTitle>Provider ingress dashboard unavailable</CardTitle></CardHeader><CardContent className="text-sm text-zinc-400">Projection read failed. Check `/ui/burnin` or backend reachability.</CardContent></Card>;
  }

  const drifted = isReadPlaneDrifted(data.generated_at_utc, 30 * 60_000);
  const enabledCount = data.metrics.providerPaths.filter((provider) => provider.status === "ENABLED").length;

  return (
    <DomainPolicyGate domain="validator" title="Validator provider ingress">
      <div className="space-y-4">
        <DeepLinkContextPills />
        <ValidatorRouteHeader
          title="Provider ingress health"
          description="Review provider availability, provenance posture, and validator ingress expectations before using data-paths as corroborating evidence."
          posture={`${enabledCount}/${data.metrics.providerPaths.length} enabled`}
          rightSlot={
            <div className="flex flex-wrap justify-end gap-2">
              <ReviewPacketActions
                packetKind="validator-provider-ingress"
                pagePayload={data.metrics.providerPaths}
                provenance={{ generatedAtUtc: data.generated_at_utc, providerCount: data.metrics.providerPaths.length }}
                notes={[
                  "Provider ingress review packets remain read-plane only.",
                  `${enabledCount} providers are currently marked enabled in the projection.`,
                ]}
              />
              <ValidatorSnapshotActions payload={data.metrics.providerPaths} fileStem="strategist-validator-provider-health" />
            </div>
          }
        />
        <ProvenanceStrip provenance={{ generatedAtUtc: data.generated_at_utc, sourceLabel: "validator provider projection", verificationLabel: "provider path posture hydrated", verificationTone: enabledCount ? "verified" : "restricted", projectionFamily: "validator", trustLabel: `${enabledCount} enabled providers` }} />
        <ReadPlaneDriftBanner drifted={drifted} message="Provider ingress health is stale. Treat enablement state as historical until the validator read-plane refreshes." />
        <ProviderIngressHealth data={data} />
      </div>
    </DomainPolicyGate>
  );
}
