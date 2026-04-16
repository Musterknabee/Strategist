"use client";

import type { Route } from "next";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useCommandReceiptLane } from "@/features/shared/command-receipts/command-receipt-lane-provider";
import { useReviewPacketLane } from "@/features/shared/review-packets/review-packet-lane-provider";

function jumpToLane(anchorId: string) {
  document.getElementById(anchorId)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

export function DeepLinkContextPills({ title = "Shared context" }: { title?: string }) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const { setLaneOpen: setReceiptLaneOpen, inspectReceipt } = useCommandReceiptLane();
  const { setLaneOpen: setReviewLaneOpen, inspectPacket } = useReviewPacketLane();

  const receiptId = searchParams.get("receipt");
  const reviewPacketId = searchParams.get("reviewPacket");

  if (!receiptId && !reviewPacketId) return null;

  const clearParam = (key: "receipt" | "reviewPacket") => {
    const next = new URLSearchParams(searchParams.toString());
    next.delete(key);
    const query = next.toString();
    const nextRoute = (query ? `${pathname}?${query}` : pathname) as Route;
    router.replace(nextRoute);
  };

  return (
    <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-sm text-zinc-300">
      <span className="font-medium text-zinc-100">{title}</span>
      {receiptId ? <Badge>receipt {receiptId}</Badge> : null}
      {reviewPacketId ? <Badge>review packet {reviewPacketId}</Badge> : null}
      <span className="text-xs text-zinc-400">This route was opened with shell deep-link context. You can jump back to the originating lane or clear the context here.</span>
      {receiptId ? (
        <>
          <Button
            type="button"
            variant="outline"
            className="h-8 rounded-full border-zinc-700 bg-transparent text-xs"
            onClick={() => {
              setReceiptLaneOpen(true);
              inspectReceipt(receiptId);
              jumpToLane("command-receipt-lane");
            }}
          >
            Open receipt lane
          </Button>
          <Button
            type="button"
            variant="outline"
            className="h-8 rounded-full border-zinc-700 bg-transparent text-xs"
            onClick={() => clearParam("receipt")}
          >
            Clear receipt context
          </Button>
        </>
      ) : null}
      {reviewPacketId ? (
        <>
          <Button
            type="button"
            variant="outline"
            className="h-8 rounded-full border-zinc-700 bg-transparent text-xs"
            onClick={() => {
              setReviewLaneOpen(true);
              inspectPacket(reviewPacketId);
              jumpToLane("review-packet-lane");
            }}
          >
            Open review lane
          </Button>
          <Button
            type="button"
            variant="outline"
            className="h-8 rounded-full border-zinc-700 bg-transparent text-xs"
            onClick={() => clearParam("reviewPacket")}
          >
            Clear review context
          </Button>
        </>
      ) : null}
    </div>
  );
}
