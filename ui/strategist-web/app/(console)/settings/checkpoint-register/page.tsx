import Link from "next/link";
import type { Route } from "next";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsCheckpointRegister } from "@/lib/server/diagnostics-checkpoint-register";

export default async function DiagnosticsCheckpointRegisterPage() {
  const payload = await buildFrontendDiagnosticsCheckpointRegister();

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">diagnostics checkpoints</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Checkpoint register</h2>
          <p className="mt-1 max-w-3xl text-sm text-zinc-400">
            Final checkpoint list for deciding whether the local frontend is ready to proceed, should stay under watch,
            or should hold until blockers are cleared.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link href="/api/ui/diagnostics/checkpoint-register" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open checkpoint register JSON</Link>
          <Link href="/settings/readiness-gate" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open readiness gate</Link>
          <Link href="/settings/handoff-packet" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open handoff packet</Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard title="Latest posture" value={payload.latest?.posture ?? 'unknown'} />
        <MetricCard title="Readiness" value={payload.readiness.decision.level} />
        <MetricCard title="Handoff" value={payload.handoff.handoffLabel} />
        <MetricCard title="Blocked checkpoints" value={String(payload.checkpoints.filter((item) => item.status === 'blocked').length)} />
        <MetricCard title="Watch checkpoints" value={String(payload.checkpoints.filter((item) => item.status === 'watch').length)} />
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Checkpoint register</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {payload.checkpoints.map((item) => (
              <div key={item.id} className="rounded-2xl border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-zinc-100">{item.label}</div>
                    <div className="mt-1 text-sm text-zinc-400">{item.detail}</div>
                  </div>
                  <span className="rounded-full border border-zinc-700 px-2 py-1 text-xs text-zinc-300">{item.status}</span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Link href={item.supportingRoute as Route} className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open supporting route</Link>
                </div>
                {item.command ? (
                  <div className="mt-4">
                    <CopyCommandBlock label="Suggested command" description="Use when working this checkpoint." command={item.command} />
                  </div>
                ) : null}
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="space-y-4">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base text-zinc-100">Checkpoint notes</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm text-zinc-300">
              {payload.notes.map((note) => <div key={note}>• {note}</div>)}
            </CardContent>
          </Card>
          <CopyCommandBlock
            label="Checkpoint-before-proceed sequence"
            description="Run this when you want to preserve the current diagnostics state, inspect recommendations, and then move into validation/build only after checkpoints are reviewed."
            command={payload.checkpointBeforeProceedSequence}
          />
        </div>
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
