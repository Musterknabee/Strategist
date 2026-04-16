import Link from "next/link";
import type { Route } from "next";

import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsIncidentPlaybook } from "@/lib/server/diagnostics-incident-playbook";

export default async function DiagnosticsIncidentPlaybookPage() {
  const payload = await buildFrontendDiagnosticsIncidentPlaybook();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs uppercase tracking-[0.22em] text-zinc-500">Diagnostics center</div>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics incident playbook</h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Response-oriented playbook for working the local frontend diagnostics trail when posture degrades or warning pressure rises.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Current level" value={payload.currentLevel} />
        <MetricCard title="Latest posture" value={payload.latestPosture} />
        <MetricCard title="Latest mode" value={payload.latestMode} />
        <MetricCard title="Queued actions" value={String(payload.queuedCount)} />
        <MetricCard title="Warning pressure" value={String(payload.warningPressure)} />
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-zinc-400">
        <Link href="/api/ui/diagnostics/incident-playbook" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open incident playbook JSON</Link>
        <Link href="/settings/escalation-matrix" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open escalation matrix</Link>
        <Link href="/settings/action-queue" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open action queue</Link>
        <Link href="/settings/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard</Link>
        <Link href="/settings/status-board" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open status board</Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          {payload.steps.map((step, index) => (
            <div key={step.id} className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">Step {index + 1}</div>
                  <div className="mt-1 text-sm font-semibold text-zinc-100">{step.title}</div>
                </div>
                <Link href={step.route as Route} className="rounded-xl border border-zinc-800 bg-zinc-950 px-3 py-2 text-sm text-zinc-200 hover:bg-zinc-800">Open view</Link>
              </div>
              <div className="mt-3 text-sm text-zinc-400">{step.description}</div>
              {step.command ? (
                <div className="mt-4">
                  <CopyCommandBlock label="Suggested command" description="Copy the recommended local incident-response step." command={step.command} />
                </div>
              ) : null}
            </div>
          ))}
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <div className="text-sm font-semibold text-zinc-100">Playbook notes</div>
            <ul className="mt-3 space-y-2 text-sm text-zinc-400">
              {payload.notes.map((note) => <li key={note}>• {note}</li>)}
            </ul>
          </div>
          <CopyCommandBlock
            label="Escalation-aware maintenance loop"
            description="Use this when you want one copyable sequence that refreshes diagnostics posture before reassessing escalation."
            command="npm run doctor && npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics && npm run recommend:diagnostics && npm run check"
          />
                <Link href="/settings/readiness-gate" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open readiness gate</Link>
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
