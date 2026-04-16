import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsHandoffPacket } from "@/lib/server/diagnostics-handoff-packet";

export default async function DiagnosticsHandoffPacketPage() {
  const packet = await buildFrontendDiagnosticsHandoffPacket();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">diagnostics handoff</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Frontend handoff packet</h2>
          <p className="mt-1 text-sm text-zinc-400">Aggregated proceed / stabilize / hold packet derived from the latest diagnostics state, summary pressure, readiness gate, and decision log.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/handoff-packet" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open handoff packet JSON</Link>
          <Link href="/settings/decision-log" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open decision log</Link>
          <Link href="/settings/readiness-gate" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open readiness gate</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Packet id</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{packet.packetId}</CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Handoff label</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{packet.handoffLabel}</CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Latest posture</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{packet.latest?.posture ?? "unknown"}</CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Readiness</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{packet.readiness.decision.level}</CardContent></Card>
        <Card className="border-zinc-800 bg-zinc-900"><CardHeader><CardTitle className="text-base text-zinc-100">Decision entries</CardTitle></CardHeader><CardContent className="text-sm text-zinc-300">{packet.decisionLog.summary.totalEntries}</CardContent></Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Handoff notes</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm text-zinc-300">
            {packet.notes.map((note) => <div key={note}>• {note}</div>)}
            <div className="grid gap-3 md:grid-cols-2">
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Summary posture</div>
                <div className="mt-2 text-sm text-zinc-200">Latest summary posture: {packet.summary.latestPosture ?? "unknown"}</div>
                <div className="text-sm text-zinc-400">Warning pressure: {packet.compare.warningPressure}</div>
              </div>
              <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4">
                <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Decision mix</div>
                <div className="mt-2 text-sm text-zinc-200">Proceed: {packet.decisionLog.summary.proceedEntries}</div>
                <div className="text-sm text-zinc-400">Hold/Stabilize: {packet.decisionLog.summary.holdEntries + packet.decisionLog.summary.stabilizeEntries}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Proceed or hold sequence</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <CopyCommandBlock
              label="Suggested handoff sequence"
              description="Use this block when you want to preserve the current diagnostics posture and then either proceed or continue stabilizing based on the latest decision state."
              command={packet.proceedOrHoldSequence}
            />
            <div className="flex flex-wrap gap-2">
              <Link href="/settings/status-board" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open status board</Link>
              <Link href="/settings/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard</Link>
              <Link href="/settings/recommendations" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recommendations</Link>
              <Link href="/settings/checkpoint-register" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open checkpoint register</Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
