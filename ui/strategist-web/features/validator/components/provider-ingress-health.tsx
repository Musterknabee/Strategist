"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { UiBurnInDashboard } from "@/lib/contracts/ui";

export function ProviderIngressHealth({ data }: { data: UiBurnInDashboard }) {
  const enabled = data.metrics.providerPaths.filter((p) => p.status === "ENABLED").length;

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-4">
        <SummaryCard title="Providers" value={String(data.metrics.providerPaths.length)} description="Configured ingress/provider rows in projection payload." />
        <SummaryCard title="Enabled" value={String(enabled)} description="Providers currently enabled in this environment." />
        <SummaryCard title="Artifacts" value={String(data.artifact_summary.artifact_count)} description="Burn-in artifacts represented in the dashboard snapshot." />
        <SummaryCard title="Fallback rounds" value={String(data.artifact_summary.total_fallback_count)} description="Fallback activity captured in current artifact set." />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Provider ingress health</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.metrics.providerPaths.map((provider) => {
            const enabledProvider = provider.status === "ENABLED";
            return (
              <div key={`${provider.provider}-${provider.path}`} className="rounded-[1.1rem] border border-zinc-800 bg-zinc-950/70 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm font-medium text-zinc-100">{provider.provider}</div>
                    <div className="mt-1 text-xs text-zinc-500">{provider.path}</div>
                  </div>
                  <Badge className={enabledProvider ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-200" : undefined}>{provider.status}</Badge>
                </div>
                <div className="mt-3 grid gap-3 md:grid-cols-3">
                  <InfoCell label="Ingress posture" value={enabledProvider ? "cross-check eligible" : "inactive"} />
                  <InfoCell label="Promotion use" value={enabledProvider ? "forensic provenance" : "not admissible"} />
                  <InfoCell label="Operator note" value={enabledProvider ? "verify alongside realism and CPCV" : "do not assume availability"} />
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}

function SummaryCard({ title, value, description }: { title: string; value: string; description: string }) {
  return (
    <Card>
      <CardHeader className="pb-2"><CardTitle className="text-sm text-zinc-300">{title}</CardTitle></CardHeader>
      <CardContent>
        <div className="text-2xl font-semibold text-zinc-50">{value}</div>
        <div className="mt-1 text-sm text-zinc-400">{description}</div>
      </CardContent>
    </Card>
  );
}

function InfoCell({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-zinc-800 p-3">
      <div className="text-xs uppercase tracking-wide text-zinc-500">{label}</div>
      <div className="mt-1 text-sm text-zinc-100">{value}</div>
    </div>
  );
}
