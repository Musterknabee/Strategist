import Link from "next/link";
import type { Route } from "next";

import { buildFrontendDiagnosticsActionQueue } from "@/lib/server/diagnostics-action-queue";
import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";

export default async function DiagnosticsActionQueuePage() {
  const payload = await buildFrontendDiagnosticsActionQueue();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs uppercase tracking-[0.22em] text-zinc-500">Diagnostics center</div>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics action queue</h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Prioritized next moves derived from the latest diagnostics posture, aggregate pressure, and recommendation set.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Queued" value={String(payload.summary.queued)} />
        <MetricCard title="Watch" value={String(payload.summary.watch)} />
        <MetricCard title="Later" value={String(payload.summary.later)} />
        <MetricCard title="Latest posture" value={payload.summary.latestPosture} />
        <MetricCard title="Latest mode" value={payload.summary.latestMode} />
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-zinc-400">
        <Link href="/api/ui/diagnostics/action-queue" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open action queue JSON</Link>
        <Link href="/settings/recommendations" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recommendations</Link>
        <Link href="/settings/status-board" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open status board</Link>
        <Link href="/settings/escalation-matrix" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open escalation matrix</Link>
        <Link href="/settings/incident-playbook" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open incident playbook</Link>
        <Link href="/settings/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard</Link>
        <Link href="/settings/decision-log" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open decision log</Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.3fr_0.9fr]">
        <div className="space-y-4">
          {payload.items.map((item) => (
            <div key={item.id} className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold text-zinc-100">{item.title}</div>
                  <div className="mt-1 text-sm text-zinc-400">{item.rationale}</div>
                </div>
                <div className="flex gap-2 text-xs">
                  <span className="rounded-full border border-zinc-700 px-2 py-1 text-zinc-300">{item.priority}</span>
                  <span className="rounded-full border border-zinc-700 px-2 py-1 text-zinc-300">{item.status}</span>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                {item.suggestedRoute ? (
                  <Link href={item.suggestedRoute as Route} className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800">Open supporting view</Link>
                ) : null}
              </div>
              {item.command ? (
                <div className="mt-4">
                  <CopyCommandBlock label="Suggested command" command={item.command} description="Copy and run the recommended next-step command locally." />
                </div>
              ) : null}
            </div>
          ))}
          {!payload.items.length ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5 text-sm text-zinc-400">No diagnostics actions are queued right now.</div>
          ) : null}
        </div>
        <div className="space-y-4">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <div className="text-sm font-semibold text-zinc-100">Action-queue notes</div>
            <ul className="mt-3 space-y-2 text-sm text-zinc-400">
              {payload.notes.map((note) => (
                <li key={note}>• {note}</li>
              ))}
            </ul>
          </div>
          <CopyCommandBlock
            label="Stabilize and validate"
            command="npm run doctor && npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics && npm run check && npm run build"
            description="Recommended recurring sequence when queued diagnostics actions are low and you want a fuller signal."
          />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-4">
      <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">{title}</div>
      <div className="mt-2 text-xl font-semibold text-zinc-100">{value}</div>
    </div>
  );
}
