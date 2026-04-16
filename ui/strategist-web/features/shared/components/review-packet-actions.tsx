"use client";

import { useMemo, useState } from "react";
import { Archive, Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useRuntimeStatus } from "@/features/shared/hooks/use-runtime-status";
import { useReviewPacketLane } from "@/features/shared/review-packets/review-packet-lane-provider";

type ReviewPacketActionsProps = {
  packetKind: string;
  pagePayload: unknown;
  provenance?: Record<string, unknown>;
  notes?: string[];
};

function inferRelatedLinkage(pagePayload: unknown): {
  related_pack_kind?: string | null;
  related_work_item_key?: string | null;
  related_review_target?: string | null;
} {
  if (!pagePayload || typeof pagePayload !== "object") {
    return {};
  }
  const payload = pagePayload as Record<string, unknown>;
  const packDetail = payload.packDetail as Record<string, unknown> | undefined;
  const latestReceipt = payload.latestReceipt as Record<string, unknown> | undefined;
  const pack = packDetail?.pack as Record<string, unknown> | undefined;
  const target = latestReceipt?.target as Record<string, unknown> | undefined;

  return {
    related_pack_kind:
      (typeof pack?.pack_kind === "string" ? pack.pack_kind : null) ??
      (typeof target?.pack_kind === "string" ? target.pack_kind : null),
    related_work_item_key: typeof target?.work_item_key === "string" ? target.work_item_key : null,
    related_review_target:
      (typeof target?.review_target === "string" ? target.review_target : null) ??
      (typeof payload.review_target === "string" ? payload.review_target : null),
  };
}

export function ReviewPacketActions({
  packetKind,
  pagePayload,
  provenance,
  notes = [],
}: ReviewPacketActionsProps) {
  const [saved, setSaved] = useState(false);
  const runtimeQuery = useRuntimeStatus();
  const { pushPacket } = useReviewPacketLane();

  const linkage = useMemo(() => inferRelatedLinkage(pagePayload), [pagePayload]);

  const reviewPacket = useMemo(
    () => ({
      schema_version: "ui_review_packet/v1",
      generated_at_utc: new Date().toISOString(),
      packet_kind: packetKind,
      runtime: runtimeQuery.data ?? null,
      provenance: provenance ?? null,
      notes,
      page_payload: pagePayload,
      linkage,
    }),
    [packetKind, pagePayload, provenance, notes, linkage, runtimeQuery.data],
  );

  const fileName = `strategist-${packetKind}-review-packet.json`;

  const onDownload = () => {
    const blob = new Blob([JSON.stringify(reviewPacket, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = fileName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(url);
    pushPacket({
      packet_id: `${packetKind}-${reviewPacket.generated_at_utc}`,
      packet_kind: packetKind,
      generated_at_utc: reviewPacket.generated_at_utc,
      file_name: fileName,
      note_count: notes.length,
      provenance_keys: provenance ? Object.keys(provenance) : [],
      summary_line: `Exported review packet with runtime ${runtimeQuery.data ? "attached" : "missing"} and ${notes.length} operator note${notes.length === 1 ? "" : "s"}.`,
      notes,
      review_packet: reviewPacket as Record<string, unknown>,
      related_pack_kind: linkage.related_pack_kind ?? null,
      related_work_item_key: linkage.related_work_item_key ?? null,
      related_review_target: linkage.related_review_target ?? null,
    });
    setSaved(true);
    window.setTimeout(() => setSaved(false), 1800);
  };

  return (
    <Button variant="outline" className="gap-2" onClick={onDownload}>
      {saved ? <Check className="h-4 w-4" /> : <Archive className="h-4 w-4" />}
      {saved ? "Review packet downloaded" : "Export review packet"}
    </Button>
  );
}
