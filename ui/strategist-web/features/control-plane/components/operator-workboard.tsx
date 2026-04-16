"use client";

import { useMemo, useState } from "react";
import { AlertTriangle, ArrowRightLeft, Clock3, ShieldAlert } from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
  Bar,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import type { UiWorkboardDashboard, WorkItem } from "@/lib/contracts/ui";
import { usePackDetail } from "@/features/control-plane/hooks/use-pack-detail";
import { useOperatorCommand } from "@/features/control-plane/hooks/use-operator-command";
import { PackDetailDrawer } from "@/features/control-plane/components/pack-detail-drawer";
import { useDomainBoundary } from "@/features/shared/domain-boundary-provider";

function StatusPill({ children }: { children: React.ReactNode }) {
  return (
    <span className="rounded-full border border-zinc-700 bg-zinc-900 px-2.5 py-1 text-xs text-zinc-300">
      {children}
    </span>
  );
}

export function OperatorWorkboard({ data, actionsFrozen = false }: { data: UiWorkboardDashboard; actionsFrozen?: boolean }) {
  const queueStats = useMemo(() => {
    const buckets = new Map<string, number>();
    for (const item of data.queue.entries) {
      buckets.set(item.priority_band, (buckets.get(item.priority_band) ?? 0) + 1);
    }
    return Array.from(buckets.entries()).map(([name, value]) => ({ name, value }));
  }, [data.queue.entries]);

  const escalated = data.queue.entries.filter(
    (item) =>
      item.priority_band.toUpperCase().includes("ESCAL") ||
      item.urgency.toUpperCase().includes("HIGH")
  );

  const [selected, setSelected] = useState<WorkItem | null>(data.queue.entries[0] ?? null);
  const selectedPack = useMemo(() => {
    if (!selected) return null;
    const lower = selected.review_target.toLowerCase();
    const item = data.pack_workbench.columns
      .flatMap((column) => column.items)
      .find((candidate) => lower.includes(candidate.pack_kind.replace("_pack", "")) || lower.includes(candidate.pack_kind));
    return item ?? data.pack_workbench.columns.flatMap((column) => column.items)[0] ?? null;
  }, [data.pack_workbench.columns, selected]);
  const packDetail = usePackDetail(selectedPack?.pack_kind, selectedPack?.manifest_path);
  const command = useOperatorCommand();
  const { canPerformAction } = useDomainBoundary();

  const handleCommand = (action: string) => {
    if (!selected) return;
    command.mutate({
      action,
      payload: {
        operator_id: "JP-K",
        work_item_key: selected.work_item_key,
        review_target: selected.review_target,
        pack_kind: selectedPack?.pack_kind,
        manifest_path: selectedPack?.manifest_path,
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Board</CardTitle></CardHeader><CardContent><div className="text-lg font-semibold">{data.board_label}</div><div className="mt-1 text-xs text-zinc-400">{data.queue.summary_line}</div></CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Queue</CardTitle></CardHeader><CardContent><div className="text-lg font-semibold">{data.queue.queue_key}</div><div className="mt-1 text-xs text-zinc-400">{data.queue.queue_summary_line}</div></CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Work Items</CardTitle></CardHeader><CardContent><div className="text-2xl font-semibold">{data.queue.work_item_count}</div><div className="mt-1 text-xs text-zinc-400">projection-backed live count</div></CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Escalations</CardTitle></CardHeader><CardContent><div className="text-2xl font-semibold">{escalated.length}</div><div className="mt-1 text-xs text-zinc-400">high urgency / escalated pack indicators</div></CardContent></Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_1.6fr]">
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base">Queue Pressure by Priority</CardTitle></CardHeader><CardContent className="h-[280px]"><ResponsiveContainer width="100%" height="100%"><BarChart data={queueStats}><CartesianGrid strokeDasharray="3 3" stroke="#27272a" /><XAxis dataKey="name" stroke="#a1a1aa" /><YAxis stroke="#a1a1aa" /><Tooltip /><Bar dataKey="value" radius={[8, 8, 0, 0]} /></BarChart></ResponsiveContainer></CardContent></Card>

        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base">Active Work Queue</CardTitle></CardHeader><CardContent className="space-y-3">{data.queue.entries.map((item) => (
          <div key={item.work_item_key} className={`rounded-2xl border p-4 ${selected?.work_item_key === item.work_item_key ? "border-emerald-500/40 bg-emerald-500/5" : "border-zinc-800 bg-zinc-950/70"}`}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <div className="text-sm font-semibold text-zinc-100">{item.review_target}</div>
                <div className="mt-1 text-sm text-zinc-400">{item.summary_line}</div>
              </div>
              <div className="flex flex-wrap gap-2"><StatusPill>{item.priority_band}</StatusPill><StatusPill>{item.dispatch_posture}</StatusPill><StatusPill>{item.claim_operability}</StatusPill></div>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-zinc-800 p-3"><div className="flex items-center gap-2 text-xs text-zinc-500"><Clock3 className="h-3.5 w-3.5" />Due</div><div className="mt-1 text-sm text-zinc-200">{item.review_due_by_utc}</div></div>
              <div className="rounded-xl border border-zinc-800 p-3"><div className="flex items-center gap-2 text-xs text-zinc-500"><ArrowRightLeft className="h-3.5 w-3.5" />Owner lane</div><div className="mt-1 text-sm text-zinc-200">{item.action_owner_lane}</div></div>
              <div className="rounded-xl border border-zinc-800 p-3"><div className="flex items-center gap-2 text-xs text-zinc-500"><AlertTriangle className="h-3.5 w-3.5" />Urgency</div><div className="mt-1 text-sm text-zinc-200">{item.urgency}</div></div>
              <div className="rounded-xl border border-zinc-800 p-3"><div className="flex items-center gap-2 text-xs text-zinc-500"><ShieldAlert className="h-3.5 w-3.5" />Score</div><div className="mt-1 text-sm text-zinc-200">{item.score}</div></div>
            </div>
            {item.recommended_actions.length > 0 && <div className="mt-4"><div className="mb-2 text-xs uppercase tracking-wide text-zinc-500">Recommended actions</div><ul className="space-y-1 text-sm text-zinc-300">{item.recommended_actions.map((action) => <li key={action}>• {action}</li>)}</ul></div>}
            <div className="mt-4 flex gap-2">
              <Button className="rounded-xl" onClick={() => setSelected(item)}>Open detail</Button>
              <Button variant="outline" className="rounded-xl border-zinc-700 bg-transparent" disabled={actionsFrozen || !canPerformAction("claim-item")} onClick={() => { setSelected(item); handleCommand("claim-item"); }}>Claim item</Button>
              <Button variant="outline" className="rounded-xl border-zinc-700 bg-transparent" disabled={actionsFrozen || !canPerformAction("acknowledge-reentry")} onClick={() => { setSelected(item); handleCommand("acknowledge-reentry"); }}>Acknowledge re-entry</Button>
            </div>
          </div>
        ))}</CardContent></Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base">Pack registry view</CardTitle></CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-3">{data.pack_workbench.columns.map((column) => (
            <div key={column.pack_kind} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
              <div className="text-sm font-semibold text-zinc-100">{column.pack_kind}</div>
              <div className="mt-1 text-xs text-zinc-400">{column.item_count} indexed items</div>
              <div className="mt-3 space-y-2">{column.items.slice(0, 1).map((item) => (
                <button key={item.manifest_path} className="w-full rounded-xl border border-zinc-800 p-3 text-left hover:border-emerald-500/40" onClick={() => setSelected((prev) => prev ?? data.queue.entries[0] ?? null)}>
                  <div className="text-sm text-zinc-200">{item.summary_line ?? item.pack_kind}</div>
                  <div className="mt-1 text-xs text-zinc-500">{item.trust_status ?? "UNKNOWN"}</div>
                </button>
              ))}</div>
            </div>
          ))}</CardContent>
        </Card>

        <PackDetailDrawer
          selected={selected}
          pack={selectedPack}
          detail={packDetail.data}
          receipt={command.data ?? null}
          onCommand={handleCommand}
          actionsFrozen={actionsFrozen || packDetail.isFetching}
        />
      </div>
    </div>
  );
}
