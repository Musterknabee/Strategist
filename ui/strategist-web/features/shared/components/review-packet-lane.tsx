"use client";

import Link from "next/link";
import type { Route } from "next";
import { Archive, ArrowDownAZ, Eye, Filter, Pin, Search, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ReviewPacketInspector } from "@/features/shared/components/review-packet-inspector";
import { useReviewPacketLane } from "@/features/shared/review-packets/review-packet-lane-provider";
import {
  defaultReviewPacketPreferences,
  filterReviewPackets,
  groupReviewPacketsByKind,
  sortReviewPackets,
  type ReviewPacketSortMode,
} from "@/features/shared/review-packets/review-packet-utils";

const PREFS_KEY = "strategist.review-packet-lane-prefs";

export function ReviewPacketLane() {
  const lane = useReviewPacketLane();
  const {
    packets,
    inspectedPacketId,
    inspectPacket,
    dismissPacket,
    clearPackets,
    togglePinned,
    setLaneOpen,
  } = lane;
  const isLaneOpen = lane.isLaneOpen ?? true;
  const [search, setSearch] = useState(defaultReviewPacketPreferences.search);
  const [packetKind, setPacketKind] = useState(defaultReviewPacketPreferences.packetKind);
  const [sortMode, setSortMode] = useState<ReviewPacketSortMode>(defaultReviewPacketPreferences.sortMode);

  useEffect(() => {
    try {
      const raw = window.localStorage.getItem(PREFS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw) as Partial<typeof defaultReviewPacketPreferences>;
      if (typeof parsed.search === "string") setSearch(parsed.search);
      if (typeof parsed.packetKind === "string") setPacketKind(parsed.packetKind);
      if (parsed.sortMode === "recent" || parsed.sortMode === "kind" || parsed.sortMode === "notes") {
        setSortMode(parsed.sortMode);
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(PREFS_KEY, JSON.stringify({ search, packetKind, sortMode }));
    } catch {
      // ignore persistence errors
    }
  }, [search, packetKind, sortMode]);

  const packetKinds = useMemo(
    () => Array.from(new Set(packets.map((packet) => packet.packet_kind))).sort(),
    [packets],
  );
  const filteredPackets = useMemo(
    () => sortReviewPackets(filterReviewPackets(packets, search, packetKind), sortMode),
    [packets, search, packetKind, sortMode],
  );
  const groupedPackets = useMemo(() => groupReviewPacketsByKind(filteredPackets), [filteredPackets]);

  if (!packets.length) {
    return null;
  }

  const inspectedPacket = packets.find((packet) => packet.packet_id === inspectedPacketId) ?? null;

  return (
    <>
      <div id="review-packet-lane" className="mb-6 rounded-2xl border border-zinc-800 bg-zinc-900/80 p-4 scroll-mt-32">
        <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="text-sm font-medium text-zinc-100">Recent review packets</div>
            <div className="text-xs text-zinc-400">Downloaded handoff artifacts with provenance, runtime context, compare support, and pinning.</div>
          </div>
          <div className="flex items-center gap-2">
            <Badge>{filteredPackets.length}/{packets.length} visible</Badge>
            <Button variant="outline" className="border-zinc-700 bg-transparent text-xs" onClick={() => setLaneOpen(!isLaneOpen)}>{isLaneOpen ? "Collapse" : "Expand"}</Button>
            <Button variant="outline" className="border-zinc-700 bg-transparent text-xs" onClick={clearPackets}>
              Clear lane
            </Button>
          </div>
        </div>

        {isLaneOpen ? (
        <>
<div className="mb-4 grid gap-3 xl:grid-cols-[1.2fr_1fr_0.9fr]">
          <label className="flex items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/70 px-3 py-2 text-sm text-zinc-300">
            <Search className="h-4 w-4 text-zinc-500" />
            <input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search packet kind, file, summary, provenance, notes"
              className="w-full bg-transparent outline-none placeholder:text-zinc-500"
            />
          </label>
          <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/70 px-3 py-2">
            <div className="inline-flex items-center gap-2 text-xs uppercase tracking-wide text-zinc-500">
              <Filter className="h-3.5 w-3.5" /> packet kind
            </div>
            <Button type="button" variant={packetKind === "all" ? "default" : "outline"} className={packetKind === "all" ? "h-8 rounded-full" : "h-8 rounded-full border-zinc-700 bg-transparent"} onClick={() => setPacketKind("all")}>All</Button>
            {packetKinds.map((kind) => (
              <Button key={kind} type="button" variant={packetKind === kind ? "default" : "outline"} className={packetKind === kind ? "h-8 rounded-full" : "h-8 rounded-full border-zinc-700 bg-transparent"} onClick={() => setPacketKind(kind)}>
                {kind}
              </Button>
            ))}
          </div>
          <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-zinc-800 bg-zinc-950/70 px-3 py-2">
            <div className="inline-flex items-center gap-2 text-xs uppercase tracking-wide text-zinc-500">
              <ArrowDownAZ className="h-3.5 w-3.5" /> sort
            </div>
            {(["recent", "kind", "notes"] as const).map((mode) => (
              <Button key={mode} type="button" variant={sortMode === mode ? "default" : "outline"} className={sortMode === mode ? "h-8 rounded-full" : "h-8 rounded-full border-zinc-700 bg-transparent"} onClick={() => setSortMode(mode)}>
                {mode}
              </Button>
            ))}
          </div>
        </div>

        <div className="space-y-4">
          {groupedPackets.length ? groupedPackets.map((group) => (
            <div key={group.packetKind} className="space-y-3">
              <div className="flex items-center justify-between gap-3">
                <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">{group.packetKind}</div>
                <Badge>{group.items.length} packet{group.items.length === 1 ? "" : "s"}</Badge>
              </div>
              <div className="space-y-3">
                {group.items.map((packet) => (
                  <div key={packet.packet_id} className="flex flex-wrap items-start justify-between gap-3 rounded-2xl border border-zinc-800 bg-zinc-950/70 p-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <div className="inline-flex items-center gap-2 text-sm font-medium text-zinc-100">
                          <Archive className="h-4 w-4 text-emerald-300" />
                          {packet.packet_kind}
                        </div>
                        <Badge>{packet.file_name}</Badge>
                        <Badge>{packet.generated_at_utc}</Badge>
                        {packet.pinned ? <Badge className="border-amber-500/30 bg-amber-500/10 text-amber-300">Pinned</Badge> : null}
                      </div>
                      <div className="mt-2 text-sm text-zinc-300">{packet.summary_line}</div>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-400">
                        <span>notes: {packet.note_count}</span>
                        <span>provenance: {packet.provenance_keys.length ? packet.provenance_keys.join(", ") : "none"}</span>
                        {packet.related_pack_kind ? <span>pack: {packet.related_pack_kind}</span> : null}
                        {packet.related_review_target ? <span>target: {packet.related_review_target}</span> : null}
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-1">
                      {packet.related_pack_kind ? (
                        <Button asChild variant="ghost" className="h-8 rounded-full px-3 text-xs text-zinc-300 hover:text-zinc-100">
                          <Link href={`/packs/${encodeURIComponent(packet.related_pack_kind)}?reviewPacket=${encodeURIComponent(packet.packet_id)}&reviewPacketLane=open` as Route}>Open pack</Link>
                        </Button>
                      ) : null}
                      <Button variant="ghost" className="h-8 rounded-full px-3 text-xs text-zinc-300 hover:text-zinc-100" onClick={() => togglePinned(packet.packet_id)}>
                        <Pin className="mr-1 h-4 w-4" /> {packet.pinned ? "Unpin" : "Pin"}
                      </Button>
                      <Button variant="ghost" className="h-8 rounded-full px-3 text-xs text-zinc-300 hover:text-zinc-100" onClick={() => inspectPacket(packet.packet_id)}>
                        <Eye className="mr-1 h-4 w-4" /> Inspect
                      </Button>
                      <Button variant="ghost" className="h-8 w-8 rounded-full p-0 text-zinc-400 hover:text-zinc-100" onClick={() => dismissPacket(packet.packet_id)}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )) : (
            <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/50 p-6 text-sm text-zinc-500">
              No review packets match the current search/filter state.
            </div>
          )}
        </div>
        </>
      ) : (
        <div className="rounded-2xl border border-dashed border-zinc-800 bg-zinc-950/50 p-4 text-sm text-zinc-500">
          Lane collapsed. Expand it to inspect exported review packets, compare handoffs, and follow pack links.
        </div>
      )}
      </div>
      <ReviewPacketInspector packet={inspectedPacket} packets={filteredPackets.length ? filteredPackets : packets} onClose={() => inspectPacket(null)} />
    </>
  );
}
