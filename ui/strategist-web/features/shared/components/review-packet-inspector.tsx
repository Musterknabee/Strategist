"use client";

import { GitCompareArrows, X } from "lucide-react";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ReviewPacketRecord } from "@/features/shared/review-packets/review-packet-lane-provider";

function topLevelObject(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function buildDiffRows(left: Record<string, unknown>, right: Record<string, unknown>) {
  const keys = Array.from(new Set([...Object.keys(left), ...Object.keys(right)])).sort();
  return keys.map((key) => {
    const leftValue = JSON.stringify(left[key] ?? null);
    const rightValue = JSON.stringify(right[key] ?? null);
    return {
      key,
      changed: leftValue !== rightValue,
      leftValue,
      rightValue,
    };
  });
}

export function ReviewPacketInspector({
  packet,
  packets,
  onClose,
}: {
  packet: ReviewPacketRecord | null;
  packets: ReviewPacketRecord[];
  onClose: () => void;
}) {
  const [comparePacketId, setComparePacketId] = useState<string>("");

  const comparePacket = packets.find((entry) => entry.packet_id === comparePacketId) ?? null;

  const preview = packet?.review_packet ?? {};
  const runtime = preview && typeof preview === "object" && "runtime" in preview ? (preview as Record<string, unknown>).runtime : null;
  const diffRows = useMemo(() => {
    if (!packet || !comparePacket) return [];
    return buildDiffRows(topLevelObject(packet.review_packet), topLevelObject(comparePacket.review_packet));
  }, [packet, comparePacket]);

  if (!packet) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <Card className="max-h-[88vh] w-full max-w-6xl overflow-hidden border-zinc-800 bg-zinc-950 text-zinc-100 shadow-2xl">
        <CardHeader className="border-b border-zinc-800">
          <div className="flex items-start justify-between gap-4">
            <div>
              <CardTitle className="text-base">Review packet inspector</CardTitle>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-zinc-400">
                <Badge>{packet.packet_kind}</Badge>
                <Badge>{packet.file_name}</Badge>
                <Badge>{packet.generated_at_utc}</Badge>
              </div>
            </div>
            <Button variant="ghost" className="h-8 w-8 rounded-full p-0" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="grid max-h-[calc(88vh-5rem)] gap-4 overflow-auto p-4 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-4">
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">
              <div className="text-sm font-medium text-zinc-100">Packet summary</div>
              <div className="mt-2 text-sm text-zinc-300">{packet.summary_line}</div>
              <div className="mt-3 space-y-1 text-xs text-zinc-400">
                <div>notes: {packet.note_count}</div>
                <div>provenance keys: {packet.provenance_keys.length ? packet.provenance_keys.join(", ") : "none"}</div>
              </div>
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">
              <div className="text-sm font-medium text-zinc-100">Operator notes</div>
              {packet.notes?.length ? (
                <ul className="mt-2 space-y-2 text-sm text-zinc-300">
                  {packet.notes.map((note) => (
                    <li key={note}>• {note}</li>
                  ))}
                </ul>
              ) : (
                <div className="mt-2 text-sm text-zinc-500">No operator notes were attached to this packet.</div>
              )}
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">
              <div className="flex items-center justify-between gap-2">
                <div className="text-sm font-medium text-zinc-100">Compare / diff</div>
                <div className="flex items-center gap-2 text-xs text-zinc-400">
                  <GitCompareArrows className="h-3.5 w-3.5" /> compare against recent packet
                </div>
              </div>
              <select
                className="mt-3 w-full rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-100 outline-none"
                value={comparePacketId}
                onChange={(event) => setComparePacketId(event.target.value)}
              >
                <option value="">No comparison selected</option>
                {packets.filter((entry) => entry.packet_id !== packet.packet_id).map((entry) => (
                  <option key={entry.packet_id} value={entry.packet_id}>
                    {entry.packet_kind} · {entry.generated_at_utc}
                  </option>
                ))}
              </select>
              {comparePacket ? (
                <div className="mt-3 space-y-2">
                  <div className="text-xs text-zinc-400">Comparing against {comparePacket.file_name}</div>
                  <div className="max-h-56 space-y-2 overflow-auto">
                    {diffRows.filter((row) => row.changed).length ? diffRows.filter((row) => row.changed).map((row) => (
                      <div key={row.key} className="rounded-xl border border-zinc-800 bg-zinc-950/70 p-3">
                        <div className="text-xs font-medium text-zinc-200">{row.key}</div>
                        <div className="mt-1 grid gap-2 text-[11px] leading-5 text-zinc-400 xl:grid-cols-2">
                          <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded-lg border border-zinc-800 p-2">{row.leftValue}</pre>
                          <pre className="overflow-x-auto whitespace-pre-wrap break-words rounded-lg border border-zinc-800 p-2">{row.rightValue}</pre>
                        </div>
                      </div>
                    )) : <div className="text-sm text-zinc-500">No top-level differences detected between the selected review packets.</div>}
                  </div>
                </div>
              ) : (
                <div className="mt-3 text-sm text-zinc-500">Select another recent review packet to inspect top-level differences.</div>
              )}
            </div>
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">
              <div className="text-sm font-medium text-zinc-100">Runtime snapshot</div>
              <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-zinc-300">{JSON.stringify(runtime, null, 2)}</pre>
            </div>
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900/70 p-4">
            <div className="text-sm font-medium text-zinc-100">Full review packet preview</div>
            <pre className="mt-3 overflow-x-auto whitespace-pre-wrap break-words text-[11px] leading-5 text-zinc-300">{JSON.stringify(preview, null, 2)}</pre>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
