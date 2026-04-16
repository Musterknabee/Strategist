import Link from "next/link";
import type { Route } from "next";

import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsEscalationMatrix } from "@/lib/server/diagnostics-escalation-matrix";

const levelTone: Record<string, string> = {
  monitor: "border-emerald-800/60 bg-emerald-950/30 text-emerald-200",
  stabilize: "border-sky-800/60 bg-sky-950/30 text-sky-200",
  investigate: "border-amber-800/60 bg-amber-950/30 text-amber-200",
  reset: "border-rose-800/60 bg-rose-950/30 text-rose-200",
};

export default async function DiagnosticsEscalationMatrixPage() {
  const payload = await buildFrontendDiagnosticsEscalationMatrix();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs uppercase tracking-[0.22em] text-zinc-500">Diagnostics center</div>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics escalation matrix</h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Escalation-oriented guidance for deciding when to monitor, stabilize, investigate, or reset the local frontend diagnostics trail.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Current level" value={payload.currentLevel} tone={payload.currentLevel} />
        <MetricCard title="Latest posture" value={payload.latestPosture} />
        <MetricCard title="Latest mode" value={payload.latestMode} />
        <MetricCard title="Queued actions" value={String(payload.queuedCount)} />
        <MetricCard title="Warning pressure" value={String(payload.warningPressure)} />
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-zinc-400">
        <Link href="/api/ui/diagnostics/escalation-matrix" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open escalation matrix JSON</Link>
        <Link href="/settings/status-board" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open status board</Link>
        <Link href="/settings/action-queue" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open action queue</Link>
        <Link href="/settings/recommendations" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recommendations</Link>
              <Link href="/settings/incident-playbook" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open incident playbook</Link>
        <Link href="/settings/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard</Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          {payload.rules.map((rule) => {
            const active = rule.level === payload.currentLevel;
            return (
              <div
                key={rule.level}
                className={`rounded-2xl border p-5 ${active ? levelTone[rule.level] : "border-zinc-800 bg-zinc-900 text-zinc-200"}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold">{rule.title}</div>
                    <div className="mt-1 text-sm opacity-80">{rule.trigger}</div>
                  </div>
                  <span className="rounded-full border border-current/30 px-2 py-1 text-xs uppercase tracking-[0.16em]">{rule.level}</span>
                </div>
                <div className="mt-4 text-sm opacity-90">{rule.rationale}</div>
                <div className="mt-4 flex flex-wrap gap-3">
                  <Link href={rule.recommendedRoute as Route} className="rounded-xl border border-current/20 bg-black/10 px-3 py-2 text-sm hover:bg-black/20">Open supporting view</Link>
                </div>
                {rule.recommendedCommand ? (
                  <div className="mt-4">
                    <CopyCommandBlock
                      label="Suggested command"
                      description="Copy and run the recommended escalation response locally."
                      command={rule.recommendedCommand}
                    />
                  </div>
                ) : null}
              </div>
            );
          })}
        </div>
        <div className="space-y-4">
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <div className="text-sm font-semibold text-zinc-100">Escalation notes</div>
            <ul className="mt-3 space-y-2 text-sm text-zinc-400">
              {payload.notes.map((note) => (
                <li key={note}>• {note}</li>
              ))}
            </ul>
          </div>
          <CopyCommandBlock
            label="Stabilize-and-validate"
            description="Copy this recurring loop when escalation is below reset posture and you want to recover trust progressively."
            command="npm run doctor && npm run smoke && npm run export:diagnostics && npm run summarize:diagnostics && npm run recommend:diagnostics && npm run check"
          />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, tone }: { title: string; value: string; tone?: string }) {
  const activeTone = tone ? levelTone[tone] ?? "border-zinc-800 bg-zinc-900 text-zinc-100" : "border-zinc-800 bg-zinc-900 text-zinc-100";
  return (
    <div className={`rounded-2xl border p-4 ${activeTone}`}>
      <div className="text-xs uppercase tracking-[0.18em] opacity-70">{title}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}
