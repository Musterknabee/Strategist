"use client";

import Link from "next/link";
import type { Route } from "next";
import { CheckCircle2, Eye, Filter, GitBranch, RefreshCcw, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { deriveReceiptCorrelationHint } from "@/features/control-plane/receipt-correlation";
import { useCommandReceiptLane } from "@/features/shared/command-receipts/command-receipt-lane-provider";
import {
  defaultReceiptPreferences,
  filterCommandReceipts,
  groupCommandReceiptsByStatus,
  receiptStatusLabel,
  sortCommandReceipts,
  type ReceiptFilterMode,
  type ReceiptSortMode,
} from "@/features/shared/command-receipts/receipt-lane-utils";
import { useReviewPacketLane } from "@/features/shared/review-packets/review-packet-lane-provider";

const PREFS_KEY = "strategist.command-receipt-lane-prefs";

export function CommandReceiptLane() {
  const lane = useCommandReceiptLane();
  const {
    receipts,
    inspectedReceiptId,
    dismissReceipt,
    clearReceipts,
    inspectReceipt,
    setLaneOpen,
  } = lane;
  const isLaneOpen = lane.isLaneOpen ?? true;
  const { packets, inspectPacket } = useReviewPacketLane();
  const [search, setSearch] = useState(defaultReceiptPreferences.search);
  const [filterMode, setFilterMode] = useState<ReceiptFilterMode>(defaultReceiptPreferences.filterMode);
  const [sortMode, setSortMode] = useState<ReceiptSortMode>(defaultReceiptPreferences.sortMode);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(PREFS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<typeof defaultReceiptPreferences>;
      if (typeof parsed.search === "string") setSearch(parsed.search);
      if (parsed.filterMode === "all" || parsed.filterMode === "awaiting-refresh" || parsed.filterMode === "accepted" || parsed.filterMode === "attention") {
        setFilterMode(parsed.filterMode);
      }
      if (parsed.sortMode === "recent" || parsed.sortMode === "action" || parsed.sortMode === "status") {
        setSortMode(parsed.sortMode);
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(PREFS_KEY, JSON.stringify({ search, filterMode, sortMode }));
    } catch {
      // ignore persistence errors
    }
  }, [search, filterMode, sortMode]);

  const filteredReceipts = useMemo(
    () => sortCommandReceipts(filterCommandReceipts(receipts, search, filterMode), sortMode),
    [receipts, search, filterMode, sortMode],
  );
  const groups = useMemo(() => groupCommandReceiptsByStatus(filteredReceipts), [filteredReceipts]);

  if (!receipts.length) {
    return null;
  }

  return (
    <div id="command-receipt-lane" className="mb-4 space-y-3 scroll-mt-32">
      <div className="flex items-center justify-between px-1">
        <div>
          <div className="text-sm font-medium text-zinc-100">Governed command lane</div>
          <div className="text-xs text-zinc-400">Recent command receipts are advisory until the projection plane refreshes.</div>
        </div>
        <div className="flex items-center gap-2">
          <Badge>{filteredReceipts.length}/{receipts.length} visible</Badge>
          <Button variant="outline" className="rounded-xl border-zinc-700 bg-transparent text-xs" onClick={() => setLaneOpen(!isLaneOpen)}>{isLaneOpen ? "Collapse" : "Expand"}</Button>
          <Button variant="ghost" className="rounded-xl text-xs" onClick={clearReceipts}>
            Clear receipts
          </Button>
        </div>
      </div>

      {isLaneOpen ? (
      <>
<div className="grid gap-3 xl:grid-cols-[1.2fr_1fr_0.9fr]">
        <label className="flex items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/70 px-3 py-2 text-sm text-zinc-300">
          <Search className="h-4 w-4 text-zinc-500" />
          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search action, execution mode, summary, operator message"
            className="w-full bg-transparent outline-none placeholder:text-zinc-500"
          />
        </label>
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/70 px-3 py-2">
          <div className="inline-flex items-center gap-2 text-xs uppercase tracking-wide text-zinc-500">
            <Filter className="h-3.5 w-3.5" /> status
          </div>
          {(["all", "awaiting-refresh", "accepted", "attention"] as const).map((mode) => (
            <Button
              key={mode}
              type="button"
              variant={filterMode === mode ? "default" : "outline"}
              className={filterMode === mode ? "h-8 rounded-full" : "h-8 rounded-full border-zinc-700 bg-transparent"}
              onClick={() => setFilterMode(mode)}
            >
              {mode}
            </Button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/70 px-3 py-2">
          <div className="inline-flex items-center gap-2 text-xs uppercase tracking-wide text-zinc-500">sort</div>
          {(["recent", "action", "status"] as const).map((mode) => (
            <Button
              key={mode}
              type="button"
              variant={sortMode === mode ? "default" : "outline"}
              className={sortMode === mode ? "h-8 rounded-full" : "h-8 rounded-full border-zinc-700 bg-transparent"}
              onClick={() => setSortMode(mode)}
            >
              {mode}
            </Button>
          ))}
        </div>
      </div>

      {groups.length ? (
        <div className="space-y-3">
          {groups.map((group) => (
            <div key={group.status} className="space-y-3">
              <div className="flex items-center justify-between px-1">
                <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">{group.status}</div>
                <Badge>{group.items.length} receipt{group.items.length === 1 ? "" : "s"}</Badge>
              </div>
              <div className="grid gap-3 xl:grid-cols-2">
                {group.items.map((receipt) => {
                  const correlation = deriveReceiptCorrelationHint(receipt);
                  const statusLabel = receiptStatusLabel(receipt);
                  const relatedPacket = packets.find((packet) => {
                    const packKind = receipt.target?.pack_kind ?? null;
                    const workItemKey = receipt.target?.work_item_key ?? null;
                    return (
                      (!!packKind && packet.related_pack_kind === packKind) ||
                      (!!workItemKey && packet.related_work_item_key === workItemKey)
                    );
                  });
                  const isFocused = receipt.command_id === inspectedReceiptId;
                  return (
                    <div key={receipt.command_id} className="space-y-2">
                      <div className={isFocused ? "rounded-2xl border border-sky-500/40 bg-sky-500/10 p-4" : "rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-4"}>
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex gap-3">
                            <div className="mt-0.5 rounded-full bg-emerald-500/15 p-1.5 text-emerald-300">
                              <CheckCircle2 className="h-4 w-4" />
                            </div>
                            <div>
                              <div className="text-sm font-medium text-zinc-100">{receipt.summary_line}</div>
                              <div className="mt-1 text-sm text-zinc-300">{receipt.operator_message}</div>
                              <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-400">
                                <span className="rounded-full border border-zinc-700 px-2 py-1">{receipt.action}</span>
                                <span className="rounded-full border border-zinc-700 px-2 py-1">{receipt.execution_mode}</span>
                                <span className="rounded-full border border-zinc-700 px-2 py-1">{statusLabel}</span>
                                {receipt.requires_projection_refresh ? (
                                  <span className="inline-flex items-center gap-1 rounded-full border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-amber-300">
                                    <RefreshCcw className="h-3 w-3" />
                                    awaiting projection refresh
                                  </span>
                                ) : null}
                              </div>
                              {correlation ? (
                                <div className="mt-3 inline-flex items-start gap-2 rounded-2xl border border-zinc-700/80 bg-zinc-950/60 px-3 py-2 text-xs text-zinc-300">
                                  <GitBranch className="mt-0.5 h-3.5 w-3.5 text-zinc-400" />
                                  <span>{correlation.summary}</span>
                                </div>
                              ) : null}
                            </div>
                          </div>
                          <Button variant="ghost" className="h-8 w-8 rounded-full p-0" onClick={() => dismissReceipt(receipt.command_id)} aria-label="Dismiss receipt">
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2 px-1">
                        <Button variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs" onClick={() => inspectReceipt(isFocused ? null : receipt.command_id)}><Eye className="mr-1 h-3.5 w-3.5" /> {isFocused ? "Clear focus" : "Focus receipt"}</Button>
                        {receipt.target?.pack_kind ? (
                          <Button asChild variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs">
                            <Link href={`/packs/${encodeURIComponent(receipt.target.pack_kind)}?receipt=${encodeURIComponent(receipt.command_id)}&receiptLane=open` as Route}>Open related pack</Link>
                          </Button>
                        ) : null}
                        {relatedPacket ? (
                          <Button variant="outline" className="h-8 rounded-full border-zinc-700 bg-transparent text-xs" onClick={() => inspectPacket(relatedPacket.packet_id)}>
                            <Eye className="mr-1 h-3.5 w-3.5" /> Inspect related review packet
                          </Button>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/50 p-6 text-sm text-zinc-500">
          No receipts match the current search/filter state.
        </div>
      )}
      </>
      ) : (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/50 p-4 text-sm text-zinc-500">
          Lane collapsed. Expand it to inspect governed command receipts and projection-refresh posture.
        </div>
      )}
    </div>
  );
}
