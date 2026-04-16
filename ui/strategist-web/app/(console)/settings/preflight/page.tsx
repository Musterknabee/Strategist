import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { runFrontendPreflight } from "@/lib/server/preflight";

export default async function RuntimePreflightPage() {
  const report = await runFrontendPreflight();
  const modeLabel = report.runtime.forceMocks ? "Mock-backed" : report.runtime.backendBaseUrl ? "Backend-connected" : "Backend required";
  const modeTone = report.runtime.forceMocks
    ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
    : report.runtime.backendBaseUrl
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : "border-rose-500/30 bg-rose-500/10 text-rose-300";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-100">Frontend preflight</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Quick probe of the web shell BFF, runtime posture, and a few representative projection payloads before a full local build/test pass.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Backend mode</CardTitle></CardHeader>
          <CardContent>
            <Badge className={modeTone}>
              {modeLabel}
            </Badge>
            <div className="mt-2 text-xs text-zinc-400">generated {report.generated_at}</div>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Base URL</CardTitle></CardHeader>
          <CardContent>
            <div className="break-all text-sm text-zinc-100">{report.runtime.backendBaseUrl || '(not set)'}</div>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Timeout / force mocks</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-sm text-zinc-100">
            <div>{report.runtime.backendTimeoutMs} ms</div>
            <div className="text-xs text-zinc-400">force mocks: {report.runtime.forceMocks ? 'enabled' : 'disabled'}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        {report.checks.map((check) => (
          <Card key={check.id} className="border-zinc-800 bg-zinc-900">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between gap-3">
                <CardTitle className="text-sm text-zinc-300">{check.label}</CardTitle>
                <Badge className={check.ok ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' : 'border-amber-500/30 bg-amber-500/10 text-amber-300'}>
                  {check.ok ? 'ok' : 'attention'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              <div className="text-sm text-zinc-100">{check.detail}</div>
              <div className="text-xs text-zinc-400">duration: {check.duration_ms} ms</div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader><CardTitle className="text-base">Bring-up guidance</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          {report.guidance.length ? (
            report.guidance.map((line) => <p key={line}>• {line}</p>)
          ) : (
            <p>• Preflight did not surface any immediate configuration hints.</p>
          )}
          <p>• Recommended next step: run <code className="rounded bg-zinc-950 px-1 py-0.5">npm run check</code> and then <code className="rounded bg-zinc-950 px-1 py-0.5">npm run build</code> locally.</p>
        </CardContent>
      </Card>
    </div>
  );
}
