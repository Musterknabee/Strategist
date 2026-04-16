import Link from "next/link";
import type { Route } from "next";

import { buildFrontendDiagnosticsDecisionLog } from "@/lib/server/diagnostics-decision-log";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default async function DiagnosticsDecisionLogPage() {
  const payload = await buildFrontendDiagnosticsDecisionLog();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs uppercase tracking-[0.22em] text-zinc-500">Diagnostics center</div>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics decision log</h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Audit-style summary of recent proceed / conditional / hold / stabilize decisions derived from the readiness gate,
          recovery scorecard, and action-queue posture.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Entries" value={String(payload.summary.totalEntries)} />
        <MetricCard title="Proceed" value={String(payload.summary.proceedEntries)} />
        <MetricCard title="Conditional" value={String(payload.summary.conditionalEntries)} />
        <MetricCard title="Hold" value={String(payload.summary.holdEntries)} />
        <MetricCard title="Stabilize" value={String(payload.summary.stabilizeEntries)} />
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-zinc-400">
        <Link href="/api/ui/diagnostics/decision-log" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open decision log JSON</Link>
        <Link href="/settings/readiness-gate" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open readiness gate</Link>
        <Link href="/settings/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard</Link>
        <Link href="/settings/action-queue" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open action queue</Link>
        <Link href="/settings/handoff-packet" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open handoff packet</Link>
        <Link href="/settings/checkpoint-register" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open checkpoint register</Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          {payload.entries.map((entry) => (
            <div key={entry.id} className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-100">{entry.title}</div>
                  <div className="mt-1 text-sm text-zinc-400">{entry.rationale}</div>
                </div>
                <span className="rounded-full border border-zinc-700 px-2 py-1 text-xs text-zinc-300">{entry.decisionType}</span>
              </div>
              <div className="mt-3 grid gap-3 text-sm text-zinc-400 md:grid-cols-3">
                <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">Timestamp: {entry.timestamp}</div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">Source: {entry.sourceRoute}</div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2">Support: {entry.supportingRoute ?? "n/a"}</div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link href={entry.sourceRoute as Route} className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800">Open source view</Link>
                {entry.supportingRoute ? <Link href={entry.supportingRoute as Route} className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800">Open supporting view</Link> : null}
              </div>
              {entry.command ? <div className="mt-4"><CopyCommandBlock label="Suggested command" description="Copy and run the suggested next-step command locally." command={entry.command} /></div> : null}
            </div>
          ))}
        </div>
        <div className="space-y-4">
          <Card className="border-zinc-800 bg-zinc-900">
            <CardHeader><CardTitle className="text-base text-zinc-100">Decision-log notes</CardTitle></CardHeader>
            <CardContent className="space-y-2 text-sm text-zinc-300">
              {payload.notes.map((note) => <div key={note}>• {note}</div>)}
            </CardContent>
          </Card>
          <CopyCommandBlock
            label="Proceed or hold sequence"
            description="Use this when you want the shortest diagnostics loop that still respects the current proceed/hold posture."
            command={payload.proceedOrHoldSequence}
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
