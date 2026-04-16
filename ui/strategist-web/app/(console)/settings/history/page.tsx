import Link from "next/link";
import type { Route } from "next";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { readFrontendDiagnosticsHistory, readLatestFrontendDiagnosticsHistoryEntry } from "@/lib/server/diagnostics-history";

type SearchParams = Record<string, string | string[] | undefined>;

function firstValue(value: string | string[] | undefined, fallback = ""): string {
  return Array.isArray(value) ? value[0] ?? fallback : value ?? fallback;
}

function historyHref(filters: { mode?: string; posture?: string; search?: string; limit?: string }) {
  const params = new URLSearchParams();
  if (filters.mode && filters.mode !== "all") params.set("mode", filters.mode);
  if (filters.posture && filters.posture !== "all") params.set("posture", filters.posture);
  if (filters.search) params.set("search", filters.search);
  if (filters.limit && filters.limit !== "24") params.set("limit", filters.limit);
  const query = params.toString();
  return query ? `/settings/history?${query}` : "/settings/history";
}

export default async function DiagnosticsHistoryPage({
  searchParams,
}: {
  searchParams?: Promise<SearchParams>;
}) {
  const resolved = (await searchParams) ?? {};
  const mode = firstValue(resolved.mode, "all");
  const posture = firstValue(resolved.posture, "all");
  const search = firstValue(resolved.search, "").trim();
  const limit = firstValue(resolved.limit, "24");

  const history = await readFrontendDiagnosticsHistory({
    limit: Number.parseInt(limit, 10),
    mode: mode as any,
    posture,
    search,
  });
  const latest = await readLatestFrontendDiagnosticsHistoryEntry();

  const backendConnectedCount = history.filter((entry) => entry.mode === "backend-connected").length;
  const warningCount = history.filter((entry) => entry.posture !== "ok").length;

  const currentApiHref = `/api/ui/diagnostics/history?${new URLSearchParams({
    limit,
    ...(mode !== "all" ? { mode } : {}),
    ...(posture !== "all" ? { posture } : {}),
    ...(search ? { search } : {}),
  }).toString()}`;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-xs uppercase tracking-[0.18em] text-zinc-500">settings / history</div>
          <h2 className="mt-2 text-2xl font-semibold text-zinc-100">Diagnostics history</h2>
          <p className="mt-1 text-sm text-zinc-400">
            Recent local frontend diagnostics exports, useful for comparing bring-up posture across repeated runs.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Link
            href={currentApiHref as Route}
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Open filtered JSON
          </Link>
          <Link
            href="/api/ui/diagnostics/latest"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Open latest JSON
          </Link>
          <Link
            href="/settings/summary"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Open summary
          </Link>
          <Link
            href="/settings/trends"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Open trends
          </Link>
          <Link
            href="/settings/export"
            className="rounded-full border border-zinc-700 bg-zinc-900 px-4 py-2 text-sm text-zinc-300 transition hover:border-zinc-600 hover:text-white"
          >
            Back to export
          </Link>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-5">
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Entries</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{history.length}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Backend-connected</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{backendConnectedCount}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Warnings</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{warningCount}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Latest posture</CardTitle></CardHeader>
          <CardContent className="text-sm text-zinc-300">{latest?.posture ?? "no-history"}</CardContent>
        </Card>
        <Card className="border-zinc-800 bg-zinc-900">
          <CardHeader><CardTitle className="text-base text-zinc-100">Filters</CardTitle></CardHeader>
          <CardContent className="space-y-1 text-xs text-zinc-300">
            <div>Mode: {mode}</div>
            <div>Posture: {posture}</div>
            <div>Search: {search || "none"}</div>
            <div>Filtered warning count: {warningCount}</div>
          </CardContent>
        </Card>
      </div>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Quick filters</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-2 text-sm">
          {[
            { label: "All", href: historyHref({ limit }) },
            { label: "Backend-connected", href: historyHref({ mode: "backend-connected", posture, search, limit }) },
            { label: "Mock-backed", href: historyHref({ mode: "mock-backed", posture, search, limit }) },
            { label: "Warnings only", href: historyHref({ mode, posture: "warning", search, limit }) },
            { label: "Attention only", href: historyHref({ mode, posture: "attention", search, limit }) },
            { label: "Latest 8", href: historyHref({ mode, posture, search, limit: "8" }) },
            { label: "Latest 50", href: historyHref({ mode, posture, search, limit: "50" }) },
          ].map((item) => (
            <Link
              key={item.label}
              href={item.href as Route}
              className="rounded-full border border-zinc-700 bg-zinc-950 px-3 py-1.5 text-zinc-300 transition hover:border-zinc-600 hover:text-white"
            >
              {item.label}
            </Link>
          ))}
        </CardContent>
      </Card>

      <Card className="border-zinc-800 bg-zinc-900">
        <CardHeader>
          <CardTitle className="text-base text-zinc-100">Recent export runs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {history.length ? (
            history.map((entry, index) => (
              <div key={`${entry.exportId}-${entry.generatedAt}-${index}`} className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-300">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="font-medium text-zinc-100">{entry.exportId}</div>
                  <div className="text-xs text-zinc-400">{entry.generatedAt}</div>
                </div>
                <div className="mt-3 grid gap-2 md:grid-cols-4">
                  <div>Mode: {entry.mode}</div>
                  <div>Posture: {entry.posture}</div>
                  <div>Probes: {entry.probeCount}</div>
                  <div>Notes: {entry.notesCount}</div>
                </div>
                <div className="mt-2 grid gap-2 md:grid-cols-3 text-xs text-zinc-400">
                  <div>Runtime: {entry.runtimeEnvironment ?? "unknown"}</div>
                  <div>Status: {entry.status ?? "n/a"}</div>
                  <div className="truncate">URL: {entry.url ?? "n/a"}</div>
                </div>
              </div>
            ))
          ) : (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-950/60 p-4 text-sm text-zinc-400">
              No diagnostics history for the current filters. Run <code className="rounded bg-zinc-950 px-1 py-0.5 text-zinc-200">npm run export:diagnostics</code> or clear the filters above.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
