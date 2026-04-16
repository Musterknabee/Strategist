import Link from "next/link";
import type { Route } from "next";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsReadinessGate } from "@/lib/server/diagnostics-readiness-gate";

export default async function DiagnosticsReadinessGatePage() {
  const payload = await buildFrontendDiagnosticsReadinessGate();

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard title="Decision" value={payload.decision.level} />
        <MetricCard title="Latest posture" value={payload.latest?.posture ?? "unknown"} />
        <MetricCard title="Recovery label" value={payload.recovery.readiness.label} />
        <MetricCard title="Blockers" value={String(payload.blockers.length)} />
        <MetricCard title="Warning pressure" value={payload.statusBoard.compare.warningPressure} />
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader><CardTitle className="text-base text-zinc-100">Go / no-go rationale</CardTitle></CardHeader>
        <CardContent className="space-y-3 text-sm text-zinc-300">
          <div>{payload.decision.rationale}</div>
          <CopyCommandBlock label="Proceed sequence" description="Recommended next sequence based on the current diagnostics readiness decision." command={payload.proceedSequence} />
          <div className="flex flex-wrap gap-2">
            <Link href="/api/ui/diagnostics/readiness-gate" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open readiness gate JSON</Link>
            <Link href="/settings/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard</Link>
            <Link href="/settings/decision-log" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open decision log</Link>
            <Link href="/settings/status-board" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open status board</Link>
            <Link href="/settings/incident-playbook" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open incident playbook</Link>
            <Link href="/settings/handoff-packet" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open handoff packet</Link>
            <Link href="/settings/checkpoint-register" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open checkpoint register</Link>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Prerequisites</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {payload.prerequisites.map((item) => (
              <div key={item.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-center justify-between gap-3">
                  <div className="text-sm font-medium text-zinc-100">{item.title}</div>
                  <span className="rounded-full border border-zinc-700 px-2 py-1 text-xs text-zinc-300">{item.status}</span>
                </div>
                <div className="mt-2 text-sm text-zinc-400">{item.detail}</div>
                <div className="mt-3"><Link href={item.route as Route} className="text-sm text-sky-300 hover:text-sky-200">Open supporting route</Link></div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Blockers and notes</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {payload.blockers.length ? payload.blockers.map((item) => (
              <div key={item.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="text-sm font-medium text-zinc-100">{item.title}</div>
                <div className="mt-2 text-sm text-zinc-400">{item.detail}</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Link href={item.route as Route} className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open supporting route</Link>
                  {item.command ? <CopyCommandBlock label="Suggested command" description="Use when clearing this blocker." command={item.command} /> : null}
                </div>
              </div>
            )) : <div className="text-sm text-zinc-400">No active blockers. Continue with the proceed sequence and preserve the latest snapshot for comparison.</div>}
            <div className="space-y-2 text-sm text-zinc-300">
              {payload.notes.map((note) => <div key={note}>• {note}</div>)}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <Card className="border-zinc-800 bg-zinc-900">
      <CardHeader><CardTitle className="text-base text-zinc-100">{title}</CardTitle></CardHeader>
      <CardContent className="text-sm text-zinc-300">{value}</CardContent>
    </Card>
  );
}
