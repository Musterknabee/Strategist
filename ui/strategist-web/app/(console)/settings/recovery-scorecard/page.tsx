import Link from "next/link";
import type { Route } from "next";

import { CopyCommandBlock } from "@/features/shared/components/copy-command-block";
import { buildFrontendDiagnosticsRecoveryScorecard } from "@/lib/server/diagnostics-recovery-scorecard";

const tone: Record<string, string> = {
  ready: "border-emerald-800/60 bg-emerald-950/30 text-emerald-200",
  stabilizing: "border-sky-800/60 bg-sky-950/30 text-sky-200",
  blocked: "border-rose-800/60 bg-rose-950/30 text-rose-200",
  pass: "border-emerald-800/60 bg-emerald-950/20 text-emerald-200",
  watch: "border-amber-800/60 bg-amber-950/20 text-amber-200",
  fail: "border-rose-800/60 bg-rose-950/20 text-rose-200",
};

export default async function DiagnosticsRecoveryScorecardPage() {
  const payload = await buildFrontendDiagnosticsRecoveryScorecard();

  return (
    <div className="space-y-6">
      <div>
        <div className="text-xs uppercase tracking-[0.22em] text-zinc-500">Diagnostics center</div>
        <h1 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics recovery scorecard</h1>
        <p className="mt-2 max-w-3xl text-sm text-zinc-400">
          Recovery-oriented scorecard for deciding whether the local frontend shell is ready, still stabilizing, or blocked before a fuller validation pass.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <MetricCard title="Recovery label" value={payload.readiness.label} tone={payload.readiness.label} />
        <MetricCard title="Recovery score" value={`${payload.readiness.score}/${payload.readiness.maxScore}`} />
        <MetricCard title="Latest posture" value={payload.latest?.posture ?? "none"} />
        <MetricCard title="Queued actions" value={String(payload.queue.summary.queued)} />
        <MetricCard title="Escalation level" value={payload.escalation.currentLevel} />
      </div>

      <div className="flex flex-wrap gap-3 text-sm text-zinc-400">
        <Link href="/api/ui/diagnostics/recovery-scorecard" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open recovery scorecard JSON</Link>
        <Link href="/settings/incident-playbook" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open incident playbook</Link>
        <Link href="/settings/escalation-matrix" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open escalation matrix</Link>
        <Link href="/settings/action-queue" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open action queue</Link>
        <Link href="/settings/readiness-gate" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open readiness gate</Link>
        <Link href="/settings/decision-log" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open decision log</Link>
        <Link href="/settings/handoff-packet" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open handoff packet</Link>
        <Link href="/settings/checkpoint-register" className="rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-zinc-200 hover:bg-zinc-800">Open checkpoint register</Link>
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="space-y-4">
          {payload.checks.map((check) => (
            <div key={check.id} className={`rounded-2xl border p-5 ${tone[check.status]}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-semibold">{check.title}</div>
                  <div className="mt-1 text-sm opacity-85">{check.detail}</div>
                </div>
                <span className="rounded-full border border-current/30 px-2 py-1 text-xs uppercase tracking-[0.16em]">{check.status}</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <Link href={check.route as Route} className="rounded-xl border border-current/20 bg-black/10 px-3 py-2 text-sm hover:bg-black/20">Open supporting view</Link>
              </div>
              {check.command ? (
                <div className="mt-4">
                  <CopyCommandBlock label="Suggested command" description="Copy the local recovery step associated with this scorecard check." command={check.command} />
                </div>
              ) : null}
            </div>
          ))}
        </div>
        <div className="space-y-4">
          <div className={`rounded-2xl border p-5 ${tone[payload.readiness.label]}`}>
            <div className="text-sm font-semibold">Recovery posture</div>
            <div className="mt-2 text-sm opacity-90">
              {payload.readiness.label === "ready"
                ? "The shell looks ready to move into the full validation sequence."
                : payload.readiness.label === "stabilizing"
                  ? "The shell is partially stabilized. Clear the remaining watch/fail checks before trusting the console fully."
                  : "The shell is blocked. Use the incident playbook and escalation matrix before continuing."}
            </div>
          </div>
          <div className="rounded-2xl border border-zinc-800 bg-zinc-900 p-5">
            <div className="text-sm font-semibold text-zinc-100">Recovery notes</div>
            <ul className="mt-3 space-y-2 text-sm text-zinc-400">
              {payload.notes.map((note) => <li key={note}>• {note}</li>)}
            </ul>
          </div>
          <CopyCommandBlock
            label="Stabilize and validate"
            description="Copy this when you want one recovery-oriented sequence before a fuller build/test pass."
            command={payload.stabilizeAndValidate}
          />
        </div>
      </div>
    </div>
  );
}

function MetricCard({ title, value, tone: toneKey }: { title: string; value: string; tone?: string }) {
  const activeTone = toneKey ? tone[toneKey] ?? "border-zinc-800 bg-zinc-900 text-zinc-100" : "border-zinc-800 bg-zinc-900 text-zinc-100";
  return (
    <div className={`rounded-2xl border p-4 ${activeTone}`}>
      <div className="text-xs uppercase tracking-[0.18em] opacity-70">{title}</div>
      <div className="mt-2 text-xl font-semibold">{value}</div>
    </div>
  );
}
