import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getBackendRuntimeConfig } from "@/lib/server/backend";

export default function RuntimeDiagnosticsPage() {
  const runtime = getBackendRuntimeConfig();
  const modeLabel = runtime.forceMocks ? "Mock-backed" : runtime.backendBaseUrl ? "Backend-connected" : "Backend required";
  const modeTone = runtime.forceMocks
    ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
    : runtime.backendBaseUrl
      ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
      : "border-rose-500/30 bg-rose-500/10 text-rose-300";

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-zinc-100">Runtime diagnostics</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Local bring-up view for backend reachability, explicit mock-mode posture, and server-side fetch configuration.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Mode</CardTitle></CardHeader>
          <CardContent>
            <Badge className={modeTone}>
              {modeLabel}
            </Badge>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Backend base URL</CardTitle></CardHeader>
          <CardContent>
            <div className="text-sm text-zinc-100 break-all">{runtime.backendBaseUrl || "(not set)"}</div>
          </CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">Timeout</CardTitle></CardHeader>
          <CardContent>
            <div className="text-sm text-zinc-100">{runtime.backendTimeoutMs} ms</div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader><CardTitle className="text-base">Local execution checklist</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm text-zinc-300">
          <p>1. Copy <code className="rounded bg-zinc-950 px-1 py-0.5">.env.example</code> to <code className="rounded bg-zinc-950 px-1 py-0.5">.env.local</code>.</p>
          <p>2. Set <code className="rounded bg-zinc-950 px-1 py-0.5">STRATEGIST_BACKEND_BASE_URL</code> if you want real backend reads.</p>
          <p>3. Run <code className="rounded bg-zinc-950 px-1 py-0.5">npm install</code>, then <code className="rounded bg-zinc-950 px-1 py-0.5">npm run check</code>.</p>
          <p>4. Run <code className="rounded bg-zinc-950 px-1 py-0.5">npm run build</code> before shipping any UI slice.</p>
          <p>5. Open <Link href="/settings/preflight" className="text-emerald-300 underline underline-offset-4">frontend preflight</Link> to confirm representative payloads before a full validation pass.</p>
        </CardContent>
      </Card>
    </div>
  );
}
