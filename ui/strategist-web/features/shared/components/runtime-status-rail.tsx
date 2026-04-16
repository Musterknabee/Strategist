"use client";

import { useEffect } from "react";
import { Activity, Gavel, RadioTower, Server, UserCog, Zap } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";
import { useCommandReceiptLane } from "@/features/shared/command-receipts/command-receipt-lane-provider";
import { useReviewPacketLane } from "@/features/shared/review-packets/review-packet-lane-provider";
import { useRuntimeStatus } from "@/features/shared/hooks/use-runtime-status";
import { ProjectionDriftNotifier } from "@/features/shared/components/projection-drift-notifier";
import { formatAge, getFreshnessTone, isReadPlaneDrifted } from "@/lib/read-plane";

function toneClass(tone: string) {
  if (tone === "fresh") return "border-emerald-500/30 bg-emerald-500/10 text-emerald-300";
  if (tone === "aging") return "border-amber-500/30 bg-amber-500/10 text-amber-300";
  return "border-rose-500/30 bg-rose-500/10 text-rose-300";
}

export function RuntimeStatusRail() {
  const { operatorRole, setOperatorRole, setPolicy } = useDomainBoundary();
  const {
    receipts,
    inspectedReceiptId,
    isLaneOpen: isReceiptLaneOpen,
    inspectReceipt,
    setLaneOpen: setReceiptLaneOpen,
  } = useCommandReceiptLane();
  const {
    packets,
    inspectedPacketId,
    isLaneOpen: isReviewPacketLaneOpen,
    inspectPacket,
    setLaneOpen: setReviewPacketLaneOpen,
  } = useReviewPacketLane();
  const { data } = useRuntimeStatus();

  useEffect(() => {
    if (!data) return;
    setPolicy(data.policy);
  }, [data, setPolicy]);

  if (!data) return null;

  const freshnessTone = getFreshnessTone(data.generated_at_utc, { aging: 60_000, stale: 5 * 60_000 });
  const drifted = isReadPlaneDrifted(data.generated_at_utc, 5 * 60_000);

  return (
    <>
    <ProjectionDriftNotifier active={drifted} dedupeKey="runtime-read-plane-drift" title="Runtime read-plane drift" message="Shell runtime status is stale. Keep destructive actions frozen until the control surface refreshes." />
    <ProjectionDriftNotifier active={data.backend.status !== "reachable"} dedupeKey="runtime-backend-reachability" title="Backend reachability degraded" message="The UI runtime surface reports degraded backend reachability. Expect missing or stale projections until connectivity recovers." />
    <div className="border-b border-zinc-800 bg-zinc-950/95 px-8 py-3">
      <div className="flex flex-wrap items-center gap-2">
        <Badge className={toneClass(freshnessTone)}><RadioTower className="mr-1 h-3.5 w-3.5" /> Read plane {data.read_plane.freshness_status}</Badge>
        <Badge><Server className="mr-1 h-3.5 w-3.5" /> {data.environment}</Badge>
        <Badge><Activity className="mr-1 h-3.5 w-3.5" /> Backend {data.backend.status}</Badge>
        <Badge className="border-amber-500/30 bg-amber-500/10 text-amber-300"><Gavel className="mr-1 h-3.5 w-3.5" /> Tribunal {data.blindness.tribunal_mode}</Badge>
        <Badge><Zap className="mr-1 h-3.5 w-3.5" /> Providers {data.providers.enabled_count}</Badge>
        <button type="button" onClick={() => { setReceiptLaneOpen(true); if (receipts[0]) inspectReceipt(receipts[0].command_id); document.getElementById("command-receipt-lane")?.scrollIntoView({ behavior: "smooth", block: "start" }); }} className="inline-flex"><Badge className="cursor-pointer hover:border-zinc-600">Receipts {receipts.length}</Badge></button>
        <button type="button" onClick={() => { setReviewPacketLaneOpen(true); if (packets[0]) inspectPacket(packets[0].packet_id); document.getElementById("review-packet-lane")?.scrollIntoView({ behavior: "smooth", block: "start" }); }} className="inline-flex"><Badge className="cursor-pointer hover:border-zinc-600">Review packets {packets.length}</Badge></button>
        {inspectedReceiptId ? (
          <button
            type="button"
            onClick={() => {
              setReceiptLaneOpen(true);
              document.getElementById("command-receipt-lane")?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
            className="inline-flex"
          >
            <Badge className="cursor-pointer border-sky-500/30 bg-sky-500/10 text-sky-300 hover:border-sky-400/40">Focused receipt {inspectedReceiptId.slice(0, 10)}… {isReceiptLaneOpen ? "(lane open)" : "(lane collapsed)"}</Badge>
          </button>
        ) : null}
        {inspectedPacketId ? (
          <button
            type="button"
            onClick={() => {
              setReviewPacketLaneOpen(true);
              document.getElementById("review-packet-lane")?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
            className="inline-flex"
          >
            <Badge className="cursor-pointer border-sky-500/30 bg-sky-500/10 text-sky-300 hover:border-sky-400/40">Focused packet {inspectedPacketId.slice(0, 10)}… {isReviewPacketLaneOpen ? "(lane open)" : "(lane collapsed)"}</Badge>
          </button>
        ) : null}
        <div className="ml-auto flex items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300">
            <UserCog className="h-3.5 w-3.5" />
            <span>Persona</span>
            <select
              className="bg-transparent text-zinc-100 outline-none"
              value={operatorRole}
              onChange={(event) => setOperatorRole(event.target.value as typeof operatorRole)}
            >
              {data.persona.available_roles.map((role) => (
                <option key={role} value={role} className="bg-zinc-950">
                  {role}
                </option>
              ))}
            </select>
          </div>
          {inspectedReceiptId ? (
            <button
              type="button"
              onClick={() => inspectReceipt(null)}
              className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:border-zinc-500"
            >
              Clear receipt focus
            </button>
          ) : null}
          {inspectedPacketId ? (
            <button
              type="button"
              onClick={() => inspectPacket(null)}
              className="rounded-full border border-zinc-700 px-3 py-1 text-xs text-zinc-300 hover:border-zinc-500"
            >
              Clear packet focus
            </button>
          ) : null}
          <span className="text-xs text-zinc-400">Runtime snapshot {formatAge(data.generated_at_utc)}</span>
        </div>
      </div>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-xs text-zinc-400">
        <span>{data.read_plane.operator_message}</span>
        <span>•</span>
        <span>{data.command_bar.operator_hint}</span>
        <span>•</span>
        <span>Allowed domains: {data.policy.allowed_domains.join(", ") || "none"}</span>
        {drifted ? <span className="text-rose-300">Destructive actions should remain frozen until projections refresh.</span> : null}
      </div>
    </div>
    </>
  );
}
