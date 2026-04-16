"use client";

import Link from "next/link";
import type { Route } from "next";
import { useParams, usePathname, useRouter, useSearchParams } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PackOperatorGuidance } from "@/features/control-plane/components/pack-operator-guidance";
import { PackDetailPanel } from "@/features/control-plane/components/pack-detail-panel";
import { useOperatorCommand } from "@/features/control-plane/hooks/use-operator-command";
import { usePackDetail } from "@/features/control-plane/hooks/use-pack-detail";
import { ConsoleErrorState, ConsoleLoadingState } from "@/features/shared/components/console-state";
import { DomainPolicyGate } from "@/features/shared/components/domain-policy-gate";
import { ExportSnapshotActions } from "@/features/shared/components/export-snapshot-actions";
import { ProjectionDriftNotifier } from "@/features/shared/components/projection-drift-notifier";
import { ProvenanceStrip } from "@/features/shared/components/provenance-strip";
import { ReadPlaneDriftBanner } from "@/features/shared/components/read-plane-drift-banner";
import { ReviewPacketActions } from "@/features/shared/components/review-packet-actions";
import { isReadPlaneDrifted } from "@/lib/read-plane";

function jumpToSection(sectionId: string) {
  const element = document.getElementById(sectionId);
  if (!element) return;
  element.scrollIntoView({ behavior: "smooth", block: "start" });
}

export default function PackDetailPage() {
  const params = useParams<{ packKind: string }>();
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const packKind = typeof params.packKind === "string" ? params.packKind : undefined;
  const receiptId = searchParams.get("receipt");
  const reviewPacketId = searchParams.get("reviewPacket");
  const { data, isLoading, isError } = usePackDetail(packKind);
  const command = useOperatorCommand();

  const clearDeepLinkContext = (kind: "receipt" | "reviewPacket") => {
    const next = new URLSearchParams(searchParams.toString());
    next.delete(kind);
    const query = next.toString();
    const nextRoute = (query ? `${pathname}?${query}` : pathname) as Route;
    router.replace(nextRoute);
  };

  if (isLoading) return <ConsoleLoadingState title="Loading pack detail" message="Hydrating pack timeline, assignment, lease, escalation, and evidence projections…" />;
  if (isError || !data) {
    return <ConsoleErrorState title="Pack detail unavailable" message="Projection read failed for the selected pack. Check `/ui/packs/detail` and backend reachability." />;
  }

  const drifted = isReadPlaneDrifted(data.generated_at_utc);

  return (
    <DomainPolicyGate domain="control-plane" title="Pack detail">
      <div className="space-y-4">
        <ProvenanceStrip
          provenance={{
            generatedAtUtc: data.generated_at_utc,
            sourceLabel: "pack detail projection",
            verificationLabel: "governed command route",
            verificationTone: drifted ? "restricted" : "verified",
            projectionFamily: "control-plane",
            trustLabel: data.pack?.trust_status ?? (drifted ? "stale projection" : "projected pack detail"),
          }}
        />
        <ReadPlaneDriftBanner drifted={drifted} />
        <ProjectionDriftNotifier active={drifted} dedupeKey="pack-detail-projection-drift" title="Stale projection warning" message="This surface is operating on a stale read-plane snapshot. Governed actions should stay frozen until projections refresh." />
        {receiptId || reviewPacketId ? (
          <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-sm text-zinc-300">
            <span className="font-medium text-zinc-100">Deep link context</span>
            {receiptId ? <Badge>receipt {receiptId}</Badge> : null}
            {reviewPacketId ? <Badge>review packet {reviewPacketId}</Badge> : null}
            <span className="text-xs text-zinc-400">This pack view was opened from a shell lane correlation link. The matching provenance section below is highlighted.</span>
            {receiptId ? (
              <>
                <Button type="button" variant="outline" className="ml-auto h-8 rounded-full border-zinc-700 bg-transparent text-xs" onClick={() => jumpToSection("pack-receipt-context")}>
                  Jump to receipt provenance
                </Button>
                <Link href={`/?receipt=${receiptId}&receiptLane=open#command-receipt-lane`} className="inline-flex">
                  <Button type="button" variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs">
                    Return to receipt lane
                  </Button>
                </Link>
                <Button type="button" variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs" onClick={() => clearDeepLinkContext("receipt")}>
                  Clear receipt context
                </Button>
              </>
            ) : null}
            {reviewPacketId ? (
              <>
                <Button type="button" variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs" onClick={() => jumpToSection("pack-evidence-context")}>
                  Jump to evidence provenance
                </Button>
                <Link href={`/?reviewPacket=${reviewPacketId}&reviewPacketLane=open#review-packet-lane`} className="inline-flex">
                  <Button type="button" variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs">
                    Return to review lane
                  </Button>
                </Link>
                <Button type="button" variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs" onClick={() => clearDeepLinkContext("reviewPacket")}>
                  Clear review context
                </Button>
              </>
            ) : null}
          </div>
        ) : null}

        <div className="grid gap-3 xl:grid-cols-2">
          <div id="pack-receipt-context" className={receiptId ? "rounded-2xl ring-1 ring-sky-500/40 ring-offset-0" : undefined}>
            <ProvenanceStrip
              provenance={{
                generatedAtUtc: command.data?.generated_at_utc ?? data.generated_at_utc,
                sourceLabel: "governed command receipt",
                verificationLabel: command.data ? command.data.execution_mode : "no receipt captured in session",
                verificationTone: command.data?.accepted ? "verified" : "neutral",
                projectionFamily: "control-plane",
                trustLabel: command.data?.accepted ? command.data.action : "receipt lane idle",
              }}
            />
          </div>
          <div id="pack-evidence-context" className={reviewPacketId ? "rounded-2xl ring-1 ring-sky-500/40 ring-offset-0" : undefined}>
            <ProvenanceStrip
              provenance={{
                generatedAtUtc: data.pack?.generated_at_utc ?? data.generated_at_utc,
                sourceLabel: "pack evidence artifacts",
                verificationLabel: (data.pack?.output_artifact_paths?.length ?? 0) > 0 ? "pack artifacts projected" : "no pack artifacts projected",
                verificationTone: (data.pack?.output_artifact_paths?.length ?? 0) > 0 ? "verified" : "restricted",
                projectionFamily: "evidence-backbone",
                trustLabel: `${data.pack?.output_artifact_paths?.length ?? 0} evidence artifacts`,
              }}
            />
          </div>
        </div>

        <PackOperatorGuidance pack={data.pack} detail={data} receipt={command.data} />

        <div className="flex flex-wrap justify-end gap-2">
          <ReviewPacketActions
            packetKind="pack-detail"
            pagePayload={{ packDetail: data, latestReceipt: command.data }}
            provenance={{ pack: data.pack, generatedAtUtc: data.generated_at_utc }}
            notes={[
              "Pack detail exports bundle projected tabs and latest governed command receipt, if present.",
              command.data?.summary_line ?? "No command receipt captured in this session.",
            ]}
          />
          <ExportSnapshotActions payload={{ packDetail: data, latestReceipt: command.data }} fileStem={`strategist-pack-${data.pack?.pack_kind ?? "detail"}-snapshot`} />
        </div>

        <PackDetailPanel
          selected={null}
          pack={data.pack}
          detail={data}
          receipt={command.data}
          onCommand={(action) =>
            command.mutate({
              action,
              payload: {
                operator_id: "JP-K",
                pack_kind: data.pack?.pack_kind,
                manifest_path: data.pack?.manifest_path,
              },
            })
          }
          actionsFrozen={drifted}
        />
      </div>
    </DomainPolicyGate>
  );
}
